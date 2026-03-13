# NotebookLM limits & merging guidelines

Source limits (per NotebookLM FAQ)
- Max sources per notebook: 50
- Max words per source: 500,000
- Max file size per source: 200 MB
- Notebooks per account: 100
- Daily usage (chat): 50 queries/day; audio generations: 3/day

Practical targets for this repo
- Keep each merged text/markdown source ≤ ~2.0–2.5 MB (UTF-8) to avoid edge cases and ensure fast upload.
- Prefer ≤ ~150k–200k words per source (well under the 500k cap) to keep latency low.
- If a merged file exceeds 2.5 MB, rechunk by natural boundaries (per-video or per-episode) until under target.

Chunking tips
- Split on clear separators (e.g., `===== ... Video N:`) to keep semantic boundaries.
- Preserve a short header/TOC in each chunk for navigation.
- Avoid giant single-section files; ensure the regex actually finds per-video blocks.

Recommended workflow here
1) Merge or download raw transcripts.
2) Run the appropriate chunker (e.g., `rechunk_huberman_full_v2.py`) with MAX_SIZE around 2.5 MB.
3) Verify sizes:
   ```powershell
   powershell -Command "Get-Item 'c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Transcripts/Huberman/HUBERMAN_FULL_*_CHUNK_*.md' | Select Name,@{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}}"
   ```
4) Re-run chunking if any chunk > 2.5 MB.

Why stay below the hard limits
- NotebookLM rejects oversized sources; smaller chunks upload reliably and respond faster.
- Keeping generous headroom (2–2.5 MB vs 200 MB / 500k words) prevents failures from encoding variance or hidden characters.
