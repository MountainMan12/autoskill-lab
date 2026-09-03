# Published Skills

Use this registry to track skills generated from publications and published in this repository.

Each entry should link to the skill itself and to the provenance record used to approve and publish it.

## Registry

| Skill | Source publication | Provenance | Status | Published date | Notes |
| --- | --- | --- | --- | --- | --- |
| [`ctgov-arm-results-kg-builder`](generated-skills/ctgov-arm-results-kg-builder/) | Shi & Du, _Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov_; PMID: `38184674`; PMCID: `PMC10771511`; DOI: `10.1038/s41597-023-02869-7` | [`provenance.json`](generated-skills/ctgov-arm-results-kg-builder/provenance.json) | Published | `2026-09-03` | Approved from user-PDF full-paper analysis. Supports ClinicalTrials.gov XML and JSON inputs. Duplicate check: no matches; create new. |
| [`clinical-trial-efficacy-significance-classifier`](generated-skills/clinical-trial-efficacy-significance-classifier/) | Shi & Du, _Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov_; PMID: `38184674`; PMCID: `PMC10771511`; DOI: `10.1038/s41597-023-02869-7` | [`provenance.json`](generated-skills/clinical-trial-efficacy-significance-classifier/provenance.json) | Published | `2026-09-03` | Approved alternate from user-PDF full-paper analysis. Classifies efficacy from p-values and confidence intervals. |
| [`clinical-trial-arm-matcher`](generated-skills/clinical-trial-arm-matcher/) | Shi & Du, _Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov_; PMID: `38184674`; PMCID: `PMC10771511`; DOI: `10.1038/s41597-023-02869-7` | [`provenance.json`](generated-skills/clinical-trial-arm-matcher/provenance.json) | Published | `2026-09-03` | Approved alternate from user-PDF full-paper analysis. Maps reported-results groups to design arms. |
| [`clinical-outcome-type-classifier`](generated-skills/clinical-outcome-type-classifier/) | Shi & Du, _Constructing a finer-grained representation of clinical trial results from ClinicalTrials.gov_; PMID: `38184674`; PMCID: `PMC10771511`; DOI: `10.1038/s41597-023-02869-7` | [`provenance.json`](generated-skills/clinical-outcome-type-classifier/provenance.json) | Published | `2026-09-03` | Approved alternate from user-PDF full-paper analysis. Classifies outcomes as biomarker, patient-reported outcome, clinical endpoint, or unresolved. |

## Entry Format

When a skill is published, replace the placeholder row with entries like:

| Skill | Source publication | Provenance | Status | Published date | Notes |
| --- | --- | --- | --- | --- | --- |
| [`example-skill`](generated-skills/example-skill/) | PMID: `12345678`; DOI: `10.xxxx/example` | [`provenance.json`](generated-skills/example-skill/provenance.json) | Published | `YYYY-MM-DD` | Approved from full-paper AI analysis. |

## Required Provenance

Every published skill entry should preserve:

- Link to the generated skill directory.
- Paper title and identifiers where available.
- Link to the approval provenance JSON.
- Whether the analysis was based on full text, PDF text, user PDF, abstract only, or metadata only.
- User approval status.
- Any limitations from extraction or duplicate-skill review.
