# Provenance Schema

Provenance is stored as JSON. JSON is the source of truth for all publication, proposal, approval, and feedback state.

## Top-Level Shape

```json
{
  "paper": {},
  "content": {},
  "availability": {},
  "paper_type": "unknown",
  "analysis_basis": "full text",
  "candidate_skills": [],
  "proposal": {},
  "duplicate_check": {},
  "decision": {}
}
```

## Required Sections

`paper`:

- `title`
- `authors`
- `journal`
- `publication_date`
- `doi`
- `pmid`
- `pmcid`
- `urls`
- `source_type`
- `source_value`

`content`:

- `abstract`
- `full_text`
- `pages`
- `sections`
- `detected_headings`
- `captions`
- `excluded_sections`
- `methods_text`
- `methods_summary`
- `extraction_status`
- `parser`
- `limitations`

`availability`:

- `full_text_available`
- `pdf_available`
- `pdf_path`
- `data_availability`
- `code_availability`
- `repository_links`

`paper_type`:

- `original research`
- `review`
- `benchmark`
- `workflow`
- `software/resource`
- `unknown`

`analysis_basis`:

- `full text`
- `abstract only`
- `PDF text`
- `full-text XML`
- `user PDF`
- `metadata only`

`candidate_skills`:

- `skill_name`
- `purpose`
- `evidence`
- `reusable_value`
- `expected_inputs`
- `expected_outputs`
- `implementation_complexity`
- `limitations`
- `rank`

`proposal`:

- `skill_name`
- `description`
- `usefulness`
- `evidence`
- `expected_inputs`
- `expected_outputs`
- `limitations`
- `status`

`duplicate_check`:

- `repository`
- `status`
- `matches`
- `recommendation`
- `searched_at`

`decision`:

- `status`: `pending`, `approved`, or `declined`
- `user_feedback`
- `decided_at`

Do not scaffold generated skills from decisions where `decision.status` is not `approved`.
