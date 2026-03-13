"""
Wiki Pipeline - End-to-End Processing
Processes transcripts -> embeddings -> Pinecone.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .cost_tracker import CostTracker
    from .embedding_generator import EmbeddingGenerator
    from .guest_extractor import GuestExtractor
    from .pinecone_manager import PineconeManager
    from .topic_extractor import TopicExtractor
    from .wiki_chunker import TranscriptChunker
except ImportError:
    from cost_tracker import CostTracker
    from embedding_generator import EmbeddingGenerator
    from guest_extractor import GuestExtractor
    from pinecone_manager import PineconeManager
    from topic_extractor import TopicExtractor
    from wiki_chunker import TranscriptChunker


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
APP_GENERATED_DIR = PROJECT_ROOT / "youtuber wiki apps" / "my-app" / "data" / "generated"


def load_channel_config(channel_name: str, registry_path: str = "channel_registry.json") -> Dict[str, Any]:
    """Load channel configuration from registry."""
    registry_file = Path(registry_path)
    if not registry_file.is_absolute():
        registry_file = SCRIPT_DIR / registry_file

    with open(registry_file, "r", encoding="utf-8") as handle:
        registry = json.load(handle)

    if channel_name not in registry["channels"]:
        raise ValueError(f"Channel '{channel_name}' not found in registry")

    config = dict(registry["channels"][channel_name])
    config["transcript_dir"] = str(PROJECT_ROOT / config["transcript_dir"])
    return config


def parse_consolidated_transcript(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a consolidated transcript file (multiple videos in one file).

    Returns list of video dicts with metadata and transcript.
    """
    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    pattern = r"---\s*\n\s*#\s+(.+?)\s*\n\s*URL:\s*(https://.+?)\s*\n\s*---"
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    videos = []
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        url = match.group(2).strip()

        video_id = ""
        if "youtube.com/watch?v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]

        start_pos = match.end()
        end_pos = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        transcript = content[start_pos:end_pos].strip()

        videos.append(
            {
                "title": title,
                "url": url,
                "video_id": video_id,
                "transcript": transcript,
            }
        )

    return videos


def chunk_videos(videos: List[Dict[str, Any]], channel: str) -> List[Dict[str, Any]]:
    """Chunk all videos from consolidated files."""
    chunker = TranscriptChunker(chunk_size=1000, chunk_overlap=200)
    all_chunks = []

    for video in videos:
        if not video["transcript"]:
            continue

        video_metadata = {
            "video_id": video["video_id"],
            "title": video["title"],
            "url": video["url"],
            "channel": channel,
            "duration": len(video["transcript"]) / 20,
        }

        try:
            chunks = chunker.chunk_transcript(video["transcript"], video_metadata)
            all_chunks.extend(chunks)
            print(f"  {video['title'][:50]}... -> {len(chunks)} chunks")
        except Exception as exc:
            print(f"  Error chunking {video['title']}: {exc}")

    return all_chunks


def enrich_chunks(
    chunks: List[Dict[str, Any]],
    topic_extractor: TopicExtractor,
    guest_extractor: GuestExtractor,
) -> List[Dict[str, Any]]:
    """Add topics and guests to chunks."""
    videos: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        video_id = chunk["metadata"]["video_id"]
        if video_id not in videos:
            videos[video_id] = {
                "title": chunk["metadata"]["title"],
                "chunks": [],
            }
        videos[video_id]["chunks"].append(chunk)

    print(f"\nExtracting topics and guests for {len(videos)} videos...")

    enriched_chunks = []
    for video_data in videos.values():
        title = video_data["title"]
        preview = video_data["chunks"][0]["text"] if video_data["chunks"] else ""
        topics = topic_extractor.extract(title, preview)
        guest = guest_extractor.extract(title, preview)

        for chunk in video_data["chunks"]:
            chunk["topics"] = topics
            chunk["guest"] = guest
            enriched_chunks.append(chunk)

        guest_str = f" (guest: {guest})" if guest else ""
        print(f"  {title[:50]}... topics: {len(topics)}{guest_str}")

    return enriched_chunks


def generate_static_files(channel: str, chunks: List[Dict[str, Any]], output_dir: Path):
    """Generate static JSON files for the Next.js frontend."""
    channel_dir = output_dir / channel
    channel_dir.mkdir(parents=True, exist_ok=True)

    episodes: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        video_id = chunk["metadata"]["video_id"]
        if video_id not in episodes:
            episodes[video_id] = {
                "id": video_id,
                "title": chunk["metadata"]["title"],
                "url": chunk["metadata"]["url"],
                "channel": channel,
                "topics": chunk.get("topics", []),
                "guest": chunk.get("guest"),
                "chunk_count": 0,
                "duration_minutes": int(chunk["metadata"].get("duration", 0) / 60),
            }
        episodes[video_id]["chunk_count"] += 1

    with open(channel_dir / "episodes.json", "w", encoding="utf-8") as handle:
        json.dump(list(episodes.values()), handle, indent=2, ensure_ascii=False)

    topics: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        for topic in chunk.get("topics", []):
            if topic not in topics:
                topics[topic] = {"episodes": [], "count": 0}
            if chunk["metadata"]["video_id"] not in topics[topic]["episodes"]:
                topics[topic]["episodes"].append(chunk["metadata"]["video_id"])
                topics[topic]["count"] += 1

    topics = dict(sorted(topics.items(), key=lambda item: item[1]["count"], reverse=True))
    with open(channel_dir / "topics.json", "w", encoding="utf-8") as handle:
        json.dump(topics, handle, indent=2, ensure_ascii=False)

    guests: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        guest = chunk.get("guest")
        if not guest:
            continue
        if guest not in guests:
            guests[guest] = {"episodes": [], "count": 0}
        if chunk["metadata"]["video_id"] not in guests[guest]["episodes"]:
            guests[guest]["episodes"].append(chunk["metadata"]["video_id"])
            guests[guest]["count"] += 1

    guests = dict(sorted(guests.items(), key=lambda item: item[1]["count"], reverse=True))
    with open(channel_dir / "guests.json", "w", encoding="utf-8") as handle:
        json.dump(guests, handle, indent=2, ensure_ascii=False)

    print("\nGenerated static files:")
    print(f"  - {len(episodes)} episodes")
    print(f"  - {len(topics)} topics")
    print(f"  - {len(guests)} guests")


