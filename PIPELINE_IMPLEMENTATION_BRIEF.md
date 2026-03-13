# PIPELINE IMPLEMENTATION BRIEF
## For Code Agent: Self-Evolving YouTube Transcript & Embedding System

---

## WHAT YOU ARE BUILDING

A self-evolving, automated pipeline that:
1. Monitors YouTube channels for new videos
2. Downloads + cleans transcripts automatically
3. Merges them into chunked consolidated files
4. Calculates embedding costs BEFORE spending money
5. Embeds into Pinecone vector DB with budget guardrails
6. Connects to a Next.js wiki app (already built) so new content appears automatically
7. Eventually: auto-discovers new channels algorithmically

---

## REPO STRUCTURE (WHAT ALREADY EXISTS)

```
c:\Users\aweis\Downloads\YouTube_Tools_Scripts\
├── transcripts/                          # All consolidated transcript chunks
│   ├── Mark_Bell/                        # 44 PART files (~500+ videos)
│   ├── Mark_Bell_Raw/                    # Individual raw .md per video
│   ├── Jay_Campbell/                     # 18 PART files
│   ├── Ken_Wheeler/                      # 8 PART files (1384 raw files!)
│   ├── Hyperarch_Fascia/                 # 6 PART files
│   ├── Alchemical_Science/               # 4 PART files
│   ├── Alex_Kikel/                       # 9 PART files
│   ├── Daru_Strong/                      # 8 PART files
│   ├── Coach_Micah_B/                    # 2 PART files
│   ├── Combat_Athlete_Physio/            # 2 PART files
│   ├── CIA_INTEL_Chunked/                # 6 PART files
│   ├── Scotty_Optimal/                   # 1 PART file
│   ├── Professor_Jiang/                  # 4 PART files
│   ├── Warrior_Collective/               # 7 PART files
│   ├── Solar_Athlete/                    # 9 PART files
│   ├── Huberman/                         # 20 PART files
│   ├── n8n/                              # 3 PART files
│   └── [Channel]_Raw/                    # Raw individual .md files per channel
│
├── yt_processor/                         # ALL PYTHON SCRIPTS LIVE HERE
│   ├── channel_registry.json             # MASTER channel config (handles, dirs, patterns)
│   ├── pending_updates.json              # Output of scanner (new videos to download)
│   ├── transcript_scanner.py             # Scans channels, finds new videos
│   ├── transcript_updater.py             # Downloads new transcripts, appends to chunks
│   ├── universal_parallel_downloader.py  # Downloads transcripts (10 workers)
│   ├── universal_chunker.py              # Chunks raw .md files into PART files
│   ├── wiki_pipeline.py                  # End-to-end: transcripts -> embeddings -> Pinecone
│   ├── wiki_chunker.py                   # Splits transcripts into vector search chunks
│   ├── embedding_generator.py            # OpenAI text-embedding-3-small wrapper
│   ├── pinecone_manager.py               # Pinecone upsert/query/delete manager
│   ├── topic_extractor.py                # Extracts topics from transcripts
│   └── guest_extractor.py                # Extracts guest names from transcripts
│
├── youtuber wiki apps/my-app/            # NEXT.JS APP (already built)
│   ├── app/
│   │   ├── page.tsx                      # Homepage - shows all 16 channel cards
│   │   ├── channel/[channel]/page.tsx    # Channel page with episodes + pagination
│   │   ├── channel/[channel]/chat/page.tsx
│   │   ├── channel/[channel]/episode/[episodeId]/page.tsx
│   │   ├── api/[channel]/search/route.ts # POST /api/{channel}/search (Zod validated)
│   │   └── api/[channel]/chat/route.ts   # POST /api/{channel}/chat (streaming)
│   ├── lib/
│   │   ├── episodes.ts                   # Parses transcript PART files -> Episode objects
│   │   └── channels.ts                   # Reads channel-registry.json -> Channel objects
│   ├── components/
│   │   ├── youtube-embed.tsx             # YouTubeEmbed + EpisodeCard components
│   │   ├── paginated-episodes.tsx        # Load More pagination (30 at a time)
│   │   └── search-bar.tsx                # Client-side search component
│   └── data/
│       └── channel-registry.json         # 16 channels with slugs, colors, handles
```

---

