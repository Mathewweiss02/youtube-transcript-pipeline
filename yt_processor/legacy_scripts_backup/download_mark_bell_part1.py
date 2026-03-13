#!/usr/bin/env python3
"""
Download transcripts for FIRST HALF of Mark Bell filtered videos (videos 1-951).
Second half (952-1903) will be downloaded on another computer.
"""
import os
import sys
import subprocess
from pathlib import Path

def find_yt_dlp():
    """Find yt-dlp executable."""
    possible_paths = [
        r'C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt-dlp-2025.11.12\yt-dlp-2025.11.12\yt-dlp.exe',
        r'yt-dlp.exe',
        r'yt-dlp'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("yt-dlp.exe not found")

def download_transcript(video_url, output_dir, yt_dlp_exe):
    """Download and clean transcript for a single video."""
    try:
        # Download SRT
        cmd = [
            yt_dlp_exe,
            '--skip-download',
            '--write-auto-sub',
            '--sub-lang', 'en',
            '--sub-format', 'srt',
            '--output', str(output_dir / '%(id)s.%(ext)s'),
            video_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return None, f"Download failed: {result.stderr[:100]}"
        
        # Find the downloaded SRT file
        video_id = video_url.split('v=')[1].split('&')[0] if 'v=' in video_url else None
        if not video_id:
            return None, "Could not extract video ID"
        
        srt_file = output_dir / f"{video_id}.en.srt"
        if not srt_file.exists():
            return None, "SRT file not found after download"
        
        # Clean the transcript
        txt_file = output_dir / f"{video_id}.txt"
        with open(srt_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip timestamp lines and sequence numbers
            if not line or line.isdigit() or '-->' in line:
                continue
            cleaned_lines.append(line)
        
        # Write cleaned transcript
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_lines))
        
        # Get word count
        word_count = len(' '.join(cleaned_lines).split())
        
        return word_count, None
        
    except Exception as e:
        return None, str(e)

def main():
    BASE_DIR = Path(r'C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt_processor')
    input_file = BASE_DIR / 'mark_bell_filtered_list.txt'
    output_dir = BASE_DIR / 'downloads'
    output_dir.mkdir(exist_ok=True)
    
    # Find yt-dlp
    try:
        yt_dlp_exe = find_yt_dlp()
        print(f"Using yt-dlp: {yt_dlp_exe}\n")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Load videos
    videos = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '\t' in line:
                title, url = line.strip().split('\t', 1)
                videos.append((title, url))
    
    total_videos = len(videos)
    half_point = total_videos // 2
    
    # FIRST HALF ONLY (videos 1 to half_point)
    videos_to_download = videos[:half_point]
    
    print("="*80)
    print("MARK BELL TRANSCRIPT DOWNLOAD - PART 1 (FIRST HALF)")
    print("="*80)
    print(f"\nTotal filtered videos: {total_videos}")
    print(f"Downloading: Videos 1-{half_point} ({len(videos_to_download)} videos)")
    print(f"Remaining for Computer 2: Videos {half_point + 1}-{total_videos} ({total_videos - half_point} videos)")
    print(f"\nOutput directory: {output_dir}\n")
    
    # Download transcripts
    successful = 0
    failed = 0
    total_words = 0
    
    for i, (title, url) in enumerate(videos_to_download, 1):
        print(f"[{i}/{len(videos_to_download)}] {title[:60]}...")
        
        word_count, error = download_transcript(url, output_dir, yt_dlp_exe)
        
        if error:
            print(f"  ❌ FAILED: {error}")
            failed += 1
        else:
            print(f"  ✅ SUCCESS ({word_count:,} words)")
            successful += 1
            total_words += word_count
        
        # Progress update every 50 videos
        if i % 50 == 0:
            print(f"\n--- Progress: {i}/{len(videos_to_download)} ({i/len(videos_to_download)*100:.1f}%) ---")
            print(f"    Successful: {successful}, Failed: {failed}")
            print(f"    Total words so far: {total_words:,}\n")
    
    # Final summary
    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE - PART 1")
    print("="*80)
    print(f"\nTotal attempted: {len(videos_to_download)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(videos_to_download)*100:.1f}%")
    print(f"\nTotal words downloaded: {total_words:,}")
    print(f"Average words per video: {total_words//successful if successful else 0:,}")
    
    # Estimate bundles needed
    words_per_bundle = 400000
    bundles_needed = (total_words + words_per_bundle - 1) // words_per_bundle
    print(f"\nEstimated bundles needed (at 400k words each): {bundles_needed}")
    
    print(f"\n✅ Part 1 complete! Ready for Computer 2 to download videos {half_point + 1}-{total_videos}")

if __name__ == "__main__":
    main()
