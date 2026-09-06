from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from pubskill_common import load_json, utc_now, write_json


GITHUB_RE = re.compile(r"https?://github\.com/([^/\s]+)/([^/\s)#?]+)", re.I)
TEXT_EXTENSIONS = (".md", ".txt", ".py", ".r", ".jl", ".ipynb", ".json", ".yaml", ".yml", ".toml")
IMPLEMENTATION_HINTS = (
    "readme",
    "notebook",
    "script",
    "src/",
    "scripts/",
    "workflow",
    "pipeline",
    "parse",
    "preprocess",
    "process",
    "analysis",
    "validate",
    "test",
    "schema",
)


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "publication-to-skill-builder/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return dict(json.loads(response.read().decode("utf-8")))


def github_repo_name(url: str) -> str | None:
    match = GITHUB_RE.search(url)
    if not match:
        return None
    owner, repo = match.groups()
    repo = repo.removesuffix(".git").rstrip("/")
    return f"{owner}/{repo}"


def fetch_tree(repo: str, ref: str) -> list[dict[str, Any]]:
    encoded_repo = urllib.parse.quote(repo, safe="/")
    url = f"https://api.github.com/repos/{encoded_repo}/git/trees/{urllib.parse.quote(ref)}?recursive=1"
    data = fetch_json(url)
    return [item for item in data.get("tree", []) if item.get("type") == "blob"]


def score_path(path: str) -> tuple[int, str]:
    lowered = path.lower()
    score = 0
    if lowered.endswith("readme.md"):
        score += 10
    if lowered.endswith(".ipynb"):
        score += 8
    if lowered.endswith((".py", ".r", ".jl")):
        score += 7
    if any(hint in lowered for hint in IMPLEMENTATION_HINTS):
        score += 5
    if lowered.endswith(TEXT_EXTENSIONS):
        score += 2
    return (-score, path)


def select_files(tree: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in tree
        if item.get("path", "").lower().endswith(TEXT_EXTENSIONS)
        and int(item.get("size") or 0) <= 1_000_000
    ]
    return sorted(candidates, key=lambda item: score_path(item["path"]))[:limit]


def inspect_github(url: str, ref: str, file_limit: int) -> dict[str, Any]:
    repo = github_repo_name(url)
    if not repo:
        return {"url": url, "status": "unsupported", "limitations": ["Only GitHub repository URLs are inspected by this script."]}
    try:
        tree = fetch_tree(repo, ref)
    except Exception as exc:
        return {"url": url, "repository": repo, "status": "failed", "limitations": [str(exc)]}

    inspected = select_files(tree, file_limit)
    findings = []
    paths = [item["path"] for item in inspected]
    if any(path.lower().endswith(".ipynb") for path in paths):
        findings.append("Repository contains notebooks that may document extraction or analysis workflows.")
    if any(path.lower().endswith((".py", ".r", ".jl")) for path in paths):
        findings.append("Repository contains executable source files suitable for script-boundary review.")
    if any("readme" in path.lower() for path in paths):
        findings.append("Repository README should be used to confirm dataset, code, and workflow claims.")
    return {
        "url": url,
        "repository": repo,
        "status": "inspected",
        "default_ref": ref,
        "inspected_files": paths,
        "implementation_findings": findings,
        "limitations": [],
    }


def inspect(publication_doc: dict[str, Any], ref: str, file_limit: int) -> dict[str, Any]:
    links = publication_doc.get("availability", {}).get("repository_links", [])
    repositories = [inspect_github(link, ref, file_limit) for link in links]
    if not links:
        status = "not_found"
    elif any(repo.get("status") == "inspected" for repo in repositories):
        status = "inspected"
    elif any(repo.get("status") == "failed" for repo in repositories):
        status = "failed"
    else:
        status = "not_accessed"
    return {
        "status": status,
        "repositories": repositories,
        "inspected_files": [path for repo in repositories for path in repo.get("inspected_files", [])],
        "implementation_findings": [
            finding for repo in repositories for finding in repo.get("implementation_findings", [])
        ],
        "limitations": [limitation for repo in repositories for limitation in repo.get("limitations", [])],
        "reviewed_at": utc_now(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect source repositories reported by a publication.")
    parser.add_argument("--publication", required=True, help="Publication, analysis, proposal, or decision JSON.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--file-limit", type=int, default=12)
    args = parser.parse_args()
    doc = load_json(args.publication)
    doc["repository_review"] = inspect(doc, args.ref, args.file_limit)
    write_json(Path(args.out), doc)


if __name__ == "__main__":
    main()
