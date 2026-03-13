#!/usr/bin/env python3
"""
Jay Campbell Bulk Re-Downloader

Uses universal_parallel_downloader.py approach but with inventory JSON.
Re-downloads all 269 videos with proper URL: format.
"""

import json
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time

# Configuration
INVENTORY_PATH = Path("jay_campbell_full_inventory.json")
OUTPUT_DIR = Path("../../transcripts/Jay_Campbell_Redownload")
WORKERS = 10

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# yt-dlp path
scripts_dir = Path(sys.executable).parent / 'Scripts'
yt_dlp_exe = scripts_dir / 'yt-dlp.exe'
if not yt_dlp_exe.exists():
    yt_dlp_exe = "yt-dlp"


def clean_vtt_file(vtt_path):
    """Parse VTT file and extract clean text content."""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    seen = set()
    
    for line in lines:
        line = line.strip()
        
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
        
        # Remove VTT timestamp tags
        line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', line)
        line = re.sub(r'</?c>', '', line)
        
        if line and line not in seen:
            seen.add(line)
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def download_video(video_data):
    """Download transcript for a single video."""
    title = video_data['title']
    url = video_data['url']
    video_id = video_data['video_id']
    
    # Clean up existing files
    for ext in ['.en.vtt', '.vtt', '.md']:
        existing = OUTPUT_DIR / f"{video_id}{ext}"
        if existing.exists():
            try:
                existing.unlink()
            except:
                pass
    
    # Clean up .part files
    for attempt in range(3):
        try:
            for part_file in OUTPUT_DIR.glob(f"{video_id}.*.part"):
                part_file.unlink()
            break
        except:
            if attempt < 2:
                time.sleep(1)
    
    # Download VTT subtitles
    temp_template = OUTPUT_DIR / f"{video_id}.%(ext)s"
    cmd = [
        str(yt_dlp_exe),
        "--write-auto-sub",
        "--sub-langs", "en",
        "--skip-download",
        "-o", str(temp_template),
        "--no-warnings",
        url
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return (title, "FAILED", e.stderr.strip()[:100] if e.stderr else "yt-dlp error")
    
    # Find VTT file
    vtt_files = list(OUTPUT_DIR.glob(f"{video_id}*.vtt"))
    if not vtt_files:
        return (title, "NO_SUBS", "No subtitles available")
    
    vtt_path = vtt_files[0]
    
    # Clean and write .md file with proper format
    try:
        cleaned_text = clean_vtt_file(vtt_path)
        
        md_path = OUTPUT_DIR / f"{video_id}.md"
        with open(md_path, 'w', encoding='utf-8') as f_out:
            f_out.write(f"# {title}\n\n")
            f_out.write(f"URL: {url}\n")
            f_out.write(f"Video ID: {video_id}\n\n")
            f_out.write("---\n\n")
            f_out.write(cleaned_text)
        
        # Clean up VTT file
        vtt_path.unlink()
        return (title, "SUCCESS", f"{md_path.name}")
        
    except Exception as e:
        return (title, "ERROR", str(e)[:100])


def main():
    print("=" * 80)
    print("🎙️ JAY CAMPBELL BULK RE-DOWNLOADER")
    print("=" * 80)
    print(f"Using yt-dlp: {yt_dlp_exe}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Workers: {WORKERS}")
    print()
    
    # Load inventory
    if not INVENTORY_PATH.exists():
        print(f"❌ Inventory not found: {INVENTORY_PATH}")
        print("Run: python jay_campbell_collector.py")
        sys.exit(1)
    
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data.get('videos', {}).get('missing', []) + data.get('videos', {}).get('with_transcripts', [])
    
    print(f"📺 Videos to download: {len(videos)}")
    print(f"📁 Output: {OUTPUT_DIR}")
    print()
    
    # Download with thread pool
    successful = []
    failed = []
    no_subs = []
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(download_video, video): video for video in videos}
        
        for i, future in enumerate(as_completed(futures), 1):
            title, status, message = future.result()
            
            if status == "SUCCESS":
                print(f"[{i}/{len(videos)}] ✅ {title[:50]}...")
                successful.append(title)
            elif status == "NO_SUBS":
                print(f"[{i}/{len(videos)}] ⚠️  {title[:50]}... (no subtitles)")
                no_subs.append(title)
            else:
                print(f"[{i}/{len(videos)}] ❌ {title[:50]}... ({status})")
                failed.append((title, status, message))
    
    print()
    print("=" * 80)
    print("📊 DOWNLOAD COMPLETE!")
    print("=" * 80)
    print(f"✅ Success: {len(successful)}/{len(videos)}")
    print(f"⚠️  No subtitles: {len(no_subs)}/{len(videos)}")
    print(f"❌ Failed: {len(failed)}/{len(videos)}")
    
    if failed:
        print("\nFailed videos:")
        for title, status, msg in failed[:10]:
            print(f"  - {title[:50]}... ({status})")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    print()
    print("💡 Next steps:")
    print("   1. Check files in Jay_Campbell_Redownload/")
    print("   2. Run wiki_chunker.py to merge into consolidated parts")
    print("   3. Update sidecar with new video IDs")
    print("   4. Delete old Jay_Campbell/ directory when ready")


if __name__ == "__main__":
    main()
