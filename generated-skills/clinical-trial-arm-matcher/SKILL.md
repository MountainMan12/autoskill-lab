---
name: clinical-trial-arm-matcher
description: Map unlabeled statistical-analysis arm-group names back to experimental and comparator design arms.
metadata:
  source: publication-to-skill-builder
---

# clinical-trial-arm-matcher

Use this skill when the user wants to map reported-results group names back to clinical trial design arms, especially when statistical-analysis groups are not explicitly labeled as intervention or comparator. Accept ClinicalTrials.gov XML-derived tables, JSON records, CSV files, spreadsheets, or dataframe-like inputs.

This skill is derived from:

- Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov
- DOI: 10.1038/s41597-023-02869-7
- Paper type: original research
- Analysis basis: user PDF

## Workflow

1. Inspect input fields and identify design-arm titles, design-arm labels or types, intervention names, and reported-results group names.
2. If the user provides ClinicalTrials.gov trial IDs or URLs instead of local tables, run `scripts/fetch_ctgov_trials.py` to fetch single or bulk trial records from the ClinicalTrials.gov v2 API and normalize design arms plus outcome-analysis group IDs.
3. Normalize strings with lowercasing, whitespace cleanup, punctuation cleanup, dose/unit normalization where safe, and synonym-preserving tokenization.
4. Run deterministic matching first: exact match, normalized exact match, containment checks, and intervention-name overlap.
5. When deterministic matching is insufficient, compute semantic similarity between design-arm names and result-group names using an available biomedical embedding model or a general embedding fallback.
6. Assign each reported-results group to the design arm with the strongest supported match, while respecting the trial-local arm set.
7. For two-arm efficacy comparisons, identify intervention and comparator groups from matched design-arm labels when available.
8. Emit match score, match method, source fields, and ambiguity flags. Do not silently force a match when evidence is weak.
9. Produce a validation summary with unresolved groups, many-to-one matches, low-confidence assignments, and any assumptions.

## Method Basis

The paper embeds titles from the study design and statistical analysis sections with BioBERT and assigns labels by highest semantic similarity.

## Expected Inputs

- Design-arm names and labels
- Reported-results group names
- ClinicalTrials.gov trial IDs or URLs when source records should be fetched directly
- Embedding model or equivalent semantic matcher
- JSON records containing trial design arms and reported-results groups

## Expected Outputs

- Intervention_group and comparator_group assignments with similarity scores

## Helper Scripts

Use `scripts/fetch_ctgov_trials.py` when the user provides trial IDs or URLs:

```bash
python scripts/fetch_ctgov_trials.py --trial NCT01050998 --out ctgov_trials.json
python scripts/fetch_ctgov_trials.py --input trial_ids_or_urls.txt --out ctgov_trials.json --raw-dir raw-ctgov
```

The script uses the ClinicalTrials.gov v2 single-study endpoint and emits normalized `metadata`, `design_arms`, `outcomes`, `statistical_analyses`, and `adverse_events`. For this skill, use `design_arms`, outcome `groups`, and `statistical_analyses.group_ids` as the matching inputs.

## Source Links

- https://doi.org/10.1038/s41597-023-02869-7
- https://pubmed.ncbi.nlm.nih.gov/38184674/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10771511/

## Code Availability

- https://github.com/xuanyshi/Finer-Grained-Clinical-Trial-Results

## Limitations

- Accuracy was imperfect in the paper's manual validation and may vary by intervention naming quality.
