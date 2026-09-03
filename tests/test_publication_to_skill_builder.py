from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "publication-to-skill-builder" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


normalize_inputs = load_module("normalize_inputs")
parse_pdf = load_module("parse_pdf")
analyze_publication = load_module("analyze_publication")
check_existing_skills = load_module("check_existing_skills")
write_provenance = load_module("write_provenance")
scaffold_skill = load_module("scaffold_skill")
prepare_published_skills = load_module("prepare_published_skills")


class PublicationToSkillBuilderTests(unittest.TestCase):
    def test_analyzer_does_not_hardcode_biomedical_method_terms(self) -> None:
        analyzer_source = (SCRIPTS / "analyze_publication.py").read_text(encoding="utf-8")

        self.assertNotIn("differential expression", analyzer_source)
        self.assertNotIn("survival analysis", analyzer_source)
        self.assertNotIn("volcano plot", analyzer_source)
        self.assertNotIn("find_terms", analyzer_source)
        self.assertNotIn("preferred_sections", analyzer_source)

    def test_normalize_mixed_inputs_and_deduplicates(self) -> None:
        result = normalize_inputs.normalize(
            [
                "PMID:12345678",
                "PMC7654321",
                "https://doi.org/10.1038/s41586-020-2649-2",
                "10.1038/s41586-020-2649-2",
            ]
        )

        self.assertEqual(result["count"], 3)
        self.assertEqual([item["source_type"] for item in result["publications"]], ["pmid", "pmcid", "doi"])

    def test_normalize_rejects_more_than_ten(self) -> None:
        values = [f"PMID:{10000000 + index}" for index in range(11)]

        with self.assertRaisesRegex(ValueError, "maximum is 10"):
            normalize_inputs.normalize(values)

    def test_analyze_publication_uses_full_text_without_methods_heading(self) -> None:
        publication = {
            "id": "pub-test",
            "paper": {"title": "Review of clinical omics workflows", "urls": [], "doi": "10.1/test"},
            "content": {
                "abstract": "This review compares analysis workflows for clinical omics.",
                "full_text": (
                    "Introduction\nClinical omics studies often combine cohort curation, visualization, "
                    "and reproducibility checks. Practical workflow ideas are discussed throughout. "
                    "Resources are available at https://github.com/example/workflow.\nDiscussion\nDone."
                ),
                "limitations": [],
            },
            "availability": {"repository_links": []},
        }

        analysis = analyze_publication.analyze(publication)

        self.assertEqual(analysis["paper_type"], "review")
        self.assertEqual(analysis["analysis_basis"], "full text")
        self.assertEqual(analysis["candidate_skills"], [])
        self.assertEqual(analysis["proposal"]["status"], "requires_ai_candidate_selection")
        self.assertIn("full_text_for_ai_review", analysis["ai_prompt_bundle"])
        self.assertEqual(analysis["availability"]["repository_links"], ["https://github.com/example/workflow"])

    def test_parse_pdf_text_helpers_preserve_full_paper_structure(self) -> None:
        text = (
            "Title\n"
            "Introduction\n"
            "Background text.\n"
            "Workflow Concepts\n"
            "A reusable tool idea is described here.\n"
            "Figure 1 Overview of the analysis workflow.\n"
            "https://github.com/example/tool\n"
        )

        self.assertIn("Introduction", parse_pdf.detect_headings(text))
        self.assertIn("workflow-concepts", parse_pdf.detect_sections(text))
        self.assertEqual(parse_pdf.find_captions(text), ["Figure 1 Overview of the analysis workflow."])
        self.assertEqual(parse_pdf.find_links(text), ["https://github.com/example/tool"])

    def test_analyze_publication_excludes_references_from_ai_bundle(self) -> None:
        publication = {
            "id": "pub-references",
            "paper": {"title": "Workflow paper", "urls": [], "doi": ""},
            "content": {
                "abstract": "A workflow paper.",
                "full_text": (
                    "Introduction\nA reusable workflow is described in the paper body.\n"
                    "References\n"
                    "Smith J. https://github.com/reference-only/not-a-source-method\n"
                ),
                "limitations": [],
            },
            "availability": {"repository_links": []},
        }

        analysis = analyze_publication.analyze(publication)

        self.assertNotIn("Smith J", analysis["content"]["full_text"])
        self.assertNotIn("reference-only", analysis["ai_prompt_bundle"]["full_text_for_ai_review"])
        self.assertEqual(analysis["availability"]["repository_links"], [])
        self.assertEqual(analysis["content"]["excluded_sections"], ["references"])

    def test_analyze_publication_marks_abstract_only_as_partial_basis(self) -> None:
        publication = {
            "id": "pub-abstract",
            "paper": {"title": "A benchmark of tools", "urls": [], "doi": ""},
            "content": {"abstract": "This benchmark compares reusable computational tools.", "limitations": []},
            "availability": {"repository_links": []},
        }

        analysis = analyze_publication.analyze(publication)

        self.assertEqual(analysis["paper_type"], "benchmark")
        self.assertEqual(analysis["analysis_basis"], "abstract only")
        self.assertIn("partial", " ".join(analysis["proposal"]["limitations"]))

    def test_duplicate_check_recommends_reuse_for_close_match(self) -> None:
        proposal_doc = {"proposal": {"skill_name": "differential-expression-from-rna-cohort-comparison"}}
        result = check_existing_skills.check(
            proposal_doc,
            ["differential-expression-from-rna-cohort-comparison/SKILL.md"],
        )

        self.assertEqual(result["recommendation"], "reuse_existing")
        self.assertTrue(result["matches"])

    def test_write_provenance_records_declined_feedback(self) -> None:
        proposal = {
            "paper": {"title": "Paper"},
            "content": {},
            "availability": {},
            "paper_type": "review",
            "analysis_basis": "full text",
            "candidate_skills": [{"skill_name": "plot-review-workflow", "rank": 1}],
            "proposal": {"skill_name": "paper-skill"},
            "duplicate_check": {"status": "searched"},
        }

        decision = write_provenance.build_decision(proposal, "declined", "Prefer a plotting skill.")

        self.assertEqual(decision["decision"]["status"], "declined")
        self.assertEqual(decision["decision"]["user_feedback"], "Prefer a plotting skill.")
        self.assertTrue(decision["decision"]["decided_at"])
        self.assertEqual(decision["paper_type"], "review")
        self.assertEqual(decision["analysis_basis"], "full text")
        self.assertEqual(decision["candidate_skills"][0]["skill_name"], "plot-review-workflow")

    def test_scaffold_requires_approval(self) -> None:
        decision = {
            "paper": {"title": "Paper", "doi": "", "urls": []},
            "availability": {"repository_links": []},
            "proposal": {
                "skill_name": "paper-skill",
                "description": "A paper skill.",
                "expected_inputs": ["data"],
                "expected_outputs": ["plot"],
                "limitations": [],
            },
            "decision": {"status": "declined"},
        }

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not approved"):
                scaffold_skill.scaffold(decision, Path(tmp))

    def test_scaffold_writes_approved_skill(self) -> None:
        decision = {
            "paper": {"title": "Paper", "doi": "10.1/test", "urls": ["https://doi.org/10.1/test"]},
            "availability": {"repository_links": []},
            "proposal": {
                "skill_name": "paper-skill",
                "description": "A paper skill.",
                "evidence": "Methods evidence.",
                "expected_inputs": ["data"],
                "expected_outputs": ["plot"],
                "limitations": [],
            },
            "decision": {"status": "approved"},
        }

        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = scaffold_skill.scaffold(decision, Path(tmp))

            self.assertTrue((skill_dir / "SKILL.md").exists())
            self.assertTrue((skill_dir / "provenance.json").exists())

    def test_publish_prepare_script_does_not_switch_branches(self) -> None:
        source = (SCRIPTS / "prepare_published_skills.py").read_text(encoding="utf-8")

        self.assertNotIn("switch", source)
        self.assertNotIn("pub-skills", source)
        self.assertIn('"published-skills.md"', source)


if __name__ == "__main__":
    unittest.main()
