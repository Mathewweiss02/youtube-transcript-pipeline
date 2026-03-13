#!/usr/bin/env python3
"""
Download transcripts from multiple channels in parallel.
"""
import os
import sys
import subprocess
import threading
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_BASE = os.path.join(os.path.dirname(BASE_DIR), "transcripts")

# Force yt-dlp from this Python install
scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
yt_dlp_exe = os.path.join(scripts_dir, "yt-dlp.exe")
if not os.path.exists(yt_dlp_exe):
    yt_dlp_exe = "yt-dlp"

# Channels to process
CHANNELS = [
    ("warriorcollective", "https://www.youtube.com/@warriorcollective/videos"),
    ("combatathletephysio", "https://www.youtube.com/@combatathletephysio/videos"),
    ("coachmicahb", "https://www.youtube.com/@CoachMicahB/videos"),
]

def sanitize_filename(title):
    """Sanitize a video title to be a safe Windows filename."""
    name = "".join(c if c.isalnum() or c in (" ", "-", "_", "(", ")", "[", "]", ".", ",") else "_" for c in title).strip()
    name = " ".join(name.split())
    if len(name) > 100:
        name = name[:97] + "..."
    return name

def get_channel_videos(channel_url):
    """Get all videos from channel using yt-dlp."""
    cmd = [
        yt_dlp_exe,
        "--flat-playlist",
        "--print", "%(id)s\t%(title)s",
        channel_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        videos = []
        if result.stdout:
            for line in result.stdout.splitlines():
                if "\t" in line:
                    vid, title = line.split("\t", 1)
                    videos.append((vid, title))
        return videos
    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

def download_cleaned_transcript(video_id, title, output_dir):
    """Download auto-generated English subtitles and strip timestamps."""
    safe_name = sanitize_filename(title)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    if os.path.exists(md_path):
        return "SKIP"
    
    temp_template = os.path.join(output_dir, f"{video_id}.%(ext)s")
    cmd = [
        yt_dlp_exe,
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "--convert-subs", "srt",
        "-o", temp_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    except subprocess.CalledProcessError:
        return "FAIL"

    srt_path = os.path.join(output_dir, f"{video_id}.en.srt")
    if not os.path.exists(srt_path):
        srt_path = os.path.join(output_dir, f"{video_id}.srt")
    if not os.path.exists(srt_path):
        return "NOSUB"

    with open(srt_path, "r", encoding="utf-8", errors='replace') as f_in, open(md_path, "w", encoding="utf-8") as f_out:
        seen = set()
        f_out.write(f"# {title}\n\n")
        f_out.write(f"https://www.youtube.com/watch?v={video_id}\n\n")
        for line in f_in:
            line = line.strip()
            if not line: continue
            if line.isdigit(): continue
            if "-->" in line: continue
            if line in seen: continue
            seen.add(line)
            f_out.write(line + "\n")
    
    try:
        os.remove(srt_path)
    except:
        pass
    
    return "OK"

def process_channel(channel_name, channel_url):
    """Process a single channel."""
    print(f"\n[{channel_name.upper()}] Starting...")
    
    output_dir = os.path.join(TRANSCRIPTS_BASE, channel_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch videos
    print(f"[{channel_name.upper()}] Fetching video list...")
    videos = get_channel_videos(channel_url)
    print(f"[{channel_name.upper()}] Found {len(videos)} videos")
    
    if not videos:
        print(f"[{channel_name.upper()}] No videos found!")
        return
    
    # Download transcripts
    success = 0
    failed = 0
    skipped = 0
    nosub = 0
    
    for i, (vid, title) in enumerate(videos, 1):
        status = download_cleaned_transcript(vid, title, output_dir)
        
        if status == "OK":
            success += 1
        elif status == "SKIP":
            skipped += 1
        elif status == "NOSUB":
            nosub += 1
        else:
            failed += 1
        
        if i % 50 == 0:
            print(f"[{channel_name.upper()}] [{i}/{len(videos)}] Downloaded {success} so far...")
    
    print(f"\n[{channel_name.upper()}] COMPLETE:")
    print(f"  Success: {success}")
    print(f"  Skipped: {skipped}")
    print(f"  No subs: {nosub}")
    print(f"  Failed: {failed}")
    print(f"  Output: {output_dir}")

def main():
    print(f"Using yt-dlp: {yt_dlp_exe}")
    print(f"Processing {len(CHANNELS)} channels in parallel...\n")
    
    threads = []
    for channel_name, channel_url in CHANNELS:
        thread = threading.Thread(target=process_channel, args=(channel_name, channel_url))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("\n" + "="*70)
    print("ALL CHANNELS COMPLETE!")
    print("="*70)

if __name__ == "__main__":
    main()