## EXISTING SCRIPTS - HOW THEY WORK

### 1. `yt_processor/transcript_scanner.py`
**Purpose:** Finds new videos on YouTube not yet transcribed

**How it runs:**
```bash
python transcript_scanner.py                  # Scan ALL channels
python transcript_scanner.py Mark_Bell        # Single channel
python transcript_scanner.py --report         # Show last results
```

**What it does:**
- Reads `channel_registry.json` for channel URLs and transcript dirs
- Uses `yt-dlp --flat-playlist --dump-single-json` to get all video IDs from channel
- Scans existing PART files for `URL: https://youtube.com/watch?v=VIDEO_ID` lines
- Diffs: YouTube videos - already transcribed = new videos needed
- **Filters YouTube Shorts** (duration ≤ 60s or `/shorts/` in URL) - NEVER download shorts
- Writes results to `pending_updates.json`
- Supports legacy title-based matching for channels without URL lines (Jay_Campbell, Alex_Kikel, Solar_Athlete)

**yt-dlp discovery order:**
1. `C:/yt-dlp/yt-dlp*.exe`
2. Python Scripts dir (`Scripts/yt-dlp.exe`)
3. WinGet packages (`%LOCALAPPDATA%\Microsoft\WinGet\Packages`)
4. `YT_DLP_PATH` env var
5. PATH fallback

---

### 2. `yt_processor/transcript_updater.py`
**Purpose:** Downloads transcripts for pending videos and appends to chunk files

**How it runs:**
```bash
python transcript_updater.py                  # Update ALL channels
python transcript_updater.py Mark_Bell        # Single channel
python transcript_updater.py --dry-run        # Preview only
```

**What it does:**
- Reads `pending_updates.json` (output from scanner)
- For each new video: downloads VTT subtitle with yt-dlp, cleans it, saves as .md
- Raw .md format:
  ```
  # Video Title
  URL: https://www.youtube.com/watch?v=VIDEO_ID
  ---
  [cleaned transcript text]
  ```
- Appends to last PART file OR creates new PART file if last one would exceed **2.4MB**
- Uses **10 parallel workers** (ThreadPoolExecutor)
- After processing, removes completed videos from `pending_updates.json`

**Chunk file naming pattern:**
```
MARK_BELL_PART_01.md, MARK_BELL_PART_02.md, ...
Jay_Campbell_CONSOLIDATED_PART_01.md, ...
HYPERARCH_FASCIA_PART_01.md, ...
```

---

### 3. `yt_processor/universal_parallel_downloader.py`
**Purpose:** Bulk download transcripts from a video list file (for new channels)

**Input format** (`title<TAB>url`):
```
My Video Title	https://www.youtube.com/watch?v=abc123
Another Video	https://www.youtube.com/watch?v=xyz789
```

**What it does:**
- Reads input file, filters Shorts, downloads VTT for each video
- Cleans VTT: removes timestamps, WEBVTT headers, `[Music]`, duplicate lines
- Saves each video as `{VIDEO_ID}.md` in output dir
- 10 parallel workers, retries on failure

---

### 4. `yt_processor/universal_chunker.py`
**Purpose:** Merges individual raw .md files into NotebookLM-compliant PART files

**What it does:**
- Reads all `.md` files from `_Raw` directory
- Parses title, URL, transcript from each
- Groups into chunks ≤ 2.4MB (NotebookLM limit is 2.5MB)
- Writes PART files with Table of Contents header
- Each PART file format:
  ```markdown
  # CHANNEL_NAME - Part 01
  ## Table of Contents
  1. Video Title One
  2. Video Title Two
  ...
  ================================================================================
  
  # Video Title One
  URL: https://www.youtube.com/watch?v=abc123
  ---
  [transcript text]
  
  ---
  
  # Video Title Two
  ...
  ```

---

### 5. `yt_processor/wiki_chunker.py`
**Purpose:** Splits transcripts into vector search chunks for Pinecone

**Settings:**
- Chunk size: **1000 tokens**
- Chunk overlap: **200 tokens**
- Tokenizer: `tiktoken` with `cl100k_base` (OpenAI tokenizer)

