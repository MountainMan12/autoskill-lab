# Publication-to-Skill Workflow

## Input Handling

Normalize user inputs into publication records before fetching content. Supported input values are:

- PMID values such as `12345678` or `PMID:12345678`.
- PMCID values such as `PMC1234567`.
- DOI values such as `10.1038/s41586-020-2649-2` or DOI URLs.
- PubMed, Europe PMC, PMC, publisher, and direct PDF URLs.
- Local PDF paths.
- Text files containing one publication input per line.

Reject runs containing more than 10 publication records.

## Retrieval

Use public APIs and open resources where available:

- Europe PMC search and full-text metadata.
- NCBI/PubMed and PMC pages when identifiers are known.
- Crossref metadata for DOI fallback.
- Direct PDF URLs when the user provides them.

Record retrieval failures in provenance. Do not treat a failed fetch as evidence that the method does not exist.

## Full-Paper Analysis

Prefer full text over abstracts. Prefer PDF text over abstract-only metadata when full text XML is unavailable. Analyze the complete paper body, not only a Methods section.

Exclude references before downstream analysis. Do not include reference lists, bibliography sections, literature-cited sections, or works-cited sections in `content.full_text`, page text used for AI review, section summaries, repository-link extraction, or candidate-skill evidence.

Extract and summarize:

- Full text and page-level text.
- Section headings and section text when detectable.
- Methods or Materials and Methods when present.
- Review article concepts, workflow ideas, comparative recommendations, and reusable analysis patterns.
- Computational/statistical methods.
- Software packages, tools, and pipelines.
- Data availability.
- Code availability.
- Repository links.
- Inputs, outputs, and reusable steps.

If extraction is partial, mark `content.extraction_status` as `partial` and explain the limitation.

Run `scripts/analyze_publication.py` to prepare a structured AI prompt bundle. The script must not decide skill ideas through hardcoded biomedical keywords. It prepares evidence; Codex performs the AI reasoning.

When reviewing the AI bundle, consider:

- Original research papers.
- Review articles.
- Benchmark and comparison papers.
- Tutorials and protocols.
- Workflow and pipeline papers.
- Software, database, and resource papers.

Generate ranked candidate skills from the whole publication. Each candidate should be grounded in paper evidence and explain why it is reusable beyond the specific biological question.

## Proposal Review

For each publication, present:

- Citation and identifiers.
- Selected candidate skill name.
- Alternate candidate skills when useful.
- What each skill would do.
- Why it is reusable.
- Evidence from the paper.
- Expected inputs and outputs.
- Data/code availability.
- Existing-skill search result.
- Limitations.

The user must approve or decline each proposal before scaffolding.

## Publishing Workflow

Generated skills belong under `generated-skills/`. Published skills should be listed in `published-skills.md` with links to the skill folder and approval provenance.

When the user asks to prepare or publish generated skills, use `scripts/prepare_published_skills.py` to stage generated skill files and `published-skills.md` on the current branch. Do not create or switch branches unless the user explicitly asks.
