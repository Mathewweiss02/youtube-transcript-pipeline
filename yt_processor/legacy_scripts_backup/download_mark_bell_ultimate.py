#!/usr/bin/env python3
"""
Ultimate Speed Transcript Downloader for Mark Bell Power Project.
Combines session-based API calls, parallel execution, and intelligent retry logic.
Goal: 5x-10x speedup over standard sequential methods.
"""
import os
import sys
import time
import json
import random
import requests
from pathlib import Path
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# List of common User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

class UltimateSpeedDownloader:
    def __init__(self, output_dir: Path, max_workers: int = 5):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.session = requests.Session()
        
    def _get_random_ua(self):
        return random.choice(USER_AGENTS)

    def fetch_transcript(self, video_id: str, retry_count: int = 3) -> Tuple[str, bool, Any]:
        """Fetch transcript with session reuse and retry logic."""
        for attempt in range(retry_count):
            try:
                # Set a fresh user-agent for each attempt if needed
                self.session.headers.update({"User-Agent": self._get_random_ua()})
                
                # Fetch transcript
                # Note: we use the API directly. It internally uses requests.
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                try:
                    # Prefer manual English
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                except NoTranscriptFound:
                    # Fallback to auto-generated English
                    transcript = transcript_list.find_generated_transcript(['en'])
                
                data = transcript.fetch()
                text = " ".join([entry['text'] for entry in data])
                
                # Save to file
                output_file = self.output_dir / f"{video_id}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                return video_id, True, len(text.split())
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + random.random()
                    time.sleep(wait_time)
                    continue
                return video_id, False, error_str
                
        return video_id, False, "Max retries exceeded (likely 429)"

    def run_batch(self, videos: List[Tuple[str, str, str]]):
        """Run download in parallel with controlled throughput."""
        print(f"\n{'='*80}")
        print(f"ULTIMATE SPEED DOWNLOADER - STARTING BATCH")
        print(f"Target: {len(videos)} videos | Workers: {self.max_workers}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        successful = 0
        failed = 0
        total_words = 0
        
        # Using a smaller chunk size to avoid overwhelming the API all at once
        chunk_size = 50
        for i in range(0, len(videos), chunk_size):
            chunk = videos[i:i+chunk_size]
            print(f"--- Processing chunk {i//chunk_size + 1} ({len(chunk)} videos) ---")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_video = {
                    executor.submit(self.fetch_transcript, vid_id): (vid_id, title)
                    for vid_id, url, title in chunk
                }
                
                for future in as_completed(future_to_video):
                    vid_id, title = future_to_video[future]
                    try:
                        vid_id, success, result = future.result()
                        if success:
                            successful += 1
                            total_words += result
                            # print(f"  ✅ {vid_id} - {result} words") # Too noisy for large batches
                        else:
                            failed += 1
                            print(f"  ❌ {vid_id} - {result}")
                    except Exception as e:
                        failed += 1
                        print(f"  ❌ {vid_id} - Unexpected error: {str(e)}")
            
            # Brief pause between chunks to let the API breathe
            time.sleep(2)
            
            elapsed = time.time() - start_time
            rate = successful / elapsed if elapsed > 0 else 0
            print(f"Progress: {successful+failed}/{len(videos)} | Success: {successful} | Failed: {failed} | Rate: {rate:.2f} vids/sec\n")

        total_time = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"ULTIMATE SPEED DOWNLOAD COMPLETE")
        print(f"{'='*80}")
        print(f"Total Time: {total_time/60:.1f} minutes")
        print(f"Final Success Rate: {successful/len(videos)*100:.1f}%")
        print(f"Total Words: {total_words:,}")
        print(f"Average Rate: {successful/total_time:.2f} videos/sec")
        print(f"Output Directory: {self.output_dir}")

def main():
    BASE_DIR = Path(r'C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt_processor')
    input_file = BASE_DIR / 'mark_bell_filtered_list.txt'
    output_dir = BASE_DIR / 'downloads_ultimate'
    
    # Load videos
    videos = []
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    title, url = parts[0], parts[1]
                    video_id = url.split('v=')[1].split('&')[0] if 'v=' in url else None
                    if video_id:
                        videos.append((video_id, url, title))
    
    # Filter for first half as per previous plan
    half_point = len(videos) // 2
    videos_to_download = videos[:half_point]
    
    # Initialize and run
    # Start with 3 workers to be safe, can push to 5+ if stable
    downloader = UltimateSpeedDownloader(output_dir, max_workers=3)
    downloader.run_batch(videos_to_download)

if __name__ == "__main__":
    main()
