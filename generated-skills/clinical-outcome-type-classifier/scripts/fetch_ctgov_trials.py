from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


CTGOV_STUDY_URL = "https://clinicaltrials.gov/api/v2/studies/{nct_id}"
NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def normalize_trial_id(value: str) -> str:
    match = NCT_RE.search(value.strip())
    if not match:
        raise ValueError(f"Could not find an NCT identifier in: {value}")
    return match.group(0).upper()


def load_trial_inputs(values: list[str], input_file: str | None = None) -> list[str]:
    raw_values = list(values)
    if input_file:
        raw_values.extend(
            line.strip()
            for line in Path(input_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    trial_ids = []
    seen = set()
    for value in raw_values:
        trial_id = normalize_trial_id(value)
        if trial_id not in seen:
            seen.add(trial_id)
            trial_ids.append(trial_id)
    return trial_ids


def fetch_trial(trial_id: str) -> dict[str, Any]:
    url = CTGOV_STUDY_URL.format(nct_id=urllib.parse.quote(trial_id))
    request = urllib.request.Request(url, headers={"User-Agent": "autoskill-lab/ctgov-helper"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ClinicalTrials.gov returned HTTP {exc.code} for {trial_id}") from exc


def module(study: dict[str, Any], section: str, name: str) -> dict[str, Any]:
    return study.get(section, {}).get(name, {}) or {}


def brief_metadata(study: dict[str, Any]) -> dict[str, Any]:
    identification = module(study, "protocolSection", "identificationModule")
    status = module(study, "protocolSection", "statusModule")
    description = module(study, "protocolSection", "descriptionModule")
    conditions = module(study, "protocolSection", "conditionsModule")
    return {
        "nct_id": identification.get("nctId", ""),
        "brief_title": identification.get("briefTitle", ""),
        "official_title": identification.get("officialTitle", ""),
        "overall_status": status.get("overallStatus", ""),
        "start_date": status.get("startDateStruct", {}).get("date", ""),
        "completion_date": status.get("completionDateStruct", {}).get("date", ""),
        "brief_summary": description.get("briefSummary", ""),
        "conditions": conditions.get("conditions", []),
    }


def parse_design_arms(study: dict[str, Any]) -> list[dict[str, Any]]:
    arms_module = module(study, "protocolSection", "armsInterventionsModule")
    arms = []
    for arm in arms_module.get("armGroups", []) or []:
        arms.append(
            {
                "arm_label": arm.get("label", ""),
                "arm_type": arm.get("type", ""),
                "description": arm.get("description", ""),
                "intervention_names": arm.get("interventionNames", []) or [],
            }
        )
    return arms


def parse_outcomes_and_analyses(study: dict[str, Any], nct_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    outcomes_module = module(study, "resultsSection", "outcomeMeasuresModule")
    outcomes = []
    analyses = []
    for outcome in outcomes_module.get("outcomeMeasures", []) or []:
        outcome_title = outcome.get("title", "")
        outcome_record = {
            "nct_id": nct_id,
            "outcome_title": outcome_title,
            "outcome_type": outcome.get("type", ""),
            "time_frame": outcome.get("timeFrame", ""),
            "description": outcome.get("description", ""),
            "population_description": outcome.get("populationDescription", ""),
            "groups": [],
        }
        for group in outcome.get("groups", []) or []:
            outcome_record["groups"].append(
                {
                    "group_id": group.get("id", ""),
                    "group_title": group.get("title", ""),
                    "group_description": group.get("description", ""),
                }
            )
        outcomes.append(outcome_record)
        for analysis in outcome.get("analyses", []) or []:
            analyses.append(
                {
                    "nct_id": nct_id,
                    "outcome_title": outcome_title,
                    "group_ids": analysis.get("groupIds", []) or [],
                    "group_description": analysis.get("groupDescription", ""),
                    "statistical_method": analysis.get("statisticalMethod", ""),
                    "p_value": analysis.get("pValue", ""),
                    "p_value_comment": analysis.get("pValueComment", ""),
                    "ci_num_sides": analysis.get("ciNumSides", ""),
                    "ci_percent": analysis.get("ciPctValue", ""),
                    "ci_lower_limit": analysis.get("ciLowerLimit", ""),
                    "ci_upper_limit": analysis.get("ciUpperLimit", ""),
                    "param_type": analysis.get("paramType", ""),
                    "param_value": analysis.get("paramValue", ""),
                    "estimate_description": analysis.get("estimateDescription", ""),
                    "dispersion_type": analysis.get("dispersionType", ""),
                    "raw_analysis": analysis,
                }
            )
    return outcomes, analyses


def parse_adverse_events(study: dict[str, Any], nct_id: str) -> list[dict[str, Any]]:
    ae_module = module(study, "resultsSection", "adverseEventsModule")
    group_lookup = {
        group.get("id", ""): group
        for group in ae_module.get("eventGroups", []) or []
    }
    rows = []
    for severity, key in [("serious", "seriousEvents"), ("other", "otherEvents")]:
        for event in ae_module.get(key, []) or []:
            for stat in event.get("stats", []) or []:
                group = group_lookup.get(stat.get("groupId", ""), {})
                rows.append(
                    {
                        "nct_id": nct_id,
                        "severity": severity,
                        "organ_system": event.get("organSystem", ""),
                        "event_term": event.get("term", ""),
                        "group_id": stat.get("groupId", ""),
                        "group_title": group.get("title", ""),
                        "subjects_affected": stat.get("numAffected", ""),
                        "subjects_at_risk": stat.get("numAtRisk", ""),
                        "raw_stat": stat,
                    }
                )
    return rows


def normalize_study(study: dict[str, Any]) -> dict[str, Any]:
    metadata = brief_metadata(study)
    nct_id = metadata["nct_id"]
    outcomes, analyses = parse_outcomes_and_analyses(study, nct_id)
    return {
        "metadata": metadata,
        "design_arms": parse_design_arms(study),
        "outcomes": outcomes,
        "statistical_analyses": analyses,
        "adverse_events": parse_adverse_events(study, nct_id),
    }


def run(trial_ids: list[str], raw_dir: str | None = None) -> dict[str, Any]:
    normalized_trials = []
    errors = []
    raw_output = Path(raw_dir) if raw_dir else None
    for trial_id in trial_ids:
        try:
            raw_study = fetch_trial(trial_id)
            if raw_output:
                write_json(raw_output / f"{trial_id}.json", raw_study)
            normalized = normalize_study(raw_study)
            normalized["source"] = {
                "trial_id": trial_id,
                "api_url": CTGOV_STUDY_URL.format(nct_id=trial_id),
            }
            normalized_trials.append(normalized)
        except Exception as exc:
            errors.append({"trial_id": trial_id, "error": str(exc)})
    return {"trial_count": len(normalized_trials), "trials": normalized_trials, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and normalize ClinicalTrials.gov v2 study records.")
    parser.add_argument("--trial", action="append", default=[], help="NCT ID or ClinicalTrials.gov trial URL.")
    parser.add_argument("--input", help="Text file with one NCT ID or ClinicalTrials.gov trial URL per line.")
    parser.add_argument("--out", required=True, help="Output normalized JSON path.")
    parser.add_argument("--raw-dir", help="Optional directory for raw API study JSON.")
    args = parser.parse_args()
    trial_ids = load_trial_inputs(args.trial, args.input)
    write_json(args.out, run(trial_ids, args.raw_dir))


if __name__ == "__main__":
    main()
