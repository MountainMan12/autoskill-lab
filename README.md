# Skills Lab

This repository contains `publication-to-skill-builder`, a Codex skill for turning scientific publications into reusable Codex skill proposals.

The skill is designed for papers from sources such as PubMed, Europe PMC, PubMed Central, DOI links, open PDFs, and user-provided local PDFs. It parses the full paper when available, prepares an AI analysis bundle, checks for similar existing skills, and requires your approval before scaffolding any generated skill.

## Can You Use It Now?

Yes, you can use the source in this repo now.

For automatic Codex skill discovery with `$publication-to-skill-builder`, install or copy the folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R publication-to-skill-builder ~/.codex/skills/
```

After that, start a new Codex task and invoke:

```text
Use $publication-to-skill-builder to analyze this DOI and propose reusable skills: 10.xxxx/example
```

If you do not install it, you can still use the scripts directly from this repository.

## What It Does

The skill supports up to 10 publications per run and can handle:

- PubMed IDs.
- PMC IDs.
- DOIs.
- PubMed, Europe PMC, PMC, publisher, and PDF URLs.
- Local PDF files.
- Text files with one publication input per line.

The workflow:

1. Normalize publication inputs.
2. Fetch available metadata and open full-text/PDF information.
3. Parse full PDF body text when available, excluding references.
4. Prepare a full-paper AI analysis bundle.
5. Ask Codex to identify candidate skills from the paper.
6. Check whether a similar skill already exists.
7. Ask you to approve or decline each proposed skill.
8. Scaffold only approved skills.
9. Store provenance for both approvals and declines.

## Dependencies

The scripts use Python standard-library modules where possible.

PDF parsing requires PyMuPDF:

```bash
python -m pip install pymupdf
```

Network access is needed for live metadata retrieval and GitHub duplicate checks.

## Direct Script Usage

Create a run directory:

```bash
RUN_ID="$(date +%Y%m%d-%H%M%S)"
mkdir -p "runs/$RUN_ID/publications" "runs/$RUN_ID/analysis" "runs/$RUN_ID/proposals" "runs/$RUN_ID/decisions"
```

Normalize inputs:

```bash
python publication-to-skill-builder/scripts/normalize_inputs.py \
  --input publications.txt \
  --out "runs/$RUN_ID/inputs.json"
```

Fetch metadata and availability:

```bash
python publication-to-skill-builder/scripts/fetch_publication.py \
  --inputs "runs/$RUN_ID/inputs.json" \
  --out "runs/$RUN_ID/publications"
```

Parse a PDF-backed publication:

```bash
python publication-to-skill-builder/scripts/parse_pdf.py \
  --publication "runs/$RUN_ID/publications/<publication-id>.json" \
  --out "runs/$RUN_ID/publications/<publication-id>.json" \
  --pdf-cache "runs/$RUN_ID/pdf-cache"
```

Prepare the full-paper AI analysis bundle:

```bash
python publication-to-skill-builder/scripts/analyze_publication.py \
  --publication "runs/$RUN_ID/publications/<publication-id>.json" \
  --out "runs/$RUN_ID/analysis/<publication-id>.json"
```

At this point, Codex should read the analysis JSON, inspect `ai_prompt_bundle`, generate ranked `candidate_skills`, select one `proposal`, and present it to you for approval.

## Approval And Provenance

Record a pending decision:

```bash
python publication-to-skill-builder/scripts/write_provenance.py \
  --proposal "runs/$RUN_ID/proposals/<publication-id>.json" \
  --status pending \
  --out "runs/$RUN_ID/decisions/<publication-id>.json"
```

Record an approved decision:

```bash
python publication-to-skill-builder/scripts/write_provenance.py \
  --proposal "runs/$RUN_ID/proposals/<publication-id>.json" \
  --status approved \
  --out "runs/$RUN_ID/decisions/<publication-id>.json"
```

Record a declined decision with feedback:

```bash
python publication-to-skill-builder/scripts/write_provenance.py \
  --proposal "runs/$RUN_ID/proposals/<publication-id>.json" \
  --status declined \
  --feedback "I wanted a reusable plotting workflow instead." \
  --out "runs/$RUN_ID/decisions/<publication-id>.json"
```

Declined feedback is stored but not implemented unless you explicitly request it later.

## Scaffold An Approved Skill

Only approved decisions can be scaffolded:

```bash
python publication-to-skill-builder/scripts/scaffold_skill.py \
  --approved-decision "runs/$RUN_ID/decisions/<publication-id>.json" \
  --out generated-skills
```

The generated skill will be written to:

```text
generated-skills/<skill-name>/
```

## Prepare Published Skills

When you want to prepare generated skills for commit on the current branch:

```bash
python publication-to-skill-builder/scripts/prepare_published_skills.py \
  --path generated-skills \
  --path published-skills.md
```

This stages the selected paths on the current branch. It does not create or switch branches, and it does not push to GitHub.

## Validate

Run the local tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
```

Validate the Codex skill:

```bash
python /Users/pawan/.codex/skills/.system/skill-creator/scripts/quick_validate.py publication-to-skill-builder
```

## Important Guardrails

- Maximum 10 publications per run.
- Full-paper body analysis is preferred over methods-only extraction.
- Reference lists are excluded from parsing and AI review.
- Review articles and workflow papers are valid sources of skill ideas.
- Skill ideas should come from Codex AI reasoning over the full-paper bundle, not hardcoded method keywords.
- Existing skills must be checked before creating a new one.
- No generated skill is scaffolded without your per-publication approval.
- Published skills are committed on the current branch unless you explicitly ask for another branch.
- GitHub push is never automatic.
