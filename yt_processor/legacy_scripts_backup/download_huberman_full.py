#!/usr/bin/env python3
"""
Download and Merge Missing Huberman Videos
"""

import os
import subprocess
import sys
import json
from pathlib import Path

# Load missing videos
missing_file = Path('../Howdy/huberman_missing_videos.json')

with open(missing_file, 'r', encoding='utf-8') as f:
    videos = json.load(f)

print(f"Loaded {len(videos)} missing videos")
print()

# Output directory
OUTPUT_DIR = Path('../Howdy/Huberman_Full_Transcripts')
OUTPUT_DIR.mkdir(exist_ok=True)

# Force yt-dlp
scripts_dir = Path(sys.executable).parent / 'Scripts'
yt_dlp_exe = scripts_dir / 'yt-dlp.exe'
if not yt_dlp_exe.exists():
    yt_dlp_exe = "yt-dlp"

print(f"Using yt-dlp: {yt_dlp_exe}")
print(f"Output directory: {OUTPUT_DIR}")
print()
print("Starting download (no rate limiting)...")
print()

def download_cleaned_transcript(video):
    """Download auto-generated English subtitles and strip timestamps."""
    video_id = video['video_id']
    title = video['title']
    
    # 1) Download .srt to temp location
    temp_template = OUTPUT_DIR / f"{video_id}.%(ext)s"
    cmd = [
        str(yt_dlp_exe),
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "--convert-subs", "srt",
        "-o", str(temp_template),
        video['url']
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  - FAILED {video_id}: {e.stderr.strip()}")
        return None

    # 2) Find the .en.srt file
    srt_path = OUTPUT_DIR / f"{video_id}.en.srt"
    if not srt_path.exists():
        srt_path = OUTPUT_DIR / f"{video_id}.srt"
    
    if not srt_path.exists():
        print(f"  - NO SUBS {video_id}")
        return None

    # 3) Clean timestamps and write .md file
    md_path = OUTPUT_DIR / f"{video_id}.md"
    with open(srt_path, 'r', encoding='utf-8') as f_in, open(md_path, 'w', encoding='utf-8') as f_out:
        seen = set()
        f_out.write(f"# {title}\n\n")
        f_out.write(f"URL: {video['url']}\n")
        f_out.write(f"Duration: {video.get('duration', 'N/A')}s\n\n")
        f_out.write("---\n\n")
        
        for line in f_in:
            line = line.strip()
            if not line: continue
            if line.isdigit(): continue
            if "-->" in line: continue
            if line in seen: continue
            seen.add(line)
            f_out.write(line + "\n")
    
    # Clean up the .srt file
    srt_path.unlink()
    return md_path

# Main loop
successful = []
failed = []

for i, video in enumerate(videos, 1):
    video_id = video['video_id']
    title = video['title'][:60] + '...' if len(video['title']) > 60 else video['title']
    
    print(f"[{i}/{len(videos)}] {title}")
    
    md_path = download_cleaned_transcript(video)
    if md_path:
        print(f"  -> {md_path.name}")
        successful.append(video)
    else:
        failed.append(video)

print()
print("=" * 80)
print("DOWNLOAD COMPLETE!")
print("=" * 80)
print()
print(f"✓ Successfully downloaded: {len(successful)} videos")
print(f"✗ Failed: {len(failed)} videos")
print()

# Merge into NotebookLM files (max 400k words approx 2.5MB)
print("Creating consolidated files for NotebookLM...")
print()

# Split into chunks of 50 videos
chunks = [successful[i:i + 50] for i in range(0, len(successful), 50)]

for chunk_idx, chunk in enumerate(chunks, 1):
    merged_file = Path(f'../Howdy/HUBERMAN_FULL_PART_{chunk_idx:02d}.md')
    
    with open(merged_file, 'w', encoding='utf-8') as f_out:
        f_out.write(f"# Andrew Huberman Lab Full Archive - Part {chunk_idx:02d}\n\n")
        f_out.write("## Table of Contents\n\n")
        
        for i, video in enumerate(chunk, 1):
            title = video['title']
            f_out.write(f"- {i:03d} - {title}\n")
        
        f_out.write("\n" + "=" * 80 + "\n\n")
        
        for i, video in enumerate(chunk, 1):
            video_id = video['video_id']
            md_file = OUTPUT_DIR / f"{video_id}.md"
            
            if md_file.exists():
                f_out.write(f"\n\n{'=' * 80}\n")
                f_out.write(f"Video {i:03d}: {video['title']}\n")
                f_out.write(f"{'=' * 80}\n\n")
                
                with open(md_file, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()
                    f_out.write(content)
    
    print(f"✓ Created merged file: {merged_file}")
    print(f"  File size: {merged_file.stat().st_size / 1024 / 1024:.1f} MB")

print()
print("All done!")
