#!/usr/bin/env python3
"""
Jay Campbell Full Data Collector

Fetches complete video metadata from YouTube channel and organizes it
for batch transcript downloading. Creates a ready-to-use JSON file with
all URLs, titles, and metadata.

Outputs:
    - jay_campbell_full_inventory.json (complete channel data)
    - jay_campbell_download_queue.json (missing videos ready for download)
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Any


# Paths
SIDEcar_PATH = Path("../../youtuber wiki apps/my-app/data/transcript-video-sidecars.json")
INVENTORY_PATH = Path("jay_campbell_full_inventory.json")
QUEUE_PATH = Path("jay_campbell_download_queue.json")


def fetch_channel_videos() -> list[dict[str, Any]]:
    """Fetch all videos from Jay Campbell's YouTube channel."""
    print("📺 Fetching Jay Campbell YouTube channel data...")
    print("   Channel: @JayCampbell")
    
    # YouTube channel URLs to try - Jay Campbell has multiple possible URLs
    urls_to_try = [
        "https://www.youtube.com/@jaycampbellpodcast/videos",
        "https://www.youtube.com/c/JayCampbellPodcast/videos",
        "https://www.youtube.com/@jaycampbell333/videos",
        "https://www.youtube.com/channel/UCx9zGDevKE1Ep7-8fE0r4Ww/videos",
        "https://www.youtube.com/user/jaycampbell/videos",
    ]
    
    all_videos = []
    
    for url in urls_to_try:
        print(f"\n   Trying: {url}")
        
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s|%(title)s|%(duration)s|%(upload_date)s",
            "--playlist-reverse",
            url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=180
            )
            
            if result.returncode != 0:
                continue
            
            videos = []
            for line in result.stdout.strip().split('\n'):
                if not line or '|' not in line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) >= 3:
                    video_id = parts[0].strip()
                    title = parts[1].strip()
                    duration_str = parts[2].strip()
                    upload_date = parts[3].strip() if len(parts) > 3 else ''
                    
                    # Skip shorts
                    try:
                        duration = int(duration_str)
                        if duration <= 60:
                            continue
                    except ValueError:
                        duration = 0
                    
                    videos.append({
                        'video_id': video_id,
                        'title': title,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'duration_seconds': duration,
                        'duration_formatted': format_duration(duration),
                        'upload_date': upload_date,
                        'thumbnail': f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg'
                    })
            
            if videos:
                print(f"   ✅ Found {len(videos)} videos")
                all_videos.extend(videos)
                
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Timeout")
            continue
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Deduplicate by video_id
    seen = set()
    unique = []
    for v in all_videos:
        if v['video_id'] not in seen:
            seen.add(v['video_id'])
            unique.append(v)
    
    print(f"\n📊 Total unique videos: {len(unique)}")
    return unique


