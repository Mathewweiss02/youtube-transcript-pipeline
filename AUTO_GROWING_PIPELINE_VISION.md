# Auto-Growing YouTube Transcript Pipeline - Architecture Vision

## Overview
A self-evolving, automated system that continuously discovers, transcribes, embeds, and adds new YouTube channels and videos to the YouTube Wiki app without manual intervention.

---

## Core Components

### 1. Channel Discovery Engine
**Purpose:** Automatically identify new YouTube channels to add to the system

**Implementation:**
- Algorithmic recommendation engine based on:
  - Existing channel similarities (topic matching)
  - Trending channels in relevant niches (health, fitness, AI, etc.)
  - User viewing patterns and interests
  - Related channels from current channel networks
- Outputs: List of candidate channel handles/URLs for transcription

### 2. New Video Detection Service
**Purpose:** Monitor existing channels for new uploads

**Implementation:**
- Runs on cloud infrastructure (cron job or scheduled function)
- Executes 2-4x per day
- Uses existing `transcript_scanner.py` logic:
  - Scans YouTube channel via yt-dlp
  - Compares against existing transcript database
  - Identifies new videos not yet processed
- Outputs: `pending_updates.json` with new video IDs per channel

### 3. Universal Transcript Pipeline
**Purpose:** Download, clean, and merge transcripts

**Implementation:**
- Parallel Python processing (10+ workers)
- Downloads VTT transcripts via yt-dlp
- Cleans formatting, timestamps
- Merges into existing consolidated files
- Enforces NotebookLM limits:
  - Max 2.5MB per merged file
  - Natural boundary chunking (per-video splits)
- Outputs: Updated `*_CONSOLIDATED_PART_XX.md` files

### 4. Cost-Aware Embedding System
**Purpose:** Track and control Pinecone embedding costs

**Implementation:**
**Pre-Embedding Cost Calculator:**
- Analyze merged transcript files before embedding
- Calculate:
  - Total word count
  - Estimated token count (OpenAI tokenizer)
  - Estimated cost per channel/video
  - Running monthly cost tracker

**Cost Guardrails:**
- Daily/weekly embedding budget caps
- Cost threshold alerts (e.g., warn at $50, stop at $100)
- Priority queue system (channels ranked by importance)
- Cost dashboard showing:
  - Current month spend
  - Projected spend based on pending transcripts
  - Per-channel embedding costs
  - Cost per 1000 videos

**Auto-Embed Controller:**
- Only proceeds if cost is within budget
- Batches embedding jobs for efficiency
- Tracks successful vs failed embeddings

### 5. Pinecone Vector Database Integration
**Purpose:** Store and search transcript embeddings

**Implementation:**
- Automatic index creation per channel
- Metadata storage (video ID, title, URL, timestamp, topics)
- Namespace organization by channel
- Hybrid search capabilities (semantic + keyword)
- Automatic upserts for new video chunks

### 6. Database Layer (Supabase)
**Purpose:** Persistent storage for pipeline state and metadata

**Tables:**
- `channels` - Channel registry with status
- `videos` - Video metadata and transcript status
- `transcript_chunks` - Chunk tracking and embedding status
- `embedding_jobs` - Queue and history of embedding operations
- `cost_tracking` - Daily cost logs and budgets
- `pipeline_logs` - Audit trail of all operations

**Purpose:** Production-ready deployment infrastructure

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHANNEL DISCOVERY                            │
│  (Algorithmic recommendations + Trending analysis)               │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              NEW VIDEO DETECTION SERVICE                          │
│  (Runs 2-4x daily, scans all channels, finds new uploads)      │
└───────────────────────┬─────────────────────────────────────────┘
                        │ pending_updates.json
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              UNIVERSAL TRANSCRIPT PIPELINE                        │
│  (Parallel download → Clean → Merge → Chunk)                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │ Merged transcript files
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              COST-AWARE EMBEDDING SYSTEM                        │
│  (Calculate cost → Check budget → Queue or Alert)              │
└───────────────────────┬─────────────────────────────────────────┘
                        │ Within budget?
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              PINECONE VECTOR DATABASE                             │
│  (Store embeddings, enable semantic search)                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              YOUTUBE WIKI APP (NEXT.JS)                           │
│  (Search, Chat, Episodes - Real-time API integration)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Tracking Requirements

