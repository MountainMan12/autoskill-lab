from __future__ import annotations

import argparse

from pubskill_common import load_json, utc_now, write_json


def build_decision(proposal_doc: dict, status: str, feedback: str = "") -> dict:
    if status not in {"pending", "approved", "declined"}:
        raise ValueError("Decision status must be pending, approved, or declined.")
    return {
        "paper": proposal_doc.get("paper", {}),
        "content": proposal_doc.get("content", {}),
        "availability": proposal_doc.get("availability", {}),
        "paper_type": proposal_doc.get("paper_type", "unknown"),
        "analysis_basis": proposal_doc.get("analysis_basis", "metadata only"),
        "candidate_skills": proposal_doc.get("candidate_skills", []),
        "repository_review": proposal_doc.get("repository_review", {}),
        "helper_scripts": proposal_doc.get("helper_scripts", []),
        "proposal": proposal_doc.get("proposal", {}),
        "duplicate_check": proposal_doc.get(
            "duplicate_check",
            {
                "repository": "https://github.com/K-Dense-AI/scientific-agent-skills",
                "status": "not_searched",
                "matches": [],
                "recommendation": "manual_review_required",
                "searched_at": "",
            },
        ),
        "decision": {
            "status": status,
            "user_feedback": feedback,
            "decided_at": utc_now() if status in {"approved", "declined"} else "",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write proposal decision provenance.")
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--status", choices=["pending", "approved", "declined"], default="pending")
    parser.add_argument("--feedback", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    decision = build_decision(load_json(args.proposal), args.status, args.feedback)
    write_json(args.out, decision)


if __name__ == "__main__":
    main()
