# YouTube Transcript Pipeline

![CI](https://github.com/Mathewweiss02/youtube-transcript-pipeline/actions/workflows/ci.yml/badge.svg)

This repository packages the reusable transcript pipeline from the larger workspace as an installable CLI.

It covers the core local workflow:

- download YouTube transcripts in parallel
- normalize legacy raw transcript folders
- rebuild merged PART files
- scan collection coverage against live channels
- update append-safe collections from pending scan results
- audit transcript/archive health

## Quickstart

Clone the repo, then use the bootstrap script for your platform.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

macOS / Linux:

```bash
bash ./bootstrap.sh
```

That installs the package in editable mode and runs `yt-pipeline-doctor`.

Then activate the local virtual environment:

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

After that, the main end-to-end command is:

```bash
yt-pipeline-download --channel-url https://www.youtube.com/@ChannelHandle --sync-chunks
```

## Installed Commands

- `yt-pipeline-download`
- `yt-pipeline-chunk`
- `yt-pipeline-normalize`
- `yt-pipeline-scan`
- `yt-pipeline-update`
- `yt-pipeline-audit`
- `yt-pipeline-doctor`

## Workspace Behavior

The CLI no longer depends on being launched from the repo root.

- In a source checkout, commands default to the repo itself as the active workspace.
- In an installed environment outside a checkout, commands default to a user-writable app data directory.
- Override that location with `--workspace /path/to/workspace` or the `YTP_WORKSPACE` environment variable.

The workspace is where transcript data, reports, and pending-update files are written.

## Manual Install

If you do not want to use the bootstrap scripts:

```bash
python -m venv .venv
python -m pip install -e .
python -m yt_processor.pipeline_doctor --create-dirs --verify-examples
```

Optional vector/embedding extras:

```bash
python -m pip install -e .[vector]
```

## Safe Example Data

The repo ships tiny synthetic examples in:

- `examples/sample_raw/`
- `examples/sample_chunked/`
- `yt_processor/examples/`

They are safe to publish and are used by the doctor smoke check.

## Repo Scope

This public repo intentionally includes:

- the reusable `yt_processor/` pipeline
- collection metadata and curated overrides
- tests, examples, bootstrap scripts, and setup docs

It intentionally excludes:

- the full transcript corpus
- the legacy `Howdy/` dump
- local frontend state and app build artifacts
- scratch scripts, inventories, and generated local research outputs

## Additional Docs

- `GETTING_STARTED.md`
- `CHANGELOG.md`
- `PUBLIC_RELEASE_RISK_ASSESSMENT.md`
- `.env.example`

The transcript corpus is intentionally split into a separate private archive repo because of size and content-distribution risk.
