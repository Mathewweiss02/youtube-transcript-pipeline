#!/usr/bin/env python3
"""
Download and Merge Missing Huberman Videos - FIXED VERSION
- Works directly with VTT format (no SRT conversion needed)
- Handles file locking with retries
- Properly cleans up temporary files
"""

import os
import subprocess
import sys
import json
import time
import re
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

def clean_vtt_file(vtt_path):
    """Parse VTT file and extract clean text content."""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip VTT header (WEBVTT)
    cleaned_lines = []
    seen = set()
    
    for line in lines:
        line = line.strip()
        
        # Skip VTT metadata and timestamps
        if not line:
            continue
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        if '-->' in line:
            continue
        if line.isdigit():
            continue
        if line == '[Music]':
            continue
        
        # Remove VTT timestamp tags like <00:00:00.640>
        line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', line)
        # Remove <c> tags
        line = re.sub(r'</?c>', '', line)
        
        if line and line not in seen:
            seen.add(line)
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def download_cleaned_transcript(video):
    """Download auto-generated English subtitles (VTT) and clean them."""
    video_id = video['video_id']
    title = video['title']
    
    # Clean up any existing files first
    for ext in ['.en.vtt', '.vtt', '.md']:
        existing = OUTPUT_DIR / f"{video_id}{ext}"
        if existing.exists():
            try:
                existing.unlink()
            except Exception as e:
                print(f"  - Warning: Could not remove {existing.name}: {e}")
    
    # Clean up .part files with retries
    for attempt in range(3):
        try:
            for part_file in OUTPUT_DIR.glob(f"{video_id}.*.part"):
                part_file.unlink()
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"  - Warning: Could not remove .part files: {e}")
    
    # Download VTT subtitles
    temp_template = OUTPUT_DIR / f"{video_id}.%(ext)s"
    cmd = [
        str(yt_dlp_exe),
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "-o", str(temp_template),
        "--no-warnings",
        video['url']
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  - FAILED {video_id}: {e.stderr.strip()}")
        return None
    
    # Find the VTT file
    vtt_files = list(OUTPUT_DIR.glob(f"{video_id}*.vtt"))
    if not vtt_files:
        print(f"  - NO SUBS {video_id}")
        return None
    
    vtt_path = vtt_files[0]
    
    # Clean VTT and write .md file
    try:
        cleaned_text = clean_vtt_file(vtt_path)
        
        md_path = OUTPUT_DIR / f"{video_id}.md"
        with open(md_path, 'w', encoding='utf-8') as f_out:
            f_out.write(f"# {title}\n\n")
            f_out.write(f"URL: {video['url']}\n")
            f_out.write(f"Duration: {video.get('duration', 'N/A')}s\n\n")
            f_out.write("---\n\n")
            f_out.write(cleaned_text)
        
        # Clean up the VTT file
        vtt_path.unlink()
        return md_path
        
    except Exception as e:
        print(f"  - ERROR cleaning {video_id}: {e}")
        return None

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

if failed:
    print("Failed videos:")
    for video in failed:
        print(f"  - {video['video_id']}: {video['title'][:50]}")
    print()
