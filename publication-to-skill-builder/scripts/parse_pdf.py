from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

from pubskill_common import is_reference_heading, load_json, remove_references_section, write_json


def heading_like(line: str) -> str | None:
    cleaned = line.strip().rstrip(":")
    if not cleaned or len(cleaned) > 100:
        return None
    if re.match(r"^(\d+(\.\d+)*[\.\)]?\s+)?[A-Z][A-Za-z0-9 /,&()_-]{2,}$", cleaned):
        if len(cleaned.split()) <= 12:
            return cleaned
    return None


def detect_headings(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        heading = heading_like(line)
        if heading and heading not in headings:
            headings.append(heading)
    return headings


def detect_sections(text: str) -> dict[str, str]:
    from pubskill_common import slugify

    sections: dict[str, list[str]] = {"front_matter": []}
    current = "front_matter"
    for line in text.splitlines():
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


def find_links(text: str) -> list[str]:
    return sorted(set(link.rstrip(".,;:") for link in re.findall(r"https?://[^\s),;\]]+", text)))


def find_captions(text: str) -> list[str]:
    captions = []
    for line in text.splitlines():
        if re.match(r"^\s*(Figure|Fig\.|Table)\s+\d+", line, re.I):
            captions.append(line.strip())
    return captions


def read_pdf(path: Path) -> dict:
    try:
        import pymupdf
    except ImportError as exc:
        try:
            import fitz as pymupdf
        except ImportError:
            raise SystemExit("PyMuPDF is required. Install with: pip install pymupdf") from exc
    with pymupdf.open(path) as doc:
        raw_pages = [
            {"page": index + 1, "text": page.get_text("text")}
            for index, page in enumerate(doc)
        ]

    pages = []
    references_removed = False
    in_references = False
    for page in raw_pages:
        kept_lines = []
        for line in page["text"].splitlines():
            if is_reference_heading(line):
                in_references = True
                references_removed = True
                break
            if not in_references:
                kept_lines.append(line)
        if not in_references or kept_lines:
            pages.append({"page": page["page"], "text": "\n".join(kept_lines).strip()})

    full_text = "\n".join(page["text"] for page in pages if page["text"])
    full_text, text_level_references_removed = remove_references_section(full_text)
    references_removed = references_removed or text_level_references_removed
    return {
        "full_text": full_text,
        "pages": pages,
        "detected_headings": detect_headings(full_text),
        "sections": detect_sections(full_text),
        "captions": find_captions(full_text),
        "links": find_links(full_text),
        "excluded_sections": ["references"] if references_removed else [],
    }


def download_pdf(url: str, out_dir: Path, publication_id: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{publication_id}.pdf"
    request = urllib.request.Request(url, headers={"User-Agent": "publication-to-skill-builder/0.1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        path.write_bytes(response.read())
    return path


def parse_publication(publication: dict, pdf_cache: Path) -> dict:
    availability = publication.setdefault("availability", {})
    content = publication.setdefault("content", {})
    pdf_path = availability.get("pdf_path")
    if not pdf_path and availability.get("pdf_url"):
        pdf_path = str(download_pdf(availability["pdf_url"], pdf_cache, publication["id"]))
        availability["pdf_path"] = pdf_path

    if not pdf_path:
        content.setdefault("limitations", []).append("No PDF path or URL was available for parsing.")
        return publication

    parsed = read_pdf(Path(pdf_path))
    content["full_text"] = parsed["full_text"]
    content["pages"] = parsed["pages"]
    content["detected_headings"] = parsed["detected_headings"]
    content["sections"] = parsed["sections"]
    content["captions"] = parsed["captions"]
    content["excluded_sections"] = sorted(set(content.get("excluded_sections", []) + parsed["excluded_sections"]))
    content["parser"] = "PyMuPDF"
    content["extraction_status"] = "full_text_extracted" if parsed["full_text"].strip() else "empty_pdf_text"
    availability["repository_links"] = sorted(
        set(
            availability.get("repository_links", [])
            + [
                link
                for link in parsed["links"]
                if any(host in link.lower() for host in ["github.com", "gitlab", "bitbucket", "zenodo.org"])
            ]
        )
    )
    return publication


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse PDF text into a publication JSON file.")
    parser.add_argument("--publication", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--pdf-cache", default="runs/pdf-cache")
    args = parser.parse_args()
    publication = load_json(args.publication)
    parsed = parse_publication(publication, Path(args.pdf_cache))
    write_json(args.out, parsed)


if __name__ == "__main__":
    main()
