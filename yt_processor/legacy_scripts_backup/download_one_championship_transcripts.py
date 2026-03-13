#!/usr/bin/env python3
"""
Download Transcripts from ONE Championship Final Catalog
Downloads all 222 instructional videos with rate limiting and VTT-to-SRT conversion
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
import yt_dlp

def convert_vtt_to_srt(vtt_content):
    """Convert VTT subtitle format to SRT format"""
    
    lines = vtt_content.split('\n')
    srt_lines = []
    counter = 1
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and WEBVTT header
        if not line or line == 'WEBVTT':
            i += 1
            continue
        
        # Look for timestamp line (format: 00:00:00.000 --> 00:00:00.000)
        if '-->' in line:
            # Convert VTT timestamp to SRT format (replace . with ,)
            srt_timestamp = line.replace('.', ',')
            
            # Add subtitle number
            srt_lines.append(str(counter))
            counter += 1
            
            # Add timestamp
            srt_lines.append(srt_timestamp)
            
            # Add subtitle text (next lines until empty line or next timestamp)
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line or '-->' in next_line:
                    break
                # Remove VTT formatting tags
                clean_line = next_line.replace('<c.', '').replace('</c>', '').replace('<', '[').replace('>', ']')
                srt_lines.append(clean_line)
                i += 1
            
            # Add empty line between subtitles
            srt_lines.append('')
        else:
            i += 1
    
    return '\n'.join(srt_lines)

def download_transcripts_with_retry(video_list, output_dir, max_retries=3, sleep_between=3):
    """Download transcripts with retry logic and rate limiting"""
    
    results = {
        'success': [],
        'failed': [],
        'no_subtitle': []
    }
    
    for i, video in enumerate(video_list, 1):
        video_id = video.get('video_id')
        title = video.get('title', 'Unknown')
        url = video.get('url')
        
        print(f"[{i}/{len(video_list)}] Downloading: {title[:60]}...")
        
        # Create safe filename
        safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:100]  # Limit length
        
        for attempt in range(max_retries):
            try:
                ydl_opts = {
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en', 'en-US', 'en-GB'],
                    'subtitlesformat': 'vtt',
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': str(output_dir / f'{safe_title}.%(ext)s'),
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    # Check if subtitles are available
                    subtitles = info.get('subtitles', {})
                    auto_captions = info.get('automatic_captions', {})
                    
                    if not subtitles and not auto_captions:
                        print(f"  ✗ No subtitles available")
                        results['no_subtitle'].append(video)
                        break
                    
                    # Download subtitles
                    ydl.download([url])
                    
                    # Find and convert VTT to SRT
                    vtt_files = list(output_dir.glob(f'{safe_title}*.vtt'))
                    
                    if vtt_files:
                        vtt_file = vtt_files[0]
                        srt_file = output_dir / f'{safe_title}.srt'
                        
                        # Read VTT and convert to SRT
                        with open(vtt_file, 'r', encoding='utf-8') as f:
                            vtt_content = f.read()
                        
                        srt_content = convert_vtt_to_srt(vtt_content)
                        
                        with open(srt_file, 'w', encoding='utf-8') as f:
                            f.write(srt_content)
                        
                        # Delete VTT file
                        vtt_file.unlink()
                        
                        print(f"  ✓ Downloaded and converted to SRT")
                        results['success'].append({
                            'video_id': video_id,
                            'title': title,
                            'url': url,
                            'srt_file': str(srt_file)
                        })
                    else:
                        print(f"  ✗ Failed to download subtitle file")
                        results['failed'].append(video)
                    
                    break  # Success, don't retry
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = sleep_between * (attempt + 1)  # Exponential backoff
                    print(f"  ✗ Error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  ✗ Failed after {max_retries} attempts: {e}")
                    results['failed'].append(video)
        
        # Rate limiting between videos
        if i < len(video_list):
            time.sleep(sleep_between)
    
    return results

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("ONE CHAMPIONSHIP TRANSCRIPT DOWNLOADER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load final catalog
    results_dir = Path('one_championship_search_results')
    catalog_file = results_dir / 'final_instructional_catalog_20260108_022119.json'
    
    with open(catalog_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"Loaded {len(videos)} videos from catalog")
    print()
    
    # Create output directory for transcripts
    transcript_dir = Path('one_championship_transcripts')
    transcript_dir.mkdir(exist_ok=True)
    
    print(f"Output directory: {transcript_dir}")
    print()
    print("Starting transcript download...")
    print("This may take a while (rate limiting: 3s between videos)")
    print()
    
    # Download transcripts
    results = download_transcripts_with_retry(videos, transcript_dir, max_retries=3, sleep_between=3)
    
    # Save results
    results_file = transcript_dir / f'download_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE!")
    print("=" * 80)
    print()
    print(f"✓ Successfully downloaded: {len(results['success'])} videos")
    print(f"✗ Failed: {len(results['failed'])} videos")
    print(f"✗ No subtitles available: {len(results['no_subtitle'])} videos")
    print()
    print(f"Results saved to: {results_file}")
    print(f"Transcripts saved to: {transcript_dir}")
    print()
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