**Chunk output format:**
```python
{
  'id': 'VIDEO_ID_chunk_0',
  'text': '...chunk text...',
  'metadata': {
    'video_id': 'abc123',
    'title': 'Video Title',
    'url': 'https://youtube.com/watch?v=abc123',
    'channel': 'Mark_Bell',
    'chunk_index': 0,
    'total_chunks': 12,
    'start_timestamp': 120  # estimated seconds
  }
}
```

---

### 6. `yt_processor/embedding_generator.py`
**Purpose:** Generates OpenAI embeddings for transcript chunks

**Model:** `text-embedding-3-small`
**Cost:** $0.02 per 1M tokens
**Batch size:** 100 chunks per API call
**Has retry logic:** exponential backoff, 5 attempts

**Cost estimation (built-in):**
```python
cost_per_1m = 0.02  # $0.02 per 1M tokens for text-embedding-3-small
cost = (total_tokens / 1_000_000) * cost_per_1m
```

---

### 7. `yt_processor/pinecone_manager.py`
**Purpose:** Manages Pinecone vector DB operations

**Index config:**
- Index name: `youtube-wiki` (single index, all channels)
- Dimension: 1536 (text-embedding-3-small output)
- Metric: cosine similarity
- Cloud: AWS us-east-1 (Serverless)
- **Namespaces:** one per channel (e.g., namespace `Mark_Bell`)

**Key methods:**
```python
manager.create_index()          # Creates if not exists
manager.upsert_chunks(channel, chunks_with_embeddings)  # Insert/update vectors
manager.query(channel, vector, top_k=10)                # Semantic search
manager.delete_namespace(channel)                       # Wipe a channel
manager.get_index_stats()                               # Stats
```

---

### 8. `yt_processor/channel_registry.json`
**The master config for the Python pipeline:**
```json
{
  "channels": {
    "Mark_Bell": {
      "channel_url": "https://www.youtube.com/@MarkBellsPowerProject",
      "transcript_dir": "transcripts/Mark_Bell",
      "raw_dir": "transcripts/Mark_Bell_Raw",
      "base_name": "MARK BELL",
      "chunk_pattern": "MARK_BELL_PART_*.md"
    },
    ...
  }
}
```

**All channels currently in registry:**
Mark_Bell, Huberman, Jay_Campbell, Hyperarch_Fascia, Alex_Kikel, Daru_Strong,
Coach_Micah_B, Combat_Athlete_Physio, Warrior_Collective, Solar_Athlete, n8n,
Professor_Jiang, Alchemical_Science, MuayThaiPros, Danny_Jones, Julian_Dorey, Scotty_Optimal

---

## TRANSCRIPT FILE FORMAT (CANONICAL)

Every individual raw transcript `.md` file MUST follow this exact format:
```markdown
# Video Title Here

URL: https://www.youtube.com/watch?v=VIDEO_ID

---

Cleaned transcript text here. No timestamps. No VTT headers.
No [Music] tags. No duplicate lines. Just clean spoken word text.
```

Every consolidated PART file follows:
```markdown
# CHANNEL_NAME - Part 01
## Table of Contents

1. Video Title One
2. Video Title Two
...

================================================================================

# Video Title One

URL: https://www.youtube.com/watch?v=abc123

---

Transcript text...

---

# Video Title Two
...
```

---

## THE NEXT.JS APP - HOW IT CONNECTS

### API Routes (currently mock, need real implementation)

**Search:** `POST /api/{channelSlug}/search`
```typescript
// Request body (Zod validated)
{ query: string, topK?: number }

// Response
{ results: [{ title, url, videoId, score, snippet, topics }] }
```

**Chat:** `POST /api/{channelSlug}/chat`
```typescript
// Request body (Zod validated)
{ messages: [{ role: 'user'|'assistant', content: string }] }

// Response: streaming text/plain
```

### Channel Slug → Pinecone Namespace Mapping
The app uses slugs like `mark-bell`, `jay-campbell`. Pinecone uses `Mark_Bell`, `Jay_Campbell`.
You need a mapping function:
```typescript
const slugToNamespace: Record<string, string> = {
  'mark-bell': 'Mark_Bell',
  'jay-campbell': 'Jay_Campbell',
  'ken-wheeler': 'Ken_Wheeler',
  // etc.
}
```

