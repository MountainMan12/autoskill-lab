from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REFERENCE_HEADINGS = {
    "references",
    "bibliography",
    "literature cited",
    "works cited",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def slugify(value: str, fallback: str = "publication-skill") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:72].strip("-") or fallback


def stable_id(value: str, prefix: str = "pub") -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def read_text_input(path_or_value: str) -> list[str]:
    path = Path(path_or_value).expanduser()
    if path.exists() and path.is_file() and path.suffix.lower() != ".pdf":
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    return [path_or_value.strip()]


def is_reference_heading(line: str) -> bool:
    cleaned = re.sub(r"^\s*\d+(\.\d+)*[\.\)]?\s*", "", line.strip().lower())
    cleaned = cleaned.rstrip(":")
    return cleaned in REFERENCE_HEADINGS


def remove_references_section(text: str) -> tuple[str, bool]:
    kept = []
    removed = False
    for line in (text or "").splitlines():
        if is_reference_heading(line):
            removed = True
            break
        kept.append(line)
    return "\n".join(kept).strip(), removed
