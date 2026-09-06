from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "generated-skills" / "ctgov-arm-results-kg-builder" / "scripts" / "fetch_ctgov_trials.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("fetch_ctgov_trials", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


fetch_ctgov_trials = load_helper()


class CtgovTrialHelperTests(unittest.TestCase):
    def test_normalize_trial_id_accepts_id_and_urls(self) -> None:
        self.assertEqual(fetch_ctgov_trials.normalize_trial_id("nct01050998"), "NCT01050998")
        self.assertEqual(
            fetch_ctgov_trials.normalize_trial_id("https://clinicaltrials.gov/study/NCT01050998"),
            "NCT01050998",
        )

    def test_load_trial_inputs_deduplicates(self) -> None:
        trial_ids = fetch_ctgov_trials.load_trial_inputs(
            ["NCT01050998", "https://clinicaltrials.gov/study/NCT01050998", "NCT03400800"]
        )

        self.assertEqual(trial_ids, ["NCT01050998", "NCT03400800"])

    def test_normalize_study_extracts_trial_tables(self) -> None:
        study = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT01050998",
                    "briefTitle": "Example trial",
                    "officialTitle": "Example official title",
                },
                "statusModule": {"overallStatus": "COMPLETED"},
                "conditionsModule": {"conditions": ["Condition A"]},
                "armsInterventionsModule": {
                    "armGroups": [
                        {
                            "label": "Drug A",
                            "type": "EXPERIMENTAL",
                            "description": "Receives Drug A",
                            "interventionNames": ["Drug: A"],
                        },
                        {
                            "label": "Placebo",
                            "type": "PLACEBO_COMPARATOR",
                            "description": "Receives placebo",
                            "interventionNames": ["Drug: Placebo"],
                        },
                    ]
                },
            },
            "resultsSection": {
                "outcomeMeasuresModule": {
                    "outcomeMeasures": [
                        {
                            "title": "Disease Activity Score",
                            "type": "PRIMARY",
                            "timeFrame": "Day 85",
                            "groups": [
                                {"id": "OG000", "title": "Drug A"},
                                {"id": "OG001", "title": "Placebo"},
                            ],
                            "analyses": [
                                {
                                    "groupIds": ["OG000", "OG001"],
                                    "statisticalMethod": "ANCOVA",
                                    "pValue": "0.03",
                                    "ciLowerLimit": "0.1",
                                    "ciUpperLimit": "1.2",
                                    "paramType": "Mean Difference",
                                }
                            ],
                        }
                    ]
                },
                "adverseEventsModule": {
                    "eventGroups": [{"id": "EG000", "title": "Drug A"}],
                    "seriousEvents": [
                        {
                            "organSystem": "Infections",
                            "term": "Pneumonia",
                            "stats": [{"groupId": "EG000", "numAffected": "1", "numAtRisk": "50"}],
                        }
                    ],
                },
            },
        }

        normalized = fetch_ctgov_trials.normalize_study(study)

        self.assertEqual(normalized["metadata"]["nct_id"], "NCT01050998")
        self.assertEqual(len(normalized["design_arms"]), 2)
        self.assertEqual(normalized["outcomes"][0]["outcome_title"], "Disease Activity Score")
        self.assertEqual(normalized["statistical_analyses"][0]["p_value"], "0.03")
        self.assertEqual(normalized["adverse_events"][0]["event_term"], "Pneumonia")


if __name__ == "__main__":
    unittest.main()