### Episode Loading (lib/episodes.ts)
- Reads PART files directly from `transcripts/{Channel}/` directory
- Parses `# Title`, `URL: https://...` from each section
- Returns `Episode[]` objects with videoId, title, url, topics
- Currently loads up to 500 episodes with 30-per-page pagination

---

## WHAT NEEDS TO BE BUILT

### PHASE 1: Connect Real APIs (Immediate)

**File: `youtuber wiki apps/my-app/app/api/[channel]/search/route.ts`**
Replace mock data with:
1. Get query embedding from OpenAI (`text-embedding-3-small`)
2. Query Pinecone namespace for that channel
3. Return top matches with title, url, score, snippet

**File: `youtuber wiki apps/my-app/app/api/[channel]/chat/route.ts`**
Replace mock streaming with:
1. Embed the latest user message
2. Query Pinecone for relevant context chunks
3. Build prompt: system + context + conversation history
4. Stream OpenAI `gpt-4o-mini` response back

**Environment variables needed:**
```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=youtube-wiki
```

---

### PHASE 2: Cost Tracker

**New file: `yt_processor/cost_tracker.py`**
```python
class CostTracker:
    def estimate_channel_cost(transcript_dir: Path) -> dict:
        # Read all PART files
        # Count total words, estimate tokens (words * 1.3)
        # Calculate cost at $0.02/1M tokens
        # Return { words, tokens, estimated_cost, file_count }
    
    def check_budget(estimated_cost: float, daily_budget: float) -> bool:
        # Read today's spend from cost_log.json
        # Return True if within budget
    
    def log_spend(channel: str, tokens: int, cost: float):
        # Append to cost_log.json with timestamp
    
    def get_monthly_report() -> dict:
        # Aggregate cost_log.json by month
```

**New file: `yt_processor/cost_log.json`** (auto-created, tracks all spend)

**Integration point:** Call `CostTracker.estimate_channel_cost()` BEFORE calling `embedding_generator.py`

---

### PHASE 3: Auto-Embed Trigger

**New file: `yt_processor/auto_embed.py`**
```python
# Full pipeline: scan -> download -> chunk -> cost check -> embed
def run_pipeline(channel: str, dry_run: bool = False):
    1. transcript_scanner.scan_channel(channel)
    2. transcript_updater.update_channel(channel)
    3. cost_tracker.estimate_cost(channel)
    4. if within_budget: embedding_generator + pinecone_manager
    5. log results to pipeline_log.json
```

---

### PHASE 4: Cloud Scheduler (Cron)

Deploy `auto_embed.py` to run 2-4x daily:
- **Option A:** GitHub Actions (free, cron schedule)
- **Option B:** Railway.app Python service
- **Option C:** Supabase Edge Functions + pg_cron

---

### PHASE 5: Supabase Database (Production)

**Tables needed:**
```sql
-- Channel registry (mirrors channel_registry.json)
CREATE TABLE channels (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  youtube_url text,
  handle text,
  transcript_dir text,
  pinecone_namespace text,
  last_scanned_at timestamptz,
  total_videos int DEFAULT 0,
  total_embedded int DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- Video metadata
CREATE TABLE videos (
  id text PRIMARY KEY,  -- YouTube video ID
  channel_id uuid REFERENCES channels(id),
  title text NOT NULL,
  url text NOT NULL,
  transcript_status text DEFAULT 'pending', -- pending|downloaded|chunked|embedded
  embedded_at timestamptz,
  chunk_count int,
  token_count int,
  embed_cost_usd numeric(10,6),
  created_at timestamptz DEFAULT now()
);

-- Embedding cost log
CREATE TABLE embedding_costs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id uuid REFERENCES channels(id),
  video_id text,
  tokens int NOT NULL,
  cost_usd numeric(10,6) NOT NULL,
  model text DEFAULT 'text-embedding-3-small',
  created_at timestamptz DEFAULT now()
);

-- Pipeline run log
CREATE TABLE pipeline_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id uuid REFERENCES channels(id),
  run_type text,  -- scan|download|embed|full
  status text,    -- running|success|failed
  new_videos int DEFAULT 0,
  tokens_used int DEFAULT 0,
  cost_usd numeric(10,6) DEFAULT 0,
  error text,
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz
);
```

---

## CRITICAL RULES (NEVER VIOLATE)

