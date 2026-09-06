---
name: clinical-outcome-type-classifier
description: Classify trial outcome titles into biomarker, patient-reported outcome, and clinical endpoint categories.
metadata:
  source: publication-to-skill-builder
---

# clinical-outcome-type-classifier

Use this skill when the user wants to classify clinical trial outcome titles into biomarker, patient-reported outcome, clinical endpoint, or unresolved categories. Accept outcome lists from CSV, spreadsheets, dataframes, JSON arrays, JSONL, ClinicalTrials.gov XML, or ClinicalTrials.gov JSON.

This skill is derived from:

- Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov
- DOI: 10.1038/s41597-023-02869-7
- Paper type: original research
- Analysis basis: user PDF

## Workflow

1. Inspect input fields and identify outcome title, outcome measure type, trial id, condition, and any existing ontology annotations.
2. If the user provides ClinicalTrials.gov trial IDs or URLs instead of local outcome rows, run `scripts/fetch_ctgov_trials.py` to fetch single or bulk trial records from the ClinicalTrials.gov v2 API and normalize outcome titles, types, time frames, descriptions, and conditions.
3. Preserve raw outcome text and create normalized text for matching.
4. If MeSH/MTI annotations are available, use them directly and keep matched terms and tree numbers as evidence.
5. If ontology annotations are unavailable, use available biomedical term extraction or mark the ontology-dependent portion as unavailable.
6. Label biomarker outcomes when supported by MeSH tree categories for chemicals/drugs or analytical, diagnostic, and therapeutic techniques/equipment, while excluding survey/questionnaire terms from biomarker evidence.
7. Label patient-reported outcomes when the title or ontology evidence indicates surveys, questionnaires, patient-reported measures, scales, or scores.
8. Label clinical endpoints when disease-related MeSH categories or equivalent condition/outcome evidence supports the label.
9. Allow multiple evidence signals but emit one primary category plus supporting evidence and ambiguity flags.
10. Return unresolved when labels cannot be grounded in title, ontology, or documented rules.

## Method Basis

The paper uses MeSH/MTI, MeSH tree roots, and patient-reported keyword matching to classify outcome titles.

## Expected Inputs

- Outcome titles
- MeSH/MTI annotations or ontology mappings
- ClinicalTrials.gov trial IDs or URLs when source records should be fetched directly
- JSON records containing outcome titles and optional ontology annotations

## Expected Outputs

- Outcome category labels and supporting matched terms

## Helper Scripts

Use `scripts/fetch_ctgov_trials.py` when the user provides trial IDs or URLs:

```bash
python scripts/fetch_ctgov_trials.py --trial NCT01050998 --out ctgov_trials.json
python scripts/fetch_ctgov_trials.py --input trial_ids_or_urls.txt --out ctgov_trials.json --raw-dir raw-ctgov
```

The script uses the ClinicalTrials.gov v2 single-study endpoint and emits normalized `outcomes` rows containing trial ID, outcome title, outcome type, time frame, description, population description, and group metadata.

## Source Links

- https://doi.org/10.1038/s41597-023-02869-7
- https://pubmed.ncbi.nlm.nih.gov/38184674/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10771511/

## Code Availability

- https://github.com/xuanyshi/Finer-Grained-Clinical-Trial-Results

## Limitations

- Rules are heuristic and may double-count or miss semantically equivalent outcomes.
