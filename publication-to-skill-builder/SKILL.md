---
name: publication-to-skill-builder
description: Build AI-grounded Codex skill proposals from complete open scientific publications, with provenance, duplicate checks, and required per-paper user approval before scaffolding generated skills.
metadata:
  short-description: Create skill proposals from papers
---

# Publication-to-Skill Builder

Use this skill when the user wants to extract reusable computational ideas from scientific publications and turn them into Codex skills.

## Core Rules

- Process at most 10 publications per run. If more are supplied, stop and ask the user to split the batch.
- Accept PubMed IDs, PMC IDs, DOIs, Europe PMC/PubMed/publisher URLs, open PDF URLs, local PDF paths, or a text file containing any of these.
- Fetch metadata and openly available full text/PDFs only from lawful public sources.
- Parse user-provided PDFs locally when supplied.
- Parse and inspect the complete paper body whenever full text or a PDF is available. Exclude references, bibliography, literature-cited, and works-cited sections from analysis.
- Treat review articles, benchmark papers, workflow papers, database/resource papers, software papers, and tutorials as valid sources of skill ideas.
- Do not invent techniques. Ground every proposed skill in paper evidence and mark uncertainty clearly.
- Check `https://github.com/K-Dense-AI/scientific-agent-skills` before proposing a new skill.
- Do not scaffold a generated skill until the user approves the proposal for that specific publication.
- If the user declines, ask what skill they would have preferred, record that feedback, and do not implement it unless the user explicitly asks later.
- Publish generated skills on the current repository branch. Do not create or switch to a publishing branch unless the user explicitly asks.
- Do not push to GitHub unless the user explicitly asks for a push.

## Workflow

For a normal run:

1. Read [references/workflow.md](references/workflow.md).
2. Normalize the user inputs with `scripts/normalize_inputs.py`.
3. Fetch metadata and open full text/PDF availability with `scripts/fetch_publication.py`.
4. Parse complete PDFs with `scripts/parse_pdf.py` when PDFs are available or supplied.
5. Prepare a full-paper AI analysis bundle with `scripts/analyze_publication.py`.
6. As Codex, read the analysis bundle and generate ranked `candidate_skills` without using a hardcoded technique list.
7. Select the strongest candidate as `proposal`, then check it with `scripts/check_existing_skills.py`.
8. Present the selected proposal and alternates to the user for approval.
9. Record the user decision with `scripts/write_provenance.py`.
10. Scaffold only approved skills with `scripts/scaffold_skill.py`.
11. Stage generated skills and `published-skills.md` on the current branch only when the user requests Git preparation or publishing.

Use [references/provenance-schema.md](references/provenance-schema.md) whenever writing or inspecting provenance JSON.

## Output Locations

- `runs/<run-id>/inputs.json`
- `runs/<run-id>/publications/*.json`
- `runs/<run-id>/analysis/*.json`
- `runs/<run-id>/proposals/*.json`
- `runs/<run-id>/decisions/*.json`
- `generated-skills/<skill-name>/`

The generated skill folder should include a concise `SKILL.md` and a provenance JSON file copied from the approved decision.