1. **NEVER download YouTube Shorts** — duration ≤ 60s OR `/shorts/` in URL. Always filter.
2. **NEVER exceed 2.5MB per PART file** — use 2.4MB as the safe limit in chunker
3. **ALWAYS check cost BEFORE embedding** — call cost_tracker before any OpenAI API call
4. **ALWAYS use `text-embedding-3-small`** — not ada-002, not large. Small = $0.02/1M tokens
5. **ALWAYS embed into Pinecone namespaces** — one namespace per channel (e.g., `Mark_Bell`)
6. **ALWAYS include URL line in raw .md files** — scanner uses these to detect already-transcribed videos
7. **The single Pinecone index is `youtube-wiki`** — don't create per-channel indexes

---

## EMBEDDING COST REFERENCE

| Model | Price | 1M videos est. |
|-------|-------|----------------|
| text-embedding-3-small | $0.02/1M tokens | ~$13 for 500 videos |
| text-embedding-3-large | $0.13/1M tokens | ~$84 for 500 videos |
| text-embedding-ada-002 | $0.10/1M tokens | ~$65 for 500 videos |

**USE: text-embedding-3-small**

**Rough estimate for current corpus:**
- ~500 Mark Bell videos × ~15K tokens avg = ~7.5M tokens = $0.15
- ~300 Ken Wheeler videos × ~15K tokens avg = ~4.5M tokens = $0.09
- Full corpus (~2000 videos) ≈ $0.60 total to embed everything once

---

## ENVIRONMENT SETUP

```bash
# Python dependencies (yt_processor/requirements.txt)
pip install yt-dlp openai pinecone-client tiktoken tenacity

# .env file needed at repo root
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=youtube-wiki
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# Next.js app (.env.local)
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=youtube-wiki
```

---

## NEXT IMMEDIATE STEPS (IN ORDER)

1. **Get API keys** from user (OpenAI + Pinecone)
2. **Run `wiki_pipeline.py`** on one channel (Scotty_Optimal - smallest, 1 PART file) to test embedding
3. **Verify Pinecone has data** with `pinecone_manager.get_index_stats()`
4. **Update Next.js search route** to use real Pinecone query
5. **Update Next.js chat route** to use real OpenAI streaming with RAG context
6. **Build `cost_tracker.py`** with pre-embedding estimates
7. **Test full pipeline** on Mark Bell (biggest channel)
8. **Set up cloud scheduler** for auto-updates

---

## FILE PATHS (ABSOLUTE - Windows)

```
Repo root:        C:\Users\aweis\Downloads\YouTube_Tools_Scripts\
Python scripts:   C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt_processor\
Transcripts:      C:\Users\aweis\Downloads\YouTube_Tools_Scripts\transcripts\
Next.js app:      C:\Users\aweis\Downloads\YouTube_Tools_Scripts\youtuber wiki apps\my-app\
Channel registry: C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt_processor\channel_registry.json
App registry:     C:\Users\aweis\Downloads\YouTube_Tools_Scripts\youtuber wiki apps\my-app\data\channel-registry.json
Pending updates:  C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt_processor\pending_updates.json
```

---

## SUMMARY TABLE: SCRIPT → PURPOSE → STATUS

| Script | Purpose | Status |
|--------|---------|--------|
| `transcript_scanner.py` | Find new videos | ✅ Working |
| `transcript_updater.py` | Download + append transcripts | ✅ Working |
| `universal_parallel_downloader.py` | Bulk download for new channels | ✅ Working |
| `universal_chunker.py` | Raw .md → PART files | ✅ Working |
| `wiki_chunker.py` | PART files → vector chunks | ✅ Working |
| `embedding_generator.py` | Chunks → OpenAI embeddings | ✅ Working (needs API key) |
| `pinecone_manager.py` | Embeddings → Pinecone | ✅ Working (needs API key) |
| `wiki_pipeline.py` | End-to-end orchestration | ✅ Working (needs API keys) |
| `cost_tracker.py` | Pre-embedding cost check | ❌ Needs to be built |
| `auto_embed.py` | Full auto pipeline | ❌ Needs to be built |
| Next.js search API | Real semantic search | ⚠️ Mock - needs API keys |
| Next.js chat API | Real RAG chat | ⚠️ Mock - needs API keys |
