from __future__ import annotations

import argparse
import re
from pathlib import Path

from pubskill_common import read_text_input, stable_id, write_json


DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I)
PMCID_RE = re.compile(r"\bPMC\d+\b", re.I)
PMID_RE = re.compile(r"^(?:PMID[:\s]*)?(\d{5,10})$", re.I)


def classify(raw_value: str) -> dict[str, str]:
    value = raw_value.strip()
    local_path = Path(value).expanduser()
    if local_path.exists() and local_path.suffix.lower() == ".pdf":
        return {"type": "pdf_path", "value": str(local_path.resolve())}

    if value.lower().endswith(".pdf") and re.match(r"https?://", value, re.I):
        return {"type": "pdf_url", "value": value}

    if re.match(r"https?://", value, re.I):
        doi_match = DOI_RE.search(value)
        pmcid_match = PMCID_RE.search(value)
        if doi_match:
            return {"type": "doi", "value": doi_match.group(1)}
        if pmcid_match:
            return {"type": "pmcid", "value": pmcid_match.group(0).upper()}
        return {"type": "url", "value": value}

    pmcid_match = PMCID_RE.search(value)
    if pmcid_match:
        return {"type": "pmcid", "value": pmcid_match.group(0).upper()}

    doi_match = DOI_RE.search(value)
    if doi_match:
        return {"type": "doi", "value": doi_match.group(1)}

    pmid_match = PMID_RE.match(value)
    if pmid_match:
        return {"type": "pmid", "value": pmid_match.group(1)}

    raise ValueError(f"Unsupported publication input: {raw_value}")


def normalize(inputs: list[str]) -> dict:
    expanded: list[str] = []
    for item in inputs:
        expanded.extend(read_text_input(item))

    records = []
    seen = set()
    for raw in expanded:
        classified = classify(raw)
        key = (classified["type"], classified["value"].lower())
        if key in seen:
            continue
        seen.add(key)
        records.append(
            {
                "id": stable_id(f"{classified['type']}:{classified['value']}"),
                "source_type": classified["type"],
                "source_value": classified["value"],
                "raw_input": raw,
            }
        )

    return {"count": len(records), "publications": records}


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize publication inputs.")
    parser.add_argument("--input", action="append", required=True, help="Publication input or file path.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()
    write_json(args.out, normalize(args.input))


if __name__ == "__main__":
    main()