def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def load_existing_data() -> tuple[set[str], dict[str, str]]:
    """Load existing transcript data from sidecar."""
    if not SIDEcar_PATH.exists():
        print(f"⚠️ Sidecar not found: {SIDEcar_PATH}")
        return set(), {}
    
    with open(SIDEcar_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('channels', {}).get('jay-campbell', {}).get('entries', [])
    
    existing_ids = set()
    title_to_id = {}
    
    for entry in entries:
        vid = entry.get('videoId', '')
        title = entry.get('title', '')
        if vid:
            existing_ids.add(vid)
            title_to_id[normalize_title(title)] = vid
    
    return existing_ids, title_to_id


def normalize_title(title: str) -> str:
    """Normalize title for matching."""
    # Unicode replacements
    replacements = {
        '：': ':', '⧸': '/', '｜': '|', '＂': '"', '？': '?', '！': '!',
        '（': '(', '）': ')', '．': '.', '，': ',', '／': '/', '＆': '&',
        '＃': '#', '＠': '@', '％': '%', '－': '-', '［': '[', '］': ']',
        '｛': '{', '｝': '}', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
    }
    
    title = title.strip().lower()
    for old, new in replacements.items():
        title = title.replace(old, new)
    
    # Strip episode numbers
    title = re.sub(r'^\d+\s*-\s*', '', title)
    # Remove .en suffix
    title = re.sub(r'\.en$', '', title)
    # Remove podcast suffixes
    title = re.sub(r'\s*\|\s*the jay campbell podcast$', '', title)
    title = re.sub(r'\s*\|\s*jay campbell podcast$', '', title)
    title = re.sub(r'\s*\|\s*jay campbell pc$', '', title)
    title = re.sub(r'\|\s*jay campbell pc$', '', title)
    # w/ to with
    title = re.sub(r'\bw/\s*', 'with ', title)
    
    return re.sub(r'\s+', ' ', title).strip()


def categorize_videos(
    all_videos: list[dict],
    existing_ids: set[str],
    title_to_id: dict[str, str]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Categorize videos into: with transcripts, missing, potential renames."""
    
    with_transcripts = []
    missing = []
    potential_renames = []
    
    for video in all_videos:
        vid = video['video_id']
        
        if vid in existing_ids:
            with_transcripts.append(video)
            continue
        
        # Check for title match
        norm_title = normalize_title(video['title'])
        matched = False
        
        for existing_norm, existing_vid in title_to_id.items():
            # Exact match
            if norm_title == existing_norm:
                video['potential_match_id'] = existing_vid
                video['match_reason'] = 'exact_title_match'
                potential_renames.append(video)
                matched = True
                break
            
            # Substring match
            if norm_title in existing_norm or existing_norm in norm_title:
                if len(norm_title) > 20 and len(existing_norm) > 20:
                    video['potential_match_id'] = existing_vid
                    video['match_reason'] = 'substring_match'
                    potential_renames.append(video)
                    matched = True
                    break
        
        if not matched:
            missing.append(video)
    
    return with_transcripts, missing, potential_renames


def save_inventory(
    all_videos: list[dict],
    with_transcripts: list[dict],
    missing: list[dict],
    potential_renames: list[dict]
):
    """Save complete inventory report."""
    
    inventory = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'channel': 'jay-campbell',
        'summary': {
            'total_videos': len(all_videos),
            'with_transcripts': len(with_transcripts),
            'missing_transcripts': len(missing),
            'potential_renames': len(potential_renames),
            'coverage_percent': round(100 * len(with_transcripts) / len(all_videos), 1) if all_videos else 0
        },
        'videos': {
            'with_transcripts': with_transcripts,
            'missing': missing,
            'potential_renames': potential_renames
        }
    }
    
    with open(INVENTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Inventory saved: {INVENTORY_PATH}")


def save_download_queue(missing: list[dict]):
    """Save download-ready queue for missing videos."""
    
    queue = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'channel': 'jay-campbell',
        'total_missing': len(missing),
        'videos': [
            {
                'video_id': v['video_id'],
                'title': v['title'],
                'url': v['url'],
                'duration': v['duration_formatted'],
                'thumbnail': v['thumbnail'],
                'upload_date': v.get('upload_date', '')
            }
            for v in missing
        ]
    }
    
    with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Download queue saved: {QUEUE_PATH}")


def print_summary(
    with_transcripts: list[dict],
    missing: list[dict],
    potential_renames: list[dict]
):
    """Print formatted summary."""
    
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    total = len(with_transcripts) + len(missing) + len(potential_renames)
    coverage = 100 * len(with_transcripts) / total if total else 0
    
    print(f"\n✅ With transcripts:     {len(with_transcripts):3d} ({100*len(with_transcripts)/total:.1f}%)")
    print(f"❌ Missing:             {len(missing):3d} ({100*len(missing)/total:.1f}%)")
    print(f"🔍 Potential renames:   {len(potential_renames):3d} ({100*len(potential_renames)/total:.1f}%)")
    print(f"\n📈 Coverage: {coverage:.1f}%")
    
    if missing:
        print(f"\n{'='*60}")
        print("📥 READY TO DOWNLOAD (First 15)")
        print(f"{'='*60}")
        
        for i, video in enumerate(missing[:15], 1):
            print(f"\n{i}. {video['title'][:70]}{'...' if len(video['title']) > 70 else ''}")
            print(f"   🎬 {video['url']}")
            print(f"   ⏱️  {video['duration_formatted']} | 📅 {video.get('upload_date', 'N/A')}")
        
        if len(missing) > 15:
            print(f"\n... and {len(missing) - 15} more")
    
    if potential_renames:
        print(f"\n{'='*60}")
        print("🔍 POTENTIAL RENAMES (Check these manually)")
        print(f"{'='*60}")
        
        for video in potential_renames[:5]:
            print(f"\nYouTube: {video['title'][:60]}{'...' if len(video['title']) > 60 else ''}")
            print(f"   Match: {video.get('match_reason', 'unknown')}")
            print(f"   URL: {video['url']}")


def main():
    print("="*60)
    print("🎙️  Jay Campbell Full Data Collector")
    print("="*60)
    
    # Fetch all videos from YouTube
    all_videos = fetch_channel_videos()
    
    if not all_videos:
        print("\n❌ No videos found. Check yt-dlp installation and channel URL.")
        sys.exit(1)
    
    # Load existing transcript data
    print("\n📂 Loading existing transcript data...")
    existing_ids, title_to_id = load_existing_data()
    print(f"   Found {len(existing_ids)} existing transcripts")
    
    # Categorize
    print("\n🔍 Analyzing videos...")
    with_trans, missing, renames = categorize_videos(all_videos, existing_ids, title_to_id)
    
    # Save files
    save_inventory(all_videos, with_trans, missing, renames)
    save_download_queue(missing)
    
    # Print summary
    print_summary(with_trans, missing, renames)
    
    print(f"\n{'='*60}")
    print("✅ Done! Check these files:")
    print(f"   📄 {INVENTORY_PATH} - Complete inventory")
    print(f"   📄 {QUEUE_PATH} - Download queue")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
