# Project Context: Publication-to-Skill Builder

## Skill Concept

This project will define a Codex skill that helps build new skills from scientific publications available through public-domain or openly accessible sources such as Europe PMC, PubMed, PubMed Central, and user-provided PDFs.

The skill is intended to identify computational research methods embedded in scientific papers, especially in methods sections, and turn reusable techniques into practical Codex skills for scientists, analysts, bioinformaticians, and computational biologists.

## Why This Is Needed

Many valuable scientific computational workflows are hidden in plain-text methods sections of publications. These methods are often written to answer a specific biological question, but they may contain reusable analytical techniques that could serve a broader audience.

Examples include:

- Statistical techniques for comparing patient cohorts.
- Bioinformatics workflows for processing omics data.
- Scientific plotting methods for complex biological datasets.
- Data analysis procedures that could be generalized beyond one paper.
- Reproducible computational protocols that are described in prose but not packaged as reusable tools.

Scientists and analysts often find interesting papers but may not know how to translate the embedded method into code, an analysis workflow, or a reusable Codex skill. This project aims to make that translation scalable.

The long-term goal is to build a repository of skills that scans scientific papers, identifies reusable computational techniques, checks whether equivalent skills already exist, and creates new skills only when they add meaningful value.

## Primary Users

The main users are:

- Bioinformaticians.
- Computational biologists.
- Biomedical data scientists.
- Wet-lab scientists who need computational analysis support.
- Analysts who want to reproduce or adapt methods from scientific publications.
- Researchers maintaining personal or shared Codex skill repositories.

## What The Skill Will Do

The Publication-to-Skill Builder will support the following workflow:

1. Accept one or more scientific publications from the user.
2. Support both individual and bulk publication inputs.
3. Enforce a maximum of 10 publications per run.
4. Fetch paper metadata from public sources such as Europe PMC, PubMed, PubMed Central, Crossref, or publisher landing pages where appropriate.
5. Attempt to fetch full text or PDF versions of the papers when legally and openly available.
6. Flag publications where the full text or PDF is unavailable.
7. Parse user-provided PDFs when supplied.
8. Extract methods sections and related computational details from available full text.
9. Analyze the methods to identify reusable computational techniques.
10. Propose one or more candidate skills that would be useful to a bioinformatician or computational biologist.
11. Check whether the proposed skill already exists in the open-source repository at `https://github.com/K-Dense-AI/scientific-agent-skills`.
12. If a matching skill already exists, point the user to that skill instead of recreating it.
13. If no equivalent skill exists, prepare a proposed skill specification for user approval.
14. Ask the user to approve or decline the proposed skill for each publication.
15. Record the user's approval or decline decision.
16. If approved, create the skill.
17. If declined, ask the user what they would have preferred to use as a skill.
18. Store the user's feedback with complete provenance and the original proposal.
19. Only implement declined-feedback ideas later if the user explicitly asks for that feedback to be implemented.
20. Push created skills to the user's personal GitHub skill repository when requested.

## Inputs

The skill should accept:

- PubMed IDs.
- PMC IDs.
- DOIs.
- Europe PMC links.
- PubMed links.
- Publisher links.
- Direct open-access PDF URLs.
- Locally supplied PDF files.
- Bulk lists containing up to 10 publications.

The skill must reject or pause on inputs containing more than 10 publications and ask the user to split the request into batches.

## PDF And Full-Text Handling

The skill should attempt to retrieve openly available full text and PDFs through appropriate public sources.

If a PDF is available, the skill should download or read it and parse it using tools such as PyMuPDF.

If a user supplies PDFs directly, the skill should parse those PDFs locally.

The parser should extract:

- Title.
- Authors.
- Journal.
- Publication date.
- DOI.
- PMID.
- PMCID.
- Abstract.
- Methods section.
- Supplementary method references when available.
- Data availability statements.
- Code availability statements.
- GitHub or repository links mentioned in the paper.
- Software packages, libraries, pipelines, and statistical methods mentioned in the methods.

If full text or methods cannot be extracted, the skill should clearly flag the limitation and avoid inventing methodological details.

## Candidate Skill Discovery

After parsing the paper, the skill should identify computational methods that could become reusable Codex skills.

Candidate skill types may include:

- Statistical testing workflows.
- Cohort comparison workflows.
- Data preprocessing pipelines.
- Bioinformatics analysis workflows.
- Scientific visualization generators.
- Reproducible plotting templates.
- Model evaluation procedures.
- Omics-specific analysis patterns.
- Quality-control procedures.
- Public-dataset retrieval and harmonization workflows.

