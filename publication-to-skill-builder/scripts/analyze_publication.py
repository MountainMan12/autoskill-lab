from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from pubskill_common import load_json, remove_references_section, slugify, utc_now, write_json


ARTICLE_TYPE_SIGNALS = {
    "review": ["review", "systematic review", "meta-analysis", "perspective", "overview"],
    "benchmark": ["benchmark", "comparison", "evaluation", "assessment"],
    "workflow": ["workflow", "pipeline", "protocol", "tutorial"],
    "software/resource": ["software", "database", "resource", "tool", "package", "web server"],
    "original research": ["results", "materials and methods", "methods"],
}


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def first_sentences(text: str, count: int = 5) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", compact_whitespace(text))
    return " ".join(sentences[:count]).strip()


def representative_excerpts(text: str, excerpt_count: int = 3, max_chars: int = 700) -> list[str]:
    cleaned = compact_whitespace(text)
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    anchors = [0]
    if excerpt_count >= 2:
        anchors.append(max(0, (len(cleaned) - max_chars) // 2))
    if excerpt_count >= 3:
        anchors.append(max(0, len(cleaned) - max_chars))

    excerpts = []
    for start in anchors[:excerpt_count]:
        excerpt = cleaned[start : start + max_chars].strip()
        if start > 0:
            first_space = excerpt.find(" ")
            if first_space != -1:
                excerpt = excerpt[first_space + 1 :].strip()
        if start + max_chars < len(cleaned):
            last_space = excerpt.rfind(" ")
            if last_space != -1:
                excerpt = excerpt[:last_space].strip()
        if excerpt and excerpt not in excerpts:
            excerpts.append(excerpt)
    return excerpts


def find_links(text: str) -> list[str]:
    return sorted(set(link.rstrip(".,;:") for link in re.findall(r"https?://[^\s),;\]]+", text or "")))


def heading_like(line: str) -> str | None:
    cleaned = line.strip().rstrip(":")
    if not cleaned or len(cleaned) > 100:
        return None
    if re.match(r"^(\d+(\.\d+)*[\.\)]?\s+)?[A-Z][A-Za-z0-9 /,&()_-]{2,}$", cleaned):
        words = cleaned.split()
        if len(words) <= 12:
            return cleaned
    return None


def detect_sections(full_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "front_matter"
    sections[current] = []
    for line in (full_text or "").splitlines():
        heading = heading_like(line)
        if heading:
            current = slugify(heading, "section")
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip()
    }


def detect_headings(full_text: str) -> list[str]:
    headings = []
    for line in (full_text or "").splitlines():
        heading = heading_like(line)
        if heading and heading not in headings:
            headings.append(heading)
    return headings


def infer_paper_type(paper: dict[str, Any], content: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(paper.get("title", "")),
            str(content.get("abstract", "")),
            " ".join(content.get("detected_headings", [])),
        ]
    ).lower()
    for paper_type, signals in ARTICLE_TYPE_SIGNALS.items():
        if any(signal in text for signal in signals):
            return paper_type
    return "unknown"


def analysis_basis(publication: dict[str, Any]) -> str:
    content = publication.get("content", {})
    availability = publication.get("availability", {})
    paper = publication.get("paper", {})
    if content.get("full_text") and paper.get("source_type") == "pdf_path":
        return "user PDF"
    if content.get("full_text") and availability.get("pdf_path"):
        return "PDF text"
    if content.get("full_text"):
        return "full text"
    if content.get("abstract"):
        return "abstract only"
    return "metadata only"


def evidence_excerpt(content: dict[str, Any]) -> str:
    full_text = content.get("full_text", "")
    abstract = content.get("abstract", "")
    source = "\n\n".join(part for part in [abstract, full_text] if part)
    excerpts = representative_excerpts(source, excerpt_count=3, max_chars=500)
    return "\n\n".join(excerpts)


def build_ai_prompt_bundle(publication: dict[str, Any], paper_type: str, basis: str) -> dict[str, Any]:
    paper = publication.get("paper", {})
    content = publication.get("content", {})
    availability = publication.get("availability", {})
    full_text = content.get("full_text", "")
    sections = content.get("sections", {})
    section_summaries = {
        name: first_sentences(text, 4)
        for name, text in sections.items()
        if text.strip()
    }
    return {
        "system_instruction": (
            "Identify reusable Codex skill opportunities from the complete publication. "
            "Do not rely on fixed keyword lists. Consider original research articles, reviews, "
            "benchmarks, tutorials, workflows, databases, resources, and software papers. "
            "Ground every candidate in evidence from the publication and mark uncertainty clearly."
        ),
        "user_task": (
            "Return ranked candidate_skills and select one proposal for user approval. "
            "Each candidate must include skill_name, purpose, evidence, reusable_value, "
            "expected_inputs, expected_outputs, implementation_complexity, and limitations."
        ),
        "paper": paper,
        "paper_type": paper_type,
        "analysis_basis": basis,
        "abstract": content.get("abstract", ""),
        "section_summaries": section_summaries,
        "availability": availability,
        "full_text_for_ai_review": full_text,
    }


def analyze(publication: dict[str, Any]) -> dict[str, Any]:
    paper = publication.get("paper", {})
    content = publication.setdefault("content", {})
    availability = publication.setdefault("availability", {})
    full_text, references_removed = remove_references_section(content.get("full_text", ""))
    content["full_text"] = full_text
    if references_removed:
        content["excluded_sections"] = sorted(set(content.get("excluded_sections", []) + ["references"]))
    combined_text = "\n".join([content.get("abstract", ""), full_text])

    content["sections"] = content.get("sections") or detect_sections(full_text)
    content["detected_headings"] = content.get("detected_headings") or detect_headings(full_text)
    content["methods_text"] = content.get("sections", {}).get("methods") or content.get("sections", {}).get("materials-and-methods", "")
    content["methods_summary"] = first_sentences(content.get("methods_text", ""), 5)

    repository_links = [
        link
        for link in find_links(combined_text)
        if any(host in link.lower() for host in ["github.com", "gitlab", "bitbucket", "zenodo.org"])
    ]
    availability["repository_links"] = sorted(set(availability.get("repository_links", []) + repository_links))

    basis = analysis_basis(publication)
    paper_type = infer_paper_type(paper, content)
    limitations = content.setdefault("limitations", [])
    if basis in {"abstract only", "metadata only"}:
        limitations.append("Full-paper text was unavailable; AI analysis must be treated as partial.")
    if not full_text and not content.get("abstract"):
        limitations.append("No abstract or full text was available for AI analysis.")

    proposal_slug = slugify(f"ai-selected-skill-from-{paper.get('title') or publication.get('id', 'publication')}")
    analysis = {
        "id": publication["id"],
        "paper": paper,
        "content": content,
        "availability": availability,
        "paper_type": paper_type,
        "analysis_basis": basis,
        "candidate_skills": [],
        "proposal": {
            "skill_name": proposal_slug,
            "description": "Pending AI selection from the full-paper analysis bundle.",
            "usefulness": "Requires Codex AI review of the prepared full-paper evidence bundle.",
            "evidence": evidence_excerpt(content),
            "expected_inputs": [],
            "expected_outputs": [],
            "limitations": limitations,
            "status": "requires_ai_candidate_selection",
        },
        "analysis_notes": {
            "created_at": utc_now(),
            "ai_required": True,
            "instructions": (
                "Codex must read ai_prompt_bundle, generate ranked candidate_skills, select proposal, "
                "then ask the user for approval before scaffolding."
            ),
        },
        "ai_prompt_bundle": build_ai_prompt_bundle(publication, paper_type, basis),
    }
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare full-paper analysis bundle for AI skill proposal generation.")
    parser.add_argument("--publication", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(args.out, analyze(load_json(args.publication)))


if __name__ == "__main__":
    main()
