#!/usr/bin/env python3
"""
Generate video list with subtitle filtering
Only includes videos that have English subtitles available
Filters out shorts and videos without transcripts
"""

import subprocess
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ CONFIGURATION ============
CHANNEL_URL = "https://www.youtube.com/channel/UCVcxJ9k14bi__-uA1cGkEcA/videos"
OUTPUT_FILE = Path("ken_wheeler_video_list.txt")
WORKERS = 10  # Parallel subtitle checks
# =========================================

def check_subtitles(video_id):
    """Check if a video has English subtitles available"""
    try:
        cmd = [
            "yt-dlp",
            "--list-subs",
            "--skip-download",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Check if English subtitles are available
        if "en" in result.stdout.lower() or "english" in result.stdout.lower():
            return True
        return False
    except:
        return False

def get_video_info(video_id):
    """Get video metadata including duration to filter shorts"""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--skip-download",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = data.get('duration', 0)
            title = data.get('title', '')
            
            # Filter out shorts (< 60 seconds)
            if duration < 60:
                return None
            
            return {
                'id': video_id,
                'title': title,
                'duration': duration
            }
    except:
        pass
    return None

def main():
    print("=" * 80)
    print("SUBTITLE-FILTERED VIDEO LIST GENERATOR")
    print("=" * 80)
    print(f"Channel: {CHANNEL_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 80)
    print("\nStep 1: Fetching all video IDs from channel...")
    
    # Get all video IDs from channel
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(id)s",
        CHANNEL_URL
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    video_ids = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    
    print(f"✓ Found {len(video_ids)} total videos")
    
    print("\nStep 2: Filtering for videos with English subtitles (this may take a while)...")
    
    valid_videos = []
    checked = 0
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        # Submit all video info checks
        future_to_id = {
            executor.submit(get_video_info, vid): vid 
            for vid in video_ids
        }
        
        for future in as_completed(future_to_id):
            checked += 1
            video_info = future.result()
            
            if video_info:
                # Check if it has subtitles
                if check_subtitles(video_info['id']):
                    valid_videos.append(video_info)
                    print(f"[{checked}/{len(video_ids)}] ✓ {video_info['title'][:60]}")
                else:
                    print(f"[{checked}/{len(video_ids)}] ✗ No subs: {video_info.get('title', 'Unknown')[:60]}")
            else:
                print(f"[{checked}/{len(video_ids)}] ⊘ Skipped (short or error)")
    
    print(f"\n✓ Found {len(valid_videos)} videos with English subtitles")
    
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for video in valid_videos:
            f.write(f"{video['title']}\thttps://www.youtube.com/watch?v={video['id']}\n")
    
    print(f"\n✓ Saved to {OUTPUT_FILE}")
    print("=" * 80)
    print(f"SUMMARY:")
    print(f"  Total videos: {len(video_ids)}")
    print(f"  With subtitles: {len(valid_videos)}")
    print(f"  Filtered out: {len(video_ids) - len(valid_videos)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