For each proposed skill, the agent should explain:

- What the skill would do.
- Which part of the paper supports the proposal.
- Why the method is reusable beyond the original paper.
- Who would use it.
- What inputs it would require.
- What outputs it would produce.
- Whether code or data from the paper is available.
- Any limitations or assumptions.

## Existing Skill Check

Before creating a new skill, the system must check the open-source skill repository:

`https://github.com/K-Dense-AI/scientific-agent-skills`

The check should determine whether:

- An identical skill already exists.
- A substantially similar skill already exists.
- An existing skill could be extended instead of creating a new one.
- The proposed skill is genuinely novel enough to create.

If an existing skill is found, the user should be given a direct link to it and a short explanation of why it matches.

## User Approval Workflow

The skill must ask for approval before creating a new skill.

Approval must happen for each publication, not only once for the whole batch.

For each publication, the skill should show the user:

- The paper citation and identifier.
- The extracted or inferred computational method.
- The proposed skill name.
- The proposed skill purpose.
- Why the skill would be useful.
- Evidence from the paper.
- Whether similar skills already exist.
- The expected inputs and outputs.
- Any implementation caveats.

The user must then approve or decline.

If the user approves, the skill may create the new skill.

If the user declines, the skill must ask what the user would have preferred to use as a skill instead.

Declined proposals and user feedback must be stored. The system must not implement declined feedback unless the user later explicitly asks it to do so.

## Feedback And Provenance Logging

Every proposal should be logged, whether approved or declined.

The log should include:

- Complete paper metadata.
- Abstract.
- Extracted methods text or method summary.
- Available data information.
- Available code information.
- GitHub or repository links from the paper.
- Proposed skill name.
- Proposed skill description.
- Evidence supporting the proposal.
- Existing-skill search results.
- User approval decision.
- User feedback when declined.
- Timestamp of the decision.
- Tool versions or parser versions where relevant.
- Source URLs and identifiers used during retrieval.

The metadata may be stored as JSON or CSV. JSON is preferred for nested provenance, with CSV export as an optional convenience.

## Repository And Branch Workflow

The user will clone this repository and use it to create their own skills.

This Publication-to-Skill Builder should live in the parent repository.

Skills created by this system should be published on the current repository branch unless the user explicitly asks to use another branch.

The expected repository flow is:

1. User clones their personal `skills-lab` repository.
2. User runs the Publication-to-Skill Builder skill.
3. The skill analyzes papers and proposes candidate skills.
4. The user approves selected skills.
5. Approved skills are generated locally.
6. Generated skills and metadata are committed or prepared for commit.
7. When requested, the generated skills are committed or pushed to the user's GitHub repository from the current branch.

The system should not assume it has permission to push to GitHub unless the user explicitly requests it and the repository is configured for GitHub access.

## Constraints

- Do not accept more than 10 publications in a single run.
- Ask the user to remove publications or run the skill in batches if more than 10 are supplied.
- Do not create a skill until the user approves the proposed skill.
- Ask for approval separately for each publication.
- Record every approval and decline decision.
- If the user declines a proposed skill, ask what they would have preferred instead.
- Store declined feedback with complete provenance.
- Do not implement feedback unless the user explicitly requests implementation later.
- Check the existing open-source skill repository before creating a new skill.
- Point users to existing skills instead of recreating them.
- Flag unavailable full text or PDFs clearly.
- Do not infer methods that are not supported by the paper text.
- Preserve paper provenance and extraction details for every generated skill.

## Suggested Implementation Components

The skill may eventually include scripts or modules for:

- Publication identifier normalization.
- PubMed and Europe PMC metadata retrieval.
- Open-access full-text discovery.
- PDF download and availability checks.
- PDF parsing with PyMuPDF.
- Methods-section extraction.
- Data and code availability extraction.
- Repository-link detection.
- Candidate skill proposal generation.
- Existing-skill search against `scientific-agent-skills`.
- User approval capture.
- Provenance logging.
- Skill scaffolding.
- Git staging and commit preparation on the current branch.
- Optional GitHub push support.

## Desired Outcome

The desired outcome is a scalable system for converting useful computational methods from scientific literature into reusable Codex skills, while preserving scientific provenance, avoiding duplicate work, and keeping the human researcher in control of what gets created.
