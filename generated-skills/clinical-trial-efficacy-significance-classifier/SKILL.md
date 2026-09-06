---
name: clinical-trial-efficacy-significance-classifier
description: Classify registry-reported efficacy analyses as positive or negative from p-values and confidence intervals.
metadata:
  source: publication-to-skill-builder
---

# clinical-trial-efficacy-significance-classifier

Use this skill when the user wants to classify clinical-trial efficacy result rows as positive, negative, or unresolved from p-values and confidence intervals. Accept CSV, spreadsheet, dataframe-like tables, JSON arrays, JSONL, or records parsed from ClinicalTrials.gov XML/JSON.

This skill is derived from:

- Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov
- DOI: 10.1038/s41597-023-02869-7
- Paper type: original research
- Analysis basis: user PDF

## Workflow

1. Inspect the input columns or JSON keys and identify trial id, outcome title, groups, p-value, confidence interval lower/upper bounds, statistical method, and parameter name.
2. If the user provides ClinicalTrials.gov trial IDs or URLs instead of local result rows, run `scripts/fetch_ctgov_trials.py` to fetch single or bulk trial records from the ClinicalTrials.gov v2 API and normalize reported-results statistical analyses.
3. Preserve raw fields and create normalized fields for numeric p-value, lower limit, upper limit, parameter class, and parse warnings.
4. Treat p-values as valid when they can be parsed from forms such as `0.03`, `<0.001`, `<= 0.05`, or equivalent numeric strings. Use the numeric threshold implied by the operator.
5. If a valid p-value exists, label the result positive when p-value <= 0.05 and negative otherwise.
6. If no valid p-value exists but a confidence interval exists, classify the statistical parameter as ratio-type for odds ratio, hazard ratio, risk ratio, relative risk, or similar measures; classify it as difference-type for mean difference, risk difference, absolute difference, or similar measures.
7. For ratio-type intervals, label positive when the interval excludes 1 and negative when it contains 1.
8. For difference-type intervals, label positive when the interval excludes 0 and negative when it contains 0.
9. Mark rows unresolved when required numeric fields or parameter semantics are missing or contradictory.
10. Return an audit summary with counts by label and a row-level explanation column.

## Method Basis

The Methods section lays out a rule pipeline: prefer valid p-values, then confidence intervals; compare p-values to 0.05; for ratio parameters test whether the interval contains 1; for difference parameters test whether it contains 0.

## Expected Inputs

- Parsed statistical analysis rows with p-values, confidence intervals, and parameter names
- ClinicalTrials.gov trial IDs or URLs when source records should be fetched directly
- JSON arrays or JSONL records containing equivalent statistical-analysis fields

## Expected Outputs

- Normalized significance labels and audit flags

## Helper Scripts

Use `scripts/fetch_ctgov_trials.py` when the user provides trial IDs or URLs:

```bash
python scripts/fetch_ctgov_trials.py --trial NCT01050998 --out ctgov_trials.json
python scripts/fetch_ctgov_trials.py --input trial_ids_or_urls.txt --out ctgov_trials.json --raw-dir raw-ctgov
```

The script uses the ClinicalTrials.gov v2 single-study endpoint and emits normalized `statistical_analyses` rows containing p-values, confidence intervals, statistical methods, parameter fields, group IDs, and raw analysis records.

## Source Links

- https://doi.org/10.1038/s41597-023-02869-7
- https://pubmed.ncbi.nlm.nih.gov/38184674/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10771511/

## Code Availability

- https://github.com/xuanyshi/Finer-Grained-Clinical-Trial-Results

## Limitations

- Depends on messy ClinicalTrials.gov strings being cleaned into numeric values and parameter types.
