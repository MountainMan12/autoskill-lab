from __future__ import annotations

import argparse
import re
import urllib.request
from difflib import SequenceMatcher

from pubskill_common import load_json, utc_now, write_json


REPO_API = "https://api.github.com/repos/K-Dense-AI/scientific-agent-skills/git/trees/main?recursive=1"
REPO_URL = "https://github.com/K-Dense-AI/scientific-agent-skills"


def fetch_repo_paths() -> list[str]:
    request = urllib.request.Request(REPO_API, headers={"User-Agent": "publication-to-skill-builder/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = __import__("json").loads(response.read().decode("utf-8"))
    return [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]


def score(a: str, b: str) -> float:
    normalize = lambda value: re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def check(proposal_doc: dict, paths: list[str] | None = None) -> dict:
    proposal = proposal_doc["proposal"]
    skill_name = proposal["skill_name"]
    status = "searched"
    errors = []
    if paths is None:
        try:
            paths = fetch_repo_paths()
        except Exception as exc:
            paths = []
            status = "search_failed"
            errors.append(str(exc))

    matches = []
    for path in paths:
        if not path.lower().endswith(("skill.md", ".md", ".py", ".yaml", ".yml")):
            continue
        candidate = path.rsplit("/", 1)[0] if path.lower().endswith("skill.md") else path
        similarity = score(skill_name, candidate)
        if skill_name in candidate.lower() or similarity >= 0.62:
            matches.append(
                {
                    "path": path,
                    "url": f"{REPO_URL}/blob/main/{path}",
                    "similarity": round(similarity, 3),
                }
            )
    matches = sorted(matches, key=lambda item: item["similarity"], reverse=True)[:5]
    recommendation = "reuse_existing" if matches and matches[0]["similarity"] >= 0.82 else "create_new"
    if status == "search_failed":
        recommendation = "manual_review_required"
    return {
        "repository": REPO_URL,
        "status": status,
        "matches": matches,
        "recommendation": recommendation,
        "errors": errors,
        "searched_at": utc_now(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for similar existing scientific skills.")
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--paths-fixture", help="Optional newline-delimited paths fixture for tests/offline runs.")
    args = parser.parse_args()
    proposal_doc = load_json(args.proposal)
    paths = None
    if args.paths_fixture:
        paths = [line.strip() for line in open(args.paths_fixture, encoding="utf-8") if line.strip()]
    proposal_doc["duplicate_check"] = check(proposal_doc, paths)
    write_json(args.out, proposal_doc)


if __name__ == "__main__":
    main()