### Embedding Cost Formula
```
Cost = (Total Tokens / 1,000) × Price per 1K tokens

Token Estimation:
- 1 word ≈ 1.3 tokens (OpenAI average)
- 1000 words ≈ 1300 tokens

Example:
- 500K words = ~650K tokens
- At $0.0001 per 1K tokens = $0.065 per video
- 1000 videos = ~$65
```

### Cost Tracking Dashboard
- **Real-time spend tracking**
- **Per-channel cost breakdown**
- **Monthly budget vs actual**
- **Projection calculator:** "If you add X more channels, estimated cost is $Y"
- **Alert thresholds:**
  - 50% of budget → Warning notification
  - 80% of budget → Urgent alert
  - 100% of budget → Auto-pause new embeddings

---

## Implementation Phases

### Phase 1: Foundation (Current)
- ✅ API routes with Zod validation
- ✅ Error boundaries, search, chat UI
- ✅ Basic episode pagination
- ✅ 16 channels mapped
- 🔄 API key integration pending

### Phase 2: Cost Tracking System
- [ ] Build cost calculator utility
- [ ] Create cost tracking database schema (Supabase)
- [ ] Implement pre-embedding cost analysis
- [ ] Build cost dashboard UI
- [ ] Set up budget alerts/notifications

### Phase 3: Auto-Video Pipeline
- [ ] Deploy transcript scanner to cloud (cron job)
- [ ] Integrate scanner with existing `transcript_scanner.py`
- [ ] Auto-merge new transcripts into consolidated files
- [ ] Trigger embedding jobs automatically
- [ ] Update app with new episodes in real-time

### Phase 4: Channel Discovery Engine
- [ ] Build recommendation algorithm
- [ ] Implement channel similarity scoring
- [ ] Create channel approval queue (manual override option)
- [ ] Full channel transcription pipeline (from scratch)

### Phase 5: Production Deployment
- [ ] Supabase database setup
- [ ] Pinecone production index configuration
- [ ] Vercel deployment with environment variables
- [ ] Monitoring and logging infrastructure
- [ ] Backup and disaster recovery

---

## Key Files to Create/Update

### New Files
```
lib/
  cost-tracker.ts         # Cost calculation utilities
  pinecone-client.ts      # Pinecone API integration
  
components/
  cost-dashboard.tsx      # Cost tracking UI
  
app/
  api/
    admin/
      cost-report/route.ts    # Cost reporting API
      embed-trigger/route.ts  # Manual embedding trigger
      
scripts/
  auto-embed.ts           # Cloud function for auto-embedding
  cost-analyzer.ts        # Pre-embedding cost analysis
  
supabase/
  schema.sql              # Database schema
  migrations/             # Database migrations
```

### Updated Files
```
lib/episodes.ts         # Add embedding status tracking
app/channel/[channel]/page.tsx  # Show embedding status
```

---

## Budget Safety Mechanisms

### Hard Limits
- **Daily embedding cap:** Max $X per day
- **Monthly budget ceiling:** Auto-stop at $Y
- **Per-channel cost threshold:** Skip if channel > $Z to embed

### Soft Warnings
- **Slack/Email alerts** at 50%, 80%, 95% of budget
- **Weekly cost reports** with projections
- **Cost-per-channel analysis** to identify expensive channels

### Manual Overrides
- Admin dashboard to approve expensive channels
- Emergency bypass for critical content
- Cost override with justification logging

---

## Success Metrics

- **Zero surprise bills** - All costs predicted before incurred
- **100% automated** - New videos appear in app within 24 hours of upload
- **Scalable** - Can handle 10→100→1000 channels without architecture changes
- **Cost-efficient** - Always know spend before committing
- **Self-healing** - Pipeline retries failures, alerts on persistent issues

---

## Notes

- Keep NotebookLM chunking limits (2.5MB) enforced in pipeline
- All channels from memory system already mapped (16 total)
- YouTube Shorts filtering must be enforced at download stage
- Use parallel processing for transcript downloads (10 workers)
- Store channel handles (@handle) for avatar fetching via YouTube API later
