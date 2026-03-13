# Getting Started

This is the canonical first-run path for a fresh clone of the public pipeline repo.

## 1. Install prerequisites

- Python 3.10+
- internet access for `yt-dlp`

`yt-dlp` is installed as a Python dependency for this package. You do not need to install it separately unless you want to override it.

## 2. Clone the repo

```bash
git clone https://github.com/Mathewweiss02/youtube-transcript-pipeline.git
cd youtube-transcript-pipeline
```

## 3. Run the bootstrap script

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

macOS / Linux:

```bash
bash ./bootstrap.sh
```

The bootstrap script:

- creates a local `.venv`
- upgrades `pip` inside that environment
- installs the repo in editable mode
- runs `yt-pipeline-doctor --create-dirs --verify-examples`

## 4. Activate the virtual environment

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

## 5. Download transcripts for a channel

```bash
yt-pipeline-download --channel-url https://www.youtube.com/@ChannelHandle
```

That writes raw transcript markdown files into a `_Raw` folder under the active workspace.

## 6. Download and rebuild merged PART files

```bash
yt-pipeline-download --channel-url https://www.youtube.com/@ChannelHandle --sync-chunks
```

This does both:

- download raw transcripts
- rebuild merged PART files from the raw folder

## 7. Other common commands

Normalize a legacy raw folder:

```bash
yt-pipeline-normalize --input-dir transcripts/Some_Channel_Raw
```

Audit collection health:

```bash
yt-pipeline-audit
```

Scan collections against live channels:

```bash
yt-pipeline-scan
```

Update append-safe collections from the pending scan results:

```bash
yt-pipeline-update
```

## 8. Workspace control

By default:

- a source checkout uses the repo itself as the workspace
- an installed environment outside a checkout uses a user-writable app data directory

Override that with either:

- `--workspace /path/to/workspace`
- `YTP_WORKSPACE=/path/to/workspace`

## 9. Optional vector/embedding extras

If you want the OpenAI / Pinecone parts of the broader pipeline:

```bash
python -m pip install -e .[vector]
```

Then configure values from `.env.example`.
