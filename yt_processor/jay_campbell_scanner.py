#!/usr/bin/env python3
"""
Jay Campbell Missing Video Scanner

Compares videos on the YouTube channel against existing transcript entries
to identify missing videos that need to be downloaded.

Usage:
    python jay_campbell_scanner.py

Outputs:
    - Missing videos report (missing_videos_report.json)
    - Summary with video IDs ready for transcript downloading
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# YouTube channel URL
JAY_CAMPBELL_CHANNEL = "https://www.youtube.com/@JayCampbell Podcast/videos"

# Paths
SIDEcar_PATH = Path("../../youtuber wiki apps/my-app/data/transcript-video-sidecars.json")
OUTPUT_PATH = Path("jay_campbell_missing.json")


def run_ytdlp_channel_scan(channel_url: str) -> list[dict[str, Any]]:
    """Scan YouTube channel for all video IDs and titles using yt-dlp."""
    print(f"Scanning channel: {channel_url}")
    print("This may take a few minutes...")
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(id)s|%(title)s|%(duration)s",
        "--playlist-reverse",  # Oldest first
        channel_url
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}", file=sys.stderr)
            return []
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line or '|' not in line:
                continue
            parts = line.split('|', 2)
            if len(parts) >= 2:
                video_id = parts[0].strip()
                title = parts[1].strip()
                duration_str = parts[2].strip() if len(parts) > 2 else '0'
                
                # Skip shorts (<= 60 seconds)
                try:
                    duration = int(duration_str)
                    if duration <= 60:
                        continue
                except ValueError:
                    pass
                
                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })
        
        print(f"Found {len(videos)} videos on channel (excluding shorts)")
        return videos
        
    except subprocess.TimeoutExpired:
        print("Channel scan timed out after 5 minutes", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("yt-dlp not found. Please install: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)


def load_existing_transcripts() -> set[str]:
    """Load existing transcript video IDs from sidecar."""
    if not SIDEcar_PATH.exists():
        print(f"Sidecar file not found: {SIDEcar_PATH}")
        return set()
    
    with open(SIDEcar_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jay_campbell_entries = data.get('channels', {}).get('jay-campbell', {}).get('entries', [])
    
    video_ids = set()
    for entry in jay_campbell_entries:
        video_id = entry.get('videoId', '')
        if video_id:
            video_ids.add(video_id)
    
    print(f"Found {len(video_ids)} videos in existing transcripts")
    return video_ids


def normalize_title_for_matching(title: str) -> str:
    """Normalize title for comparison (handles Jay Campbell's Unicode issues)."""
    # Unicode normalization
    title = title.strip()
    
    # Replace common Unicode chars
    replacements = {
        '：': ':',
        '⧸': '/',
        '｜': '|',
        '＂': '"',
        '？': '?',
        '！': '!',
        '（': '(',
        '）': ')',
        '．': '.',
        '，': ',',
        '／': '/',
        '＆': '&',
        '＃': '#',
        '＠': '@',
        '％': '%',
        '－': '-',
        '［': '[',
        '］': ']',
        '｛': '{',
        '｝': '}',
    }
    
    for old, new in replacements.items():
        title = title.replace(old, new)
    
    # Strip episode numbers like "001 -", "204 -"
    title = re.sub(r'^\d+\s*-\s*', '', title)
    
    # Remove .en suffix
    title = re.sub(r'\.en$', '', title, flags=re.IGNORECASE)
    
    # Remove "The Jay Campbell Podcast" suffix
    title = re.sub(r'\s*\|\s*The Jay Campbell Podcast$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\|\s*Jay Campbell Podcast$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\|\s*Jay Campbell PC$', '', title, flags=re.IGNORECASE)
    
    # Replace w/ with with
    title = re.sub(r'\bw/\s*', 'with ', title, flags=re.IGNORECASE)
    
    # Normalize whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title.lower()


def find_missing_videos(channel_videos: list[dict], existing_ids: set[str]) -> list[dict]:
    """Find videos on channel that aren't in transcripts."""
    missing = []
    
    for video in channel_videos:
        if video['video_id'] not in existing_ids:
            missing.append(video)
    
    return missing


def find_potential_matches(missing: list[dict], existing_titles: list[str]) -> list[dict]:
    """Try to find potential title matches for missing videos."""
    results = []
    
    for video in missing:
        normalized = normalize_title_for_matching(video['title'])
        potential_match = None
        
        for existing in existing_titles:
            existing_norm = normalize_title_for_matching(existing)
            
            # Check for substring match
            if normalized in existing_norm or existing_norm in normalized:
                potential_match = existing
                break
            
            # Check word overlap (> 70% of words match)
            missing_words = set(normalized.split())
            existing_words = set(existing_norm.split())
            
            if missing_words and existing_words:
                overlap = len(missing_words & existing_words)
                total = len(missing_words | existing_words)
                
                if total > 0 and overlap / total > 0.7:
                    potential_match = existing
                    break
        
        video['normalized_title'] = normalized
        video['potential_match'] = potential_match
        results.append(video)
    
    return results


def main():
    print("=" * 60)
    print("Jay Campbell Missing Video Scanner")
    print("=" * 60)
    print()
    
    # Load existing transcripts
    existing_ids = load_existing_transcripts()
    
    # Scan YouTube channel
    print()
    channel_videos = run_ytdlp_channel_scan(JAY_CAMPBELL_CHANNEL)
    
    if not channel_videos:
        print("No videos found on channel. Check the channel URL.")
        return
    
    # Find missing videos
    print()
    missing = find_missing_videos(channel_videos, existing_ids)
    
    print(f"\nMissing videos: {len(missing)}")
    print(f"Coverage: {len(existing_ids)}/{len(channel_videos)} ({100*len(existing_ids)/len(channel_videos):.1f}%)")
    
    # Try to find potential title matches
    sidecar_data = {}
    if SIDEcar_PATH.exists():
        with open(SIDEcar_PATH, 'r', encoding='utf-8') as f:
            sidecar_data = json.load(f)
    
    existing_titles = [
        entry.get('title', '')
        for entry in sidecar_data.get('channels', {}).get('jay-campbell', {}).get('entries', [])
    ]
    
    missing_with_matches = find_potential_matches(missing, existing_titles)
    
    # Categorize
    likely_renames = [v for v in missing_with_matches if v.get('potential_match')]
    truly_missing = [v for v in missing_with_matches if not v.get('potential_match')]
    
    print(f"\nBreakdown:")
    print(f"  - Likely renamed/retitled: {len(likely_renames)}")
    print(f"  - Truly missing (no transcript): {len(truly_missing)}")
    
    # Save report
    report = {
        'channel': 'jay-campbell',
        'scanned_at': subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode().strip(),
        'summary': {
            'channel_total': len(channel_videos),
            'existing_transcripts': len(existing_ids),
            'missing_count': len(missing),
            'coverage_percent': round(100 * len(existing_ids) / len(channel_videos), 1),
            'likely_renames': len(likely_renames),
            'truly_missing': len(truly_missing)
        },
        'truly_missing': truly_missing,
        'likely_renamed': likely_renames
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved to: {OUTPUT_PATH}")
    
    # Print truly missing videos (ready for download)
    if truly_missing:
        print(f"\n{'='*60}")
        print("TRULY MISSING VIDEOS (Ready for download):")
        print(f"{'='*60}")
        for video in truly_missing[:20]:  # Show first 20
            print(f"\n{video['title']}")
            print(f"  URL: {video['url']}")
            print(f"  Video ID: {video['video_id']}")
        
        if len(truly_missing) > 20:
            print(f"\n... and {len(truly_missing) - 20} more")
    
    # Print likely renames
    if likely_renames:
        print(f"\n{'='*60}")
        print("LIKELY RENAMED (Check if these are the same video):")
        print(f"{'='*60}")
        for video in likely_renames[:10]:  # Show first 10
            print(f"\nChannel: {video['title']}")
            print(f"  Potential match in transcripts: {video['potential_match']}")
            print(f"  URL: {video['url']}")


if __name__ == '__main__':
    main()
