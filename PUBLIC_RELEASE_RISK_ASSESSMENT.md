# Public Release Risk Assessment

This document summarizes what is and is not risky about publishing the current `YouTube_Tools_Scripts` workspace as a GitHub repository.

## Current Recommendation

The current GitHub repo should remain focused on the reusable pipeline and documentation.

That means:

- include `yt_processor/`
- include root docs and migration notes
- include a small synthetic example dataset
- exclude the full `transcripts/` corpus
- exclude `Howdy/`
- exclude the frontend app folder

## What Looks Safe Right Now

The current repo snapshot does **not** appear to contain live application secrets inside the published workspace files.

What was checked:

- root docs
- root scripts
- `yt_processor/`

What was found:

- placeholder environment variable examples such as `your_openai_api_key`
- code that reads environment variables like `os.getenv("OPENAI_API_KEY")`
- ordinary video titles containing words like `SECRET`, which are not credential leaks

## Main Risks If More Of The Folder Is Added

### 1. Transcript corpus publication risk

The local `transcripts/` folder is large and contains real transcript content from external channels.

Risks:

- copyright / redistribution concerns
- heavy clone size
- constant repo growth if the corpus keeps expanding

Recommendation:

- do not add the full corpus to the main pipeline repo
- if you ever want to share transcript data, use a separate repo or separate data distribution plan

### 2. Legacy dump noise

`Howdy/` looks like a legacy/special-case transcript dump rather than core pipeline code.

Recommendation:

- keep it out of the main repo unless you later decide it is an official supported source

### 3. Frontend distraction

`youtuber wiki apps/` is not necessary for the downloader/chunker pipeline story and carries extra build/dependency noise.

Recommendation:

- keep it out of the pipeline repo
- if needed later, give it its own repo

### 4. Generated artifacts and local state

Generated reports, provenance outputs, editor state, and local build artifacts are not good default repo material.

Examples:

- `yt_processor/reports/`
- `yt_processor/provenance_manifests/`
- `.windsurf/`
- `.tmp.driveupload/`

Recommendation:

- keep these ignored by default

## What The Final Version Of This Repo Should Include

For a strong public-facing pipeline repo, the final version should include:

- the downloader, chunker, scanner, updater, audit, and normalization scripts
- collection metadata and curated overrides
- root README and setup docs
- `.env.example`
- a small synthetic example dataset for demos and tests
- tests that run without access to your private corpus

## What I Would Not Add From This Workspace

I would **not** add these wholesale:

- `transcripts/`
- `Howdy/`
- `youtuber wiki apps/`

If any transcript content is added later, it should be intentional and minimal.
