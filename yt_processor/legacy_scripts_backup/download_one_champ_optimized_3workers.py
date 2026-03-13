#!/usr/bin/env python3
"""
3-Worker Optimized Downloader for ONE Championship
Cautious speed ramp-up: 3 workers, 5s delay between tasks
"""

import json
import time
import yt_dlp
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def download_video(video, output_dir):
    """Download video transcript using yt-dlp"""
    video_id = video['video_id']
    url = video['url']
    title = video.get('title', 'Unknown')
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'subtitlesformat': 'vtt',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check if VTT file exists
        vtt_files = list(output_dir.glob(f'{video_id}.*.vtt'))
        if vtt_files:
            return {'status': 'success', 'video': video, 'file': str(vtt_files[0])}
        else:
            return {'status': 'no_subs', 'video': video, 'error': 'No subtitle file found'}
            
    except Exception as e:
        return {'status': 'failed', 'video': video, 'error': str(e)}

def main():
    print("=" * 80)
    print("3-WORKER OPTIMIZED DOWNLOADER")
    print("=" * 80)
    print("Configuration:")
    print("  - Workers: 3")
    print("  - Rate Limit: 5s delay between tasks")
    print("  - Catalog: ONE Championship Final Instructional")
    print()
    
    # Load catalog
    catalog_file = Path('one_championship_search_results/final_instructional_catalog_20260108_022119.json')
    with open(catalog_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    # Filter out already downloaded videos
    output_dir = Path('one_championship_transcripts')
    output_dir.mkdir(exist_ok=True)
    
    existing_files = list(output_dir.glob('*.md'))
    existing_ids = {f.stem for f in existing_files}
    
    videos_to_download = [v for v in videos if v['video_id'] not in existing_ids]
    
    print(f"Total videos: {len(videos)}")
    print(f"Already downloaded: {len(existing_ids)}")
    print(f"Remaining to download: {len(videos_to_download)}")
    print()
    
    if not videos_to_download:
        print("All videos already downloaded!")
        return

    # Start downloading
    start_time = time.time()
    successful = 0
    failed = 0
    
    print(f"Starting processing with 3 workers...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit tasks with a delay to ramp up cautiously
        futures = []
        for i, video in enumerate(videos_to_download):
            if i > 0 and i % 3 == 0:
                time.sleep(5)  # 5s delay every 3 videos (batch delay)
            
            future = executor.submit(download_video, video, output_dir)
            futures.append(future)
            print(f"  + Queued: {video['title'][:40]}...")
        
        print("\nWaiting for results...")
        
        for future in as_completed(futures):
            result = future.result()
            video_title = result['video'].get('title', 'Unknown')[:40]
            
            if result['status'] == 'success':
                print(f"  ✓ DONE: {video_title}")
                successful += 1
            elif result['status'] == 'no_subs':
                print(f"  ⚠ NO SUBS: {video_title}")
                failed += 1
            else:
                print(f"  ✗ FAILED: {video_title} - {result.get('error')}")
                failed += 1

    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print("BATCH COMPLETE")
    print("=" * 80)
    print(f"Time: {total_time:.2f}s")
    print(f"Speed: {len(videos_to_download) / total_time:.2f} videos/sec")
    print(f"Success: {successful}")
    print(f"Failed: {failed}")

if __name__ == '__main__':
    main()