def process_channel(
    channel_name: str,
    skip_embeddings: bool = False,
    skip_pinecone: bool = False,
    daily_budget: Optional[float] = None,
) -> Dict[str, Any]:
    """Process an entire channel through the embedding pipeline."""
    print(f"\n{'=' * 60}")
    print(f"Processing channel: {channel_name}")
    print(f"{'=' * 60}\n")

    config = load_channel_config(channel_name)
    transcript_dir = Path(config["transcript_dir"])
    chunk_pattern = config.get("chunk_pattern", "*.md")

    transcript_files = sorted(transcript_dir.glob(chunk_pattern))
    if not transcript_files:
        transcript_files = sorted(transcript_dir.glob("*.md"))
    print(f"Found {len(transcript_files)} transcript file(s)")

    if not transcript_files:
        return {
            "channel": channel_name,
            "videos": 0,
            "chunks": 0,
            "embedded_chunks": 0,
            "estimated_cost": 0.0,
            "cost": 0.0,
            "tokens": 0,
            "status": "no_transcripts",
        }

    print("\nParsing transcripts...")
    all_videos = []
    for file_path in transcript_files:
        all_videos.extend(parse_consolidated_transcript(file_path))
    print(f"Parsed {len(all_videos)} videos")

    print("\nChunking videos...")
    chunks = chunk_videos(all_videos, channel_name)
    print(f"Created {len(chunks)} total chunks")

    if not chunks:
        return {
            "channel": channel_name,
            "videos": len(all_videos),
            "chunks": 0,
            "embedded_chunks": 0,
            "estimated_cost": 0.0,
            "cost": 0.0,
            "tokens": 0,
            "status": "no_chunks",
        }

    topic_extractor = TopicExtractor()
    guest_extractor = GuestExtractor()
    chunks = enrich_chunks(chunks, topic_extractor, guest_extractor)

    cost_tracker = CostTracker()
    cost_estimate = cost_tracker.estimate_channel_cost(transcript_dir, chunk_pattern)
    print(
        "\nEstimated embedding cost before API call: "
        f"${cost_estimate['estimated_cost']:.6f} "
        f"({cost_estimate['tokens']:,} tokens across {cost_estimate['file_count']} files)"
    )

    if not skip_embeddings and daily_budget is not None:
        budget_ok = cost_tracker.check_budget(cost_estimate["estimated_cost"], daily_budget)
        if not budget_ok:
            today_spend = cost_tracker.get_today_spend()
            raise RuntimeError(
                "Embedding budget exceeded: "
                f"today_spend=${today_spend['cost']:.6f}, "
                f"estimate=${cost_estimate['estimated_cost']:.6f}, "
                f"daily_budget=${daily_budget:.6f}"
            )

    embedded_cost = 0.0
    embedded_tokens = 0
    if not skip_embeddings:
        print("\nGenerating embeddings...")
        embedder = EmbeddingGenerator()
        chunks = embedder.process_chunks(chunks)
        usage = embedder.get_last_usage()
        embedded_cost = usage.get("estimated_cost", 0.0)
        embedded_tokens = usage.get("tokens", 0)
        cost_tracker.log_spend(channel_name, embedded_tokens, embedded_cost)
    else:
        print("\nSkipping embeddings")

    if not skip_pinecone and not skip_embeddings:
        print("\nUploading to Pinecone...")
        pinecone = PineconeManager()
        pinecone.create_index()
        pinecone.upsert_chunks(channel_name, chunks)
    else:
        print("\nSkipping Pinecone upload")

    print("\nGenerating static files...")
    generate_static_files(channel_name, chunks, APP_GENERATED_DIR)

    print(f"\n{'=' * 60}")
    print(f"Pipeline complete for {channel_name}")
    print(f"{'=' * 60}\n")

    return {
        "channel": channel_name,
        "videos": len(all_videos),
        "chunks": len(chunks),
        "embedded_chunks": len([chunk for chunk in chunks if chunk.get("embedding")]),
        "estimated_cost": cost_estimate["estimated_cost"],
        "cost": embedded_cost,
        "tokens": embedded_tokens,
        "status": "success",
    }


def main():
    parser = argparse.ArgumentParser(description="Process transcripts for the wiki pipeline")
    parser.add_argument("--channel", required=True, help="Channel name from registry")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding generation")
    parser.add_argument("--skip-pinecone", action="store_true", help="Skip Pinecone upload")
    parser.add_argument("--daily-budget", type=float, default=None, help="Daily embedding budget in USD")
    args = parser.parse_args()

    process_channel(
        args.channel,
        skip_embeddings=args.skip_embeddings,
        skip_pinecone=args.skip_pinecone,
        daily_budget=args.daily_budget,
    )


if __name__ == "__main__":
    main()
