---
name: ctgov-arm-results-kg-builder
description: Build an arm-level ClinicalTrials.gov results knowledge graph that links efficacy, comparator context, outcome categories, and serious adverse events from registry XML or JSON.
metadata:
  source: publication-to-skill-builder
---

# ctgov-arm-results-kg-builder

Use this skill when the user wants to convert ClinicalTrials.gov reported-results data into an arm-level efficacy and safety knowledge graph. Accept raw ClinicalTrials.gov XML, `AllPublicXML.zip`, ClinicalTrials.gov JSON, or normalized JSON exports that preserve study design arms, statistical analyses, outcomes, and adverse-event counts.

This skill is derived from:

- Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov
- DOI: 10.1038/s41597-023-02869-7
- Paper type: original research
- Analysis basis: user PDF

## Workflow

1. Identify the input format: XML files, zipped XML snapshot, ClinicalTrials.gov JSON, or normalized JSON.
2. If the user provides ClinicalTrials.gov trial IDs or URLs instead of local data files, run `scripts/fetch_ctgov_trials.py` to fetch single or bulk trial records from the ClinicalTrials.gov v2 API and normalize arms, outcomes, statistical analyses, and adverse events.
3. Preserve the original trial identifier, usually `NCT_ID` or `nct_id`, throughout every derived table.
4. Normalize trial design arms into a table with arm title, arm type or label, intervention names, and source fields.
5. Extract efficacy rows from reported-results statistical analysis blocks under each outcome. Keep group names, outcome title, outcome type when available, p-value, confidence interval limits, statistical method, parameter type, and raw source text.
6. Match efficacy group names back to design arms. Use exact matching first, then case/space-normalized matching, then semantic similarity or embeddings when available. Record match scores and unresolved groups.
7. Classify efficacy as positive or negative using the paper-grounded rule pipeline: valid p-value <= 0.05 is positive; otherwise use confidence intervals where ratio parameters are positive when the interval excludes 1 and difference parameters are positive when the interval excludes 0.
8. Extract serious adverse events from adverse-event records. Keep event title, category, group, affected count, at-risk count, severity, and original source fields.
9. Normalize outcomes when possible with MeSH/MTI or a substitute ontology workflow. Distinguish biomarker, patient-reported outcome, and clinical endpoint categories when evidence supports the label.
10. Build graph-ready nodes for intervention arms, outcomes, adverse events, conditions, and trials. Build edges for efficacy and safety relationships with all relevant attributes.
11. Produce validation and limitation notes, including excluded trials, ambiguous arm matches, missing p-values or intervals, and unavailable ontology mappings.

For JSON inputs, do not assume one canonical schema. First inspect keys and map them to the conceptual fields above. If the JSON is already normalized into efficacy, safety, or arm tables, preserve those records and add missing derived columns instead of reparsing from scratch.

## Method Basis

The paper describes downloading all ClinicalTrials.gov XML records, extracting statistical-analysis and adverse-event sections, separating intervention and comparator arms, classifying efficacy from p-values or confidence intervals, linking serious adverse events to arms, and constructing a graph schema for intervention, outcome, and adverse-event nodes.

## Expected Inputs

- ClinicalTrials.gov XML files or an AllPublicXML.zip snapshot
- ClinicalTrials.gov trial IDs such as `NCT01050998`
- ClinicalTrials.gov trial URLs such as `https://clinicaltrials.gov/study/NCT01050998`
- ClinicalTrials.gov JSON records or normalized JSON exports with study design, statistical analysis, and adverse-event fields
- Study design arm labels and reported-results statistical analysis blocks
- Adverse event event/subtitle/count records
- Optional MeSH/MTI outputs for outcome normalization

## Expected Outputs

- Arm-level efficacy table with intervention, comparator, outcome, p-value or confidence interval evidence, and positive/negative label
- Serious-adverse-event safety table with affected and at-risk counts
- Knowledge graph import files or schema-ready triples/edges
- Validation summary and limitations report

## Helper Scripts

Use `scripts/fetch_ctgov_trials.py` when the user provides trial IDs or URLs:

```bash
python scripts/fetch_ctgov_trials.py --trial NCT01050998 --out ctgov_trials.json
python scripts/fetch_ctgov_trials.py --input trial_ids_or_urls.txt --out ctgov_trials.json --raw-dir raw-ctgov
```

The script uses the ClinicalTrials.gov v2 single-study endpoint and emits normalized `metadata`, `design_arms`, `outcomes`, `statistical_analyses`, and `adverse_events` arrays for downstream graph construction.

## Source Links

- https://doi.org/10.1038/s41597-023-02869-7
- https://pubmed.ncbi.nlm.nih.gov/38184674/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10771511/

## Code Availability

- https://github.com/xuanyshi/Finer-Grained-Clinical-Trial-Results

## Limitations

- The paper reports 84% intervention-arm and 80% comparator-arm accuracy for BioBERT mapping on a 100-record manually annotated sample.
- The method excludes studies without exactly two comparable arms or usable experimental/comparator design labels.
- Outcome category rules rely on MeSH/MTI and keyword heuristics, so local access to those tools or a substitute ontology workflow is needed.
