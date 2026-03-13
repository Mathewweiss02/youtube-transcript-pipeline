# YouTube Transcript Pipeline

This folder now has two distinct layers:

1. `universal_parallel_downloader.py` and `universal_chunker.py`
   - These remain the fast generic download/chunk tools.
   - They are unchanged by the provenance refactor.
2. The collection-first scan/audit/provenance pipeline
   - This is the authoritative metadata layer for deciding what a transcript collection actually contains.
   - It exists to stop mixed bundles from being treated as if they were simple single-channel archives.

## Core Files

### Universal download/chunk flow

- `universal_parallel_downloader.py`
- `universal_chunker.py`

These are still the preferred tools for raw download and chunk creation.

### Collection-first pipeline

- `collection_registry.json`
  - Authoritative registry for transcript collections.
  - Collections are explicitly typed as:
    - `single_channel_appendable`
    - `single_channel_curated`
    - `multi_channel_curated`
    - `legacy_mixed_format`
    - `manual_only`
- `collection_utils.py`
  - Shared helpers for registry loading, title normalization, yt-dlp inventory fetches, markdown candidate extraction, bundle classification, and manifest helpers.
- `build_collection_provenance.py`
  - Builds per-collection provenance manifests from local transcript bundles plus live source inventories and curated overrides.
- `transcript_scanner.py`
  - Scans collections according to `scan_strategy`.
  - Uses inline URLs for append-safe archives.
  - Uses manifests for curated or mixed collections.
- `transcript_updater.py`
  - Only updates collections that are explicitly append-safe.
  - Refuses manual, curated, and mixed collections.
- `audit_transcript_collections.py`
  - Produces a read-only architecture/risk audit of the transcript corpus.

## Metadata Directories

- `provenance_manifests/`
  - Generated machine-readable manifests.
  - One JSON file per collection.
- `provenance_overrides/`
  - Curated per-collection overrides for ignored files, ignored titles, bundle roles, and known provenance corrections.
- `reports/`
  - Generated audit reports.

## Registry Model

`collection_registry.json` is now the source of truth for scan/update behavior.

Each collection record can declare:

- `collection_type`
- `transcript_dir`
- `raw_dir`
- `scan_strategy`
  - `inline_urls`
  - `manifest`
  - `manual`
- `update_strategy`
  - `append`
  - `disabled`
- `primary_channel`
- `source_channels`
- `canonical_sources`
- `provenance_manifest`
- optional sidecar bootstrap fields such as `legacy_sidecar_slug`

`channel_registry.json` is retained only for legacy compatibility during migration.

## Provenance Manifest Model

Each manifest records:

- collection identity and type
- source channels
- bundle files with file hashes, sizes, and bundle roles
- per-video entries
- unresolved titles
- duplicate groups
- summary stats

This is what makes mixed or overlapping bundles reverse-traceable.

If the same video appears in both a canonical archive chunk and a curated topic bundle, the manifest keeps both bundle references while the scanner counts that video once for source coverage.

## Scanner Behavior

### Append-safe collections

Collections with:

- `collection_type = single_channel_appendable`
- `scan_strategy = inline_urls`
- `update_strategy = append`

are scanned directly from canonical transcript chunks.

Inline URL and video ID extraction is the primary truth. Title fallback is only used when a chunk does not contain an inline URL for a candidate.

### Manifest collections

Collections with `scan_strategy = manifest` are not trusted through raw markdown parsing alone.

The scanner reads their generated manifest and compares manifest coverage against live source inventories. This is required for collections such as:

- `Solar_Athlete`
- `Alex_Kikel`
- `Professor_Jiang`
- `Huberman`
- `Alchemical_Science`
- `MuayThaiPros`

### Manual collections

Collections with `scan_strategy = manual` are still visible in scans and audits, but they are not eligible for generic updating.

## Pending Output

`pending_updates.json` is now collection-oriented:

- `pending_updates.json["collections"][collection_key]`

Each collection result includes:

- `collection_type`
- `scan_strategy`
- `scan_mode_used`
- `source_channels`
- `total_on_sources`
- `total_indexed`
- `new_count`
- `new_videos`
- `unresolved_count`
- `confidence_summary`
- `source_summaries`
- `scan_notes`

A legacy-compatible `channels` section is still emitted for append-safe single-channel collections.

## Updater Guardrails

`transcript_updater.py` will only append when both conditions are true:

- `collection_type == single_channel_appendable`
- `update_strategy == append`

All curated, mixed, legacy, and manual collections are explicitly refused.

This protects transcript bundles like `Solar_Athlete`, `Huberman`, and `Professor_Jiang` from being mutated by the generic updater.

## Typical Commands

Run from the repo root.

### Build manifests

```bash
python yt_processor/build_collection_provenance.py
```

Build manifests for specific collections:

```bash
python yt_processor/build_collection_provenance.py Solar_Athlete Alex_Kikel Professor_Jiang Huberman
```

### Run the architecture audit

```bash
python yt_processor/audit_transcript_collections.py
```

### Rebuild pending scan state

```bash
python yt_processor/transcript_scanner.py
```

Print the current scan report without rescanning:

```bash
python yt_processor/transcript_scanner.py --report
```

### Validate updater eligibility without writing

```bash
python yt_processor/transcript_updater.py --dry-run
```

Dry-run specific collections:

```bash
python yt_processor/transcript_updater.py Combat_Athlete_Physio Walter_Russell --dry-run
```

## Audit Output

`audit_transcript_collections.py` writes:

- `reports/collection_audit.json`
- `reports/collection_audit.md`

The audit is intended to surface:

- registry drift
- mixed or legacy collection structure
- oversized transcript bundles
- duplicate video IDs and normalized titles
- collections blocked from generic updates
- low-confidence scan findings
- manifest gaps for high-risk collections

## Testing

Run the collection pipeline unit tests with:

```bash
python -m unittest discover -s yt_processor/tests -v
```

These tests cover title normalization, malformed markdown candidate extraction, duplicate deduping, registry expectations, and scanner mode selection.
