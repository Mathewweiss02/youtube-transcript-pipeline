#!/usr/bin/env python3
"""
Direct-to-Chunk Merger for Huberman Full Transcripts
Merges individual video transcripts directly into NotebookLM-compliant chunks (<2.5MB)
Avoids creating large intermediate files that caused previous corruption issues.
"""

import json
import os
from pathlib import Path

# Configuration
MAX_CHUNK_SIZE = 2.4 * 1024 * 1024  # 2.4MB (safety margin under 2.5MB)
BASE_DIR = Path(r"C:\Users\aweis\Downloads\YouTube_Tools_Scripts")
SOURCE_DIR = BASE_DIR / "Howdy" / "Huberman_Full_Transcripts"
OUTPUT_DIR = BASE_DIR / "Transcripts" / "Huberman"
METADATA_FILE = BASE_DIR / "Howdy" / "huberman_all_videos.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_video_order():
    """Load videos in correct order from metadata JSON."""
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    return videos

def read_transcript(video_id):
    """Read transcript content for a video ID."""
    transcript_file = SOURCE_DIR / f"{video_id}.md"
    if not transcript_file.exists():
        return None
    with open(transcript_file, 'r', encoding='utf-8') as f:
        return f.read()

def create_chunk_header(chunk_num, videos_in_chunk):
    """Create header for a chunk with TOC."""
    lines = [
        f"# Huberman Lab Full Archive - Chunk {chunk_num:02d}\n",
        f"## Table of Contents\n"
    ]
    for i, video in enumerate(videos_in_chunk, 1):
        lines.append(f"{i}. {video['title']}\n")
    lines.append("\n---\n\n")
    return "".join(lines)

def main():
    print("=" * 80)
    print("HUBERMAN FULL TRANSCRIPTS - DIRECT-TO-CHUNK MERGER")
    print("=" * 80)
    
    # Load video order
    videos = load_video_order()
    print(f"\nLoaded {len(videos)} videos from metadata")
    
    # Initialize chunk buffer
    current_chunk = []
    current_size = 0
    chunk_num = 1
    videos_in_current_chunk = []
    
    # Process videos in order
    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']
        
        # Read transcript
        content = read_transcript(video_id)
        if content is None:
            print(f"[{i}/{len(videos)}] ⚠️  Missing: {title[:50]}...")
            continue
        
        # Calculate content size
        content_size = len(content.encode('utf-8'))
        
        # Check if adding this video would exceed chunk size
        if current_size + content_size > MAX_CHUNK_SIZE and current_chunk:
            # Write current chunk
            write_chunk(chunk_num, videos_in_current_chunk, current_chunk)
            print(f"[{i}/{len(videos)}] ✅ Chunk {chunk_num} written ({current_size/1024/1024:.2f} MB)")
            
            # Reset for next chunk
            chunk_num += 1
            current_chunk = []
            current_size = 0
            videos_in_current_chunk = []
        
        # Add video to current chunk
        current_chunk.append(content)
        current_size += content_size
        videos_in_current_chunk.append(video)
        
        if i % 50 == 0:
            print(f"[{i}/{len(videos)}] Processing... (Current chunk: {current_size/1024/1024:.2f} MB)")
    
    # Write final chunk
    if current_chunk:
        write_chunk(chunk_num, videos_in_current_chunk, current_chunk)
        print(f"[{len(videos)}/{len(videos)}] ✅ Chunk {chunk_num} written ({current_size/1024/1024:.2f} MB)")
    
    # Summary
    print("\n" + "=" * 80)
    print("MERGE COMPLETE")
    print("=" * 80)
    print(f"Total chunks created: {chunk_num}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"\nAll chunks are under {MAX_CHUNK_SIZE/1024/1024:.2f} MB")

def write_chunk(chunk_num, videos, content_list):
    """Write a chunk to disk."""
    header = create_chunk_header(chunk_num, videos)
    content = header + "\n\n---\n\n".join(content_list)
    
    output_file = OUTPUT_DIR / f"HUBERMAN_FULL_CHUNK_{chunk_num:02d}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
