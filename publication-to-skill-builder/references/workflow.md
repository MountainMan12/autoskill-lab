# Publication-to-Skill Workflow

## Input Handling

Normalize user inputs into publication records before fetching content. Supported input values are:

- PMID values such as `12345678` or `PMID:12345678`.
- PMCID values such as `PMC1234567`.
- DOI values such as `10.1038/s41586-020-2649-2` or DOI URLs.
- PubMed, Europe PMC, PMC, publisher, and direct PDF URLs.
- Local PDF paths.
- Text files containing one publication input per line.

Do not enforce a fixed publication-count cap. Accept large batches when the user's available AI plan, context window, runtime, and file/network access can support them. For oversized batches, split the work into staged run chunks and continue chunk by chunk, recording each chunk in provenance.

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
- Repository implementation files when accessible and relevant, such as scripts, notebooks, package modules, schemas, tests, and command examples.
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

## Source Repository Review

When the paper reports GitHub, GitLab, Bitbucket, Zenodo source archives, package repositories, notebooks, or other code repositories:

- For GitHub repositories, run `scripts/inspect_repository.py` on the publication, analysis, proposal, or decision JSON before final candidate selection when network access is available.
- Inspect accessible repository metadata and file trees before finalizing candidates when the repository is relevant to implementation.
- Prefer repository files that clarify data formats, parsing rules, algorithm steps, command-line interfaces, tests, schemas, notebooks, or validation routines.
- Record repository URLs, inspected files, and any access limitations in provenance.
- Treat repository code as reference material. Follow its method and cite provenance, but do not copy code unless the license is compatible and copying is necessary.
- If the repository cannot be accessed, record the failure and continue from paper evidence; do not infer missing implementation details.
- If repository code contradicts the paper, mark the discrepancy and prefer the paper unless the user explicitly asks to reproduce the repository behavior.

## Helper Script Planning

Generated skills should include helper scripts when deterministic code would make the method safer or more reusable. Recommend scripts for tasks such as:

- Fetching data from public APIs, repositories, or source databases named by the paper.
- Parsing raw XML, JSON, CSV, TSV, HDF5, FASTQ/BAM/VCF, images, or other domain data.
- Normalizing source-specific schemas into canonical analysis tables.
- Running statistical tests, model scoring, graph construction, validation checks, or figure generation.
- Writing reproducible outputs, summaries, provenance, or audit reports.

For each candidate, include a `helper_scripts` list when scripts are needed. Each script entry should include:

- `path`: relative path under the generated skill, usually `scripts/<name>.py`.
- `purpose`: what the script automates.
- `expected_inputs`.
- `expected_outputs`.
- `implementation_notes`: paper-grounded and repository-grounded behavior to implement.
- `source_references`: paper sections and repository files used as evidence.

Do not propose helper scripts merely to make a skill look substantial. Short procedural skills can remain prose-only when there is no recurring computation or data transformation.

## Proposal Review

For each publication, present:

- Citation and identifiers.
- Selected candidate skill name.
- Alternate candidate skills when useful.
- What each skill would do.
- Why it is reusable.
- Evidence from the paper.
- Expected inputs and outputs.
- Proposed helper scripts, when any, including what raw data they parse or fetch.
- Data/code availability.
- Repository files inspected or repository access limitations.
- Existing-skill search result.
- Limitations.

The user must approve or decline each proposal before scaffolding.

## Publishing Workflow

Generated skills belong under `generated-skills/`. Published skills should be listed in `published-skills.md` with links to the skill folder and approval provenance.

When the user asks to prepare or publish generated skills, use `scripts/prepare_published_skills.py` to stage generated skill files and `published-skills.md` on the current branch. Do not create or switch branches unless the user explicitly asks.
