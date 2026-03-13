#!/usr/bin/env python3
"""
Download and Merge Andrew Huberman Essentials Playlist
Using OG script approach (no rate limiting)
"""

import os
import subprocess
import sys
import json
from pathlib import Path

# Load playlist
playlist_file = Path('../Howdy/huberman_essentials_playlist.json')

with open(playlist_file, 'r', encoding='utf-8') as f:
    videos = json.load(f)

print(f"Loaded {len(videos)} videos from Essentials playlist")
print()

# Output directory
OUTPUT_DIR = Path('../Howdy/Essentials_Transcripts')
OUTPUT_DIR.mkdir(exist_ok=True)

# Force yt-dlp from this Python install
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
print(f"Transcripts saved to: {OUTPUT_DIR}")
print()

# Now create merged file optimized for NotebookLM
print("Creating merged file for NotebookLM...")
print()

merged_file = Path('../Howdy/HUBERMAN_ESSENTIALS_CONSOLIDATED.md')
with open(merged_file, 'w', encoding='utf-8') as f_out:
    f_out.write("# Andrew Huberman Lab Essentials - Consolidated Transcripts\n\n")
    f_out.write("## Table of Contents\n\n")
    
    # Write TOC
    for i, video in enumerate(successful, 1):
        video_id = video['video_id']
        title = video['title']
        safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        f_out.write(f"- {i:03d} - {safe_title}.en\n")
    
    f_out.write("\n" + "=" * 80 + "\n\n")
    
    # Write each transcript
    for i, video in enumerate(successful, 1):
        video_id = video['video_id']
        md_file = OUTPUT_DIR / f"{video_id}.md"
        
        if md_file.exists():
            f_out.write(f"\n\n{'=' * 80}\n")
            f_out.write(f"Video {i:03d} of {len(successful)}\n")
            f_out.write(f"{'=' * 80}\n\n")
            
            with open(md_file, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
                f_out.write(content)
    
    f_out.write("\n\n" + "=" * 80 + "\n")
    f_out.write("END OF TRANSCRIPTS\n")
    f_out.write("=" * 80 + "\n")

print(f"✓ Created merged file: {merged_file}")
print(f"  File size: {merged_file.stat().st_size / 1024 / 1024:.1f} MB")
print()
print("All done! Check the Howdy folder for:")
print("  - Individual transcripts in Essentials_Transcripts/")
print("  - Consolidated file: HUBERMAN_ESSENTIALS_CONSOLIDATED.md")
