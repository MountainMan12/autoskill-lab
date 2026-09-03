from __future__ import annotations

import argparse
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from pubskill_common import load_json, stable_id, utc_now, write_json


EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CROSSREF = "https://api.crossref.org/works"


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "publication-to-skill-builder/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return dict(__import__("json").loads(response.read().decode("utf-8")))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "publication-to-skill-builder/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def europe_pmc_query(record: dict[str, str]) -> dict[str, Any] | None:
    source_type = record["source_type"]
    value = record["source_value"]
    if source_type == "pmid":
        query = f"EXT_ID:{value} AND SRC:MED"
    elif source_type == "pmcid":
        query = f"PMCID:{value}"
    elif source_type == "doi":
        query = f'DOI:"{value}"'
    else:
        return None
    url = f"{EUROPE_PMC}?{urllib.parse.urlencode({'query': query, 'format': 'json', 'pageSize': 1})}"
    data = fetch_json(url)
    results = data.get("resultList", {}).get("result", [])
    return results[0] if results else None


def crossref_query(doi: str) -> dict[str, Any] | None:
    url = f"{CROSSREF}/{urllib.parse.quote(doi, safe='')}"
    data = fetch_json(url)
    return data.get("message")


def extract_pdf_url_from_full_text_xml(pmcid: str | None) -> str | None:
    if not pmcid:
        return None
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    try:
        xml_text = fetch_text(url)
    except Exception:
        return None
    match = re.search(r'href="([^"]+\.pdf[^"]*)"', xml_text, re.I)
    if match:
        return urllib.parse.urljoin("https://europepmc.org/", match.group(1))
    return None


def publication_from_record(record: dict[str, str]) -> dict[str, Any]:
    paper = {
        "title": "",
        "authors": [],
        "journal": "",
        "publication_date": "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "urls": [],
        "source_type": record["source_type"],
        "source_value": record["source_value"],
    }
    content = {
        "abstract": "",
        "methods_text": "",
        "methods_summary": "",
        "extraction_status": "metadata_only",
        "parser": "fetch_publication.py",
        "limitations": [],
    }
    availability = {
        "full_text_available": False,
        "pdf_available": False,
        "pdf_path": "",
        "pdf_url": "",
        "data_availability": "",
        "code_availability": "",
        "repository_links": [],
    }

    if record["source_type"] == "pdf_path":
        path = Path(record["source_value"])
        paper["title"] = path.stem
        availability["pdf_available"] = True
        availability["pdf_path"] = str(path)
        content["extraction_status"] = "pdf_available"
    elif record["source_type"] == "pdf_url":
        paper["urls"].append(record["source_value"])
        availability["pdf_available"] = True
        availability["pdf_url"] = record["source_value"]
    elif record["source_type"] == "url":
        paper["urls"].append(record["source_value"])
        content["limitations"].append("Generic URL metadata extraction is limited in v1.")
    else:
        try:
            epmc = europe_pmc_query(record)
        except Exception as exc:
            epmc = None
            content["limitations"].append(f"Europe PMC lookup failed: {exc}")
        if epmc:
            paper.update(
                {
                    "title": epmc.get("title", ""),
                    "authors": [name.strip() for name in epmc.get("authorString", "").split(",") if name.strip()],
                    "journal": epmc.get("journalTitle", ""),
                    "publication_date": epmc.get("firstPublicationDate", "") or epmc.get("pubYear", ""),
                    "doi": epmc.get("doi", ""),
                    "pmid": epmc.get("pmid", ""),
                    "pmcid": epmc.get("pmcid", ""),
                }
            )
            content["abstract"] = epmc.get("abstractText", "") or ""
            content["extraction_status"] = "abstract_available" if content["abstract"] else "metadata_only"
            if epmc.get("fullTextUrlList"):
                availability["full_text_available"] = True
            pdf_url = extract_pdf_url_from_full_text_xml(paper["pmcid"]) if paper["pmcid"] else None
            if pdf_url:
                availability["pdf_available"] = True
                availability["pdf_url"] = pdf_url
            if paper["doi"]:
                paper["urls"].append(f"https://doi.org/{paper['doi']}")
            if paper["pmid"]:
                paper["urls"].append(f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/")
            if paper["pmcid"]:
                paper["urls"].append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper['pmcid']}/")
        elif record["source_type"] == "doi":
            try:
                cr = crossref_query(record["source_value"])
            except Exception as exc:
                cr = None
                content["limitations"].append(f"Crossref lookup failed: {exc}")
            if cr:
                paper["title"] = " ".join(cr.get("title", [])[:1])
                paper["authors"] = [
                    " ".join(part for part in [a.get("given", ""), a.get("family", "")] if part)
                    for a in cr.get("author", [])
                ]
                paper["journal"] = " ".join(cr.get("container-title", [])[:1])
                paper["doi"] = cr.get("DOI", record["source_value"])
                paper["urls"].append(cr.get("URL", f"https://doi.org/{paper['doi']}"))

    if not paper["title"]:
        paper["title"] = record["source_value"]
    return {
        "id": record["id"],
        "retrieved_at": utc_now(),
        "paper": paper,
        "content": content,
        "availability": availability,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch publication metadata and availability.")
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = load_json(args.inputs)
    out_dir = Path(args.out)
    for record in data["publications"]:
        publication = publication_from_record(record)
        write_json(out_dir / f"{publication['id']}.json", publication)


if __name__ == "__main__":
    main()
