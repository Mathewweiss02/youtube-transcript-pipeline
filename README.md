# YouTube Transcript Pipeline

This repository contains the reusable transcript pipeline from this workspace.

It is centered on the Python tooling in `yt_processor/` for:

- downloading YouTube transcripts in parallel
- normalizing raw transcript archives
- chunking raw transcripts into merged PART files
- scanning collections against channel inventories
- auditing transcript collections and update safety

## Included

- `yt_processor/`
- root pipeline docs and one-off migration notes
- root utility scripts such as `inject_urls.py`, `merge_transcripts.py`, and `merge_with_urls.py`

## Not Included

- the full local transcript corpus
- the legacy `Howdy/` dump
- frontend build artifacts and local app dependencies
- local secrets and editor state

## Main Entry Points

- `yt_processor/universal_parallel_downloader.py`
- `yt_processor/universal_chunker.py`
- `yt_processor/normalize_raw_transcripts.py`
- `yt_processor/transcript_scanner.py`
- `yt_processor/transcript_updater.py`
- `yt_processor/audit_transcript_collections.py`

## Release-Ready Extras

- `.env.example` for optional embedding-related environment variables
- `examples/sample_raw/` for safe raw transcript examples
- `examples/sample_chunked/` for a safe merged PART example
- `PUBLIC_RELEASE_RISK_ASSESSMENT.md` for what should and should not be added from the full workspace

## Typical Flow

Download raw transcripts for a channel:

```powershell
python yt_processor\universal_parallel_downloader.py --channel-url https://www.youtube.com/@ChannelHandle
```

Download and rebuild merged PART files:

```powershell
python yt_processor\universal_parallel_downloader.py --channel-url https://www.youtube.com/@ChannelHandle --sync-chunks
```

Normalize a legacy raw folder:

```powershell
python yt_processor\normalize_raw_transcripts.py --input-dir transcripts\Some_Channel_Raw
```

Audit collection health:

```powershell
python yt_processor\audit_transcript_collections.py
```

## Notes

This repo is set up to share the pipeline itself. The local transcript corpus is intentionally excluded because it is large and may need separate handling depending on privacy, copyright, and hosting decisions.

If you want to see the expected file shapes without using the real corpus, start with `examples/sample_raw/` and `examples/sample_chunked/`.
