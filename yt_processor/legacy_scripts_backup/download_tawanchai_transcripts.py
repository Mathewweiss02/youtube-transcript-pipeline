#!/usr/bin/env python3
"""
Download transcripts from high-value Tawanchai videos
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import yt_dlp

def download_transcripts(video_list, output_dir):
    """Download transcripts from a list of videos"""
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'skip_download': True,
        'quiet': False,
        'no_warnings': False,
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'subtitlesformat': 'vtt',
    }
    
    successful = []
    failed = []
    
    for i, video in enumerate(video_list, 1):
        video_id = video['video_id']
        url = video['url']
        title = video['title'][:50] + '...' if len(video['title']) > 50 else video['title']
        
        print(f"\n[{i}/{len(video_list)}] Downloading transcript for: {title}")
        print(f"  URL: {url}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"  ✓ Success!")
            successful.append(video)
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:100]}")
            failed.append({
                'video': video,
                'error': str(e)
            })
    
    return successful, failed

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("TAWANCHAI TRANSCRIPT DOWNLOADER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Find the most recent high-value videos file
    results_dir = Path('tawanchai_search_results')
    
    if not results_dir.exists():
        print(f"Error: Directory '{results_dir}' not found!")
        print("Please run search_tawanchai_videos.py first.")
        return
    
    # Find the most recent high_value file
    high_value_files = sorted(results_dir.glob('tawanchai_high_value_*.json'), reverse=True)
    
    if not high_value_files:
        print(f"Error: No high-value video files found in '{results_dir}'!")
        return
    
    latest_file = high_value_files[0]
    print(f"Loading high-value videos from: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"Found {len(videos)} high-value videos")
    print()
    
    # Create output directory for transcripts
    transcripts_dir = Path('tawanchai_transcripts')
    transcripts_dir.mkdir(exist_ok=True)
    
    print(f"Downloading transcripts to: {transcripts_dir}")
    print()
    
    # Download transcripts
    successful, failed = download_transcripts(videos, transcripts_dir)
    
    # Save results
    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"Successful: {len(successful)}/{len(videos)}")
    print(f"Failed: {len(failed)}/{len(videos)}")
    print()
    
    # Save successful downloads
    success_file = transcripts_dir / f'successful_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(success_file, 'w', encoding='utf-8') as f:
        json.dump(successful, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved successful downloads to: {success_file}")
    
    # Save failed downloads
    if failed:
        failed_file = transcripts_dir / f'failed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved failed downloads to: {failed_file}")
        
        print("\nFailed videos:")
        for item in failed:
            print(f"  - {item['video']['title'][:60]}")
            print(f"    Error: {item['error'][:100]}")
    
    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)

if __name__ == '__main__':
    main()
