import subprocess
import json
import os
from pathlib import Path

# Load videos
with open('alchemical_science_videos.json') as f:
    videos = json.load(f)

print(f"Downloading {len(videos)} transcripts...")

transcript_dir = Path('../transcripts/Alchemical_Science')
raw_dir = Path('../transcripts/Alchemical_Science_Raw')

# Download each transcript
for i, video in enumerate(videos):
    video_id = video['video_id']
    title = video['title']
    
    # Skip if already downloaded (check raw dir)
    raw_file = raw_dir / f"{video_id}.md"
    if raw_file.exists():
        print(f"  [{i+1}/{len(videos)}] Already have: {title[:40]}...")
        continue
    
    print(f"  [{i+1}/{len(videos)}] Downloading: {title[:40]}...")
    
    # Download transcript using yt-dlp
    try:
        result = subprocess.run([
            'yt-dlp',
            '--write-auto-sub',
            '--write-subs',
            '--sub-lang', 'en',
            '--skip-download',
            '--output', str(raw_dir / f"{video_id}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}"
        ], capture_output=True, text=True, timeout=60)
    except Exception as e:
        print(f"    Error: {e}")

print("Done!")
