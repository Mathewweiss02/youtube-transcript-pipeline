# Getting Started

This is the fastest path for a new user who wants to use the public pipeline repo.

## 1. Install prerequisites

- Python 3.11+
- a working `yt-dlp` executable

The scripts try to auto-discover `yt-dlp`, but having it on `PATH` is the easiest setup.

## 2. Bootstrap the repo

The fastest Windows path is:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

That will:

- install Python dependencies
- create the local `transcripts/` directory if needed
- run a first-run environment check

You can also run the doctor directly:

```powershell
python yt_processor\pipeline_doctor.py --create-dirs --verify-examples
```

## 3. Install Python dependencies manually

From the repo root:

```powershell
pip install -r yt_processor\requirements.txt
```

## 4. Download transcripts for a channel

```powershell
python yt_processor\universal_parallel_downloader.py --channel-url https://www.youtube.com/@ChannelHandle
```

This writes raw transcript markdown files into a `_Raw` folder under `transcripts/`.

## 5. Download and rebuild merged PART files

```powershell
python yt_processor\universal_parallel_downloader.py --channel-url https://www.youtube.com/@ChannelHandle --sync-chunks
```

This does both:

- download raw transcripts
- rebuild the merged PART files from the raw folder

## 6. Normalize an older raw folder

If a raw folder contains old title-based filenames instead of canonical video ID filenames:

```powershell
python yt_processor\normalize_raw_transcripts.py --input-dir transcripts\Some_Channel_Raw
```

## 7. Audit collection health

```powershell
python yt_processor\audit_transcript_collections.py
```

This writes:

- `yt_processor/reports/collection_audit.json`
- `yt_processor/reports/collection_audit.md`

## 8. Optional API setup

If you want embedding and downstream vector workflows, start from:

- `.env.example`

The basic downloader / chunker flow does not require API keys.
