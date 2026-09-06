from __future__ import annotations

import argparse
from pathlib import Path

from pubskill_common import load_json, slugify, write_json


def markdown_list(values: list[str]) -> str:
    return "\n".join(f"- {item}" for item in values) or "- Not specified."


def helper_script_section(proposal: dict) -> str:
    helper_scripts = proposal.get("helper_scripts") or []
    if not helper_scripts:
        return """## Helper Scripts

No helper scripts were specified for this approved proposal. When using this skill, create task-specific scripts under `scripts/` if the user's data source requires repeatable parsing, fetching, computation, validation, or report generation.
"""

    sections = ["## Helper Scripts", "", "This skill includes planned helper scripts. Inspect or implement them before running the workflow on user data."]
    for script in helper_scripts:
        sections.extend(
            [
                "",
                f"### `{script.get('path', 'scripts/helper.py')}`",
                "",
                script.get("purpose", "No purpose recorded."),
                "",
                "Expected inputs:",
                markdown_list(script.get("expected_inputs", [])),
                "",
                "Expected outputs:",
                markdown_list(script.get("expected_outputs", [])),
                "",
                "Implementation notes:",
                script.get("implementation_notes", "No implementation notes recorded."),
            ]
        )
        source_references = script.get("source_references", [])
        if source_references:
            sections.extend(["", "Source references:", markdown_list(source_references)])
    return "\n".join(sections) + "\n"


def repository_section(decision_doc: dict) -> str:
    proposal = decision_doc["proposal"]
    repository_reference = proposal.get("repository_reference") or {}
    repository_review = decision_doc.get("repository_review") or {}
    if not repository_reference and not repository_review:
        return ""
    lines = ["## Repository Reference", ""]
    status = repository_review.get("status") or repository_reference.get("status")
    if status:
        lines.append(f"Repository review status: {status}")
        lines.append("")
    findings = repository_review.get("implementation_findings") or repository_reference.get("implementation_findings") or []
    if findings:
        lines.append("Implementation findings:")
        lines.append(markdown_list(findings))
        lines.append("")
    inspected = repository_review.get("inspected_files") or repository_reference.get("inspected_files") or []
    if inspected:
        lines.append("Inspected files:")
        lines.append(markdown_list(inspected))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n\n"


def skill_markdown(decision_doc: dict) -> str:
    proposal = decision_doc["proposal"]
    paper = decision_doc["paper"]
    availability = decision_doc["availability"]
    paper_type = decision_doc.get("paper_type", "unknown")
    analysis_basis = decision_doc.get("analysis_basis", "unknown")
    title = paper.get("title", "source publication")
    doi = paper.get("doi", "")
    links = "\n".join(f"- {url}" for url in paper.get("urls", [])) or "- No source URL recorded."
    repo_links = "\n".join(f"- {url}" for url in availability.get("repository_links", [])) or "- No code repository link recorded."
    return f"""---
name: {proposal["skill_name"]}
description: {proposal["description"]}
metadata:
  source: publication-to-skill-builder
---

# {proposal["skill_name"]}

Use this skill when the user wants to apply the reusable computational method derived from:

{title}

DOI: {doi or "not recorded"}

Paper type: {paper_type}

Analysis basis: {analysis_basis}

## Method Basis

{proposal.get("evidence") or "No method evidence was recorded."}

## Expected Inputs

{chr(10).join(f"- {item}" for item in proposal.get("expected_inputs", []))}

## Expected Outputs

{chr(10).join(f"- {item}" for item in proposal.get("expected_outputs", []))}

{repository_section(decision_doc)}{helper_script_section(proposal)}

## Source Links

{links}

## Code Availability

{repo_links}

## Limitations

{chr(10).join(f"- {item}" for item in proposal.get("limitations", [])) or "- Review the provenance file before use."}
"""


def scaffold(decision_doc: dict, out_dir: Path) -> Path:
    if decision_doc.get("decision", {}).get("status") != "approved":
        raise ValueError("Refusing to scaffold: decision.status is not approved.")
    proposal = decision_doc["proposal"]
    skill_name = slugify(proposal["skill_name"])
    skill_dir = out_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_markdown(decision_doc), encoding="utf-8")
    for script in proposal.get("helper_scripts") or []:
        relative_path = script.get("path", "")
        if not relative_path:
            continue
        script_path = skill_dir / relative_path
        if not script_path.resolve().is_relative_to(skill_dir.resolve()):
            raise ValueError(f"Refusing to write helper script outside skill directory: {script_path}")
        script_path.parent.mkdir(parents=True, exist_ok=True)
        content = script.get("content") or (
            '"""Helper script scaffold generated from publication provenance.\n\n'
            f"Purpose: {script.get('purpose', 'not recorded')}\n"
            'Review SKILL.md and provenance.json before completing implementation.\n'
            '"""\n\n'
            "from __future__ import annotations\n\n\n"
            "def main() -> None:\n"
            "    raise NotImplementedError('Implement this helper from the paper and repository provenance.')\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        script_path.write_text(content, encoding="utf-8")
    write_json(skill_dir / "provenance.json", decision_doc)
    return skill_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold an approved generated skill.")
    parser.add_argument("--approved-decision", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    path = scaffold(load_json(args.approved_decision), Path(args.out))
    print(path)


if __name__ == "__main__":
    main()
