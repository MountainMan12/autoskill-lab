from __future__ import annotations

import argparse
from pathlib import Path

from pubskill_common import load_json, slugify, write_json


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
