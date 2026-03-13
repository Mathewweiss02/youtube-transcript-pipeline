#!/usr/bin/env python3
"""
Improved Transcript Downloader with Rate Limiting and VTT-to-SRT Conversion
Based on yt-dlp best practices from Context7 documentation
Works with Tawanchai and ONE Championship catalogs
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
import yt_dlp

def download_transcripts_with_retry(video_list, output_dir, max_retries=3, sleep_between=5):
    """
    Download transcripts with rate limiting and retry logic
    
    Args:
        video_list: List of video dictionaries
        output_dir: Directory to save transcripts
        max_retries: Maximum retry attempts for failed downloads
        sleep_between: Seconds to sleep between downloads (rate limiting)
    
    Returns:
        Tuple of (successful, failed) lists
    """
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'skip_download': True,
        'quiet': False,
        'no_warnings': False,
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'subtitlesformat': 'vtt',
        # Add rate limiting
        'sleep_interval': sleep_between,
        # Retry configuration
        'retries': max_retries,
        'fragment_retries': max_retries,
    }
    
    successful = []
    failed = []
    
    for i, video in enumerate(video_list, 1):
        video_id = video['video_id']
        url = video['url']
        title = video['title'][:50] + '...' if len(video['title']) > 50 else video['title']
        
        print(f"\n[{i}/{len(video_list)}] Downloading transcript for: {title}")
        print(f"  URL: {url}")
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"  Retry attempt {attempt + 1}/{max_retries}...")
                    # Exponential backoff
                    wait_time = sleep_between * (2 ** attempt)
                    print(f"  Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                print(f"  ✓ Success!")
                successful.append(video)
                break  # Success, exit retry loop
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if '429' in error_msg or 'Too Many Requests' in error_msg:
                    print(f"  ✗ Rate limited (HTTP 429)")
                    if attempt < max_retries - 1:
                        wait_time = sleep_between * (2 ** (attempt + 1))
                        print(f"  Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ✗ Failed after {max_retries} attempts: Rate limit")
                        failed.append({
                            'video': video,
                            'error': error_msg,
                            'attempts': attempt + 1
                        })
                        break
                else:
                    print(f"  ✗ Failed: {error_msg[:100]}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        failed.append({
                            'video': video,
                            'error': error_msg,
                            'attempts': attempt + 1
                        })
                        break
        
        # Sleep between successful downloads to avoid rate limiting
        if i < len(video_list):
            print(f"  Sleeping {sleep_between} seconds to avoid rate limiting...")
            time.sleep(sleep_between)
    
    return successful, failed

def convert_vtt_to_srt(vtt_file, srt_file):
    """
    Convert VTT subtitle file to SRT format
    
    Args:
        vtt_file: Path to VTT file
        srt_file: Path to output SRT file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import re
        
        with open(vtt_file, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
        
        # Remove VTT header
        vtt_content = re.sub(r'WEBVTT.*?\n\n', '', vtt_content, flags=re.DOTALL)
        
        # Convert timestamps from VTT format (00:00:00.000) to SRT format (00:00:00,000)
        vtt_content = re.sub(r'(\d{2}:\d{2}:\d{2})\.(\d{3})', r'\1,\2', vtt_content)
        
        # Add SRT numbering
        lines = vtt_content.strip().split('\n\n')
        srt_content = ''
        
        for i, block in enumerate(lines, 1):
            if block.strip():
                srt_content += f"{i}\n{block}\n\n"
        
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        return True
        
    except Exception as e:
        print(f"    Error converting VTT to SRT: {e}")
        return False

def convert_all_vtt_to_srt(transcripts_dir):
    """
    Convert all VTT files in a directory to SRT format
    
    Args:
        transcripts_dir: Directory containing VTT files
    
    Returns:
        Tuple of (converted_count, failed_count)
    """
    
    vtt_files = list(transcripts_dir.glob('*.vtt'))
    converted = 0
    failed = 0
    
    print(f"\nConverting {len(vtt_files)} VTT files to SRT format...")
    
    for vtt_file in vtt_files:
        srt_file = vtt_file.with_suffix('.srt')
        
        if convert_vtt_to_srt(vtt_file, srt_file):
            print(f"  ✓ Converted: {vtt_file.name} → {srt_file.name}")
            converted += 1
        else:
            print(f"  ✗ Failed: {vtt_file.name}")
            failed += 1
    
    return converted, failed

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("IMPROVED TAWANCHAI TRANSCRIPT DOWNLOADER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Detect which catalog to use
    one_champ_catalog = Path('one_championship_search_results/final_instructional_catalog_20260108_022119.json')
    tawanchai_catalog = Path('tawanchai_search_results_ultimate/tawanchai_high_value_ultimate_20260108_011707.json')
    
    catalog_file = None
    catalog_name = ""
    
    if one_champ_catalog.exists():
        catalog_file = one_champ_catalog
        catalog_name = "ONE Championship"
    elif tawanchai_catalog.exists():
        catalog_file = tawanchai_catalog
        catalog_name = "Tawanchai"
    else:
        print("ERROR: No catalog file found!")
        print("Looking for:")
        print(f"  - {one_champ_catalog}")
        print(f"  - {tawanchai_catalog}")
        sys.exit(1)
    
    print(f"Using catalog: {catalog_name}")
    print(f"File: {catalog_file}")
    print()
    
    # Load catalog
    with open(catalog_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"Loaded {len(videos)} videos from catalog")
    print()
    
    # Create output directory
    if catalog_name == "ONE Championship":
        output_dir = Path('one_championship_transcripts')
    else:
        output_dir = Path('tawanchai_transcripts')
    
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()
    
    # Download transcripts
    print("Starting transcript download...")
    print(f"Rate limiting: 5s between videos")
    print(f"Max retries: 3")
    print()
    
    successful, failed = download_transcripts_with_retry(
        videos, 
        output_dir, 
        max_retries=3, 
        sleep_between=5
    )
    
    # Save results
    results = {
        'catalog': catalog_name,
        'total_videos': len(videos),
        'successful': len(successful),
        'failed': len(failed),
        'successful_videos': successful,
        'failed_videos': failed,
        'timestamp': datetime.now().isoformat()
    }
    
    results_file = output_dir / f'download_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
        failed_file = transcripts_dir / f'failed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved failed downloads to: {failed_file}")
        
        print("\nFailed videos:")
        for item in failed:
            print(f"  - {item['video']['title'][:60]}")
            print(f"    Error: {item['error'][:100]}")
            print(f"    Attempts: {item['attempts']}")
    
    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review downloaded transcripts in:", transcripts_dir)
    print("2. SRT files are ready for text extraction and cleaning")
    print("3. Use existing transcript processing tools to clean and merge")
    print("4. Create structured documentation from the transcripts")

if __name__ == '__main__':
    main()
