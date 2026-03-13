#!/usr/bin/env python3
"""
Production YouTube Transcript Downloader
Based on proven patterns from GitHub repos
- 10-12 workers (sustainable sweet spot)
- Chunked processing with delays
- Exponential backoff for retries
- Comprehensive error handling
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional
import json
from datetime import datetime
import sys

# Configuration
BASE_DIR = Path("C:/Users/aweis/Downloads/YouTube_Tools_Scripts/yt_processor")
INPUT_FILE = BASE_DIR / "mark_bell_filtered_list.txt"
OUTPUT_DIR = BASE_DIR / "transcripts"
STATE_FILE = BASE_DIR / "download_state.json"

# Proven settings from GitHub repos
MAX_WORKERS = 12  # Sweet spot from multiple repos
CHUNK_SIZE = 10   # Process in small chunks
DELAY_BETWEEN_CHUNKS = 2  # Seconds between chunks
MAX_RETRIES = 3   # From common implementations
BASE_DELAY = 1.5  # Base delay between requests (seconds)

class TranscriptDownloader:
    """Production-ready transcript downloader based on GitHub patterns"""

    def __init__(self, output_dir: Path, max_workers: int = MAX_WORKERS):
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ytt_api = YouTubeTranscriptApi()

    def download_transcript(
        self,
        video_info: Tuple[str, str, str],
        retry_count: int = 0
    ) -> Tuple[str, bool, str]:
        """
        Download transcript with retry logic and rate limiting
        Based on patterns from jkawamoto/mcp-youtube-transcript
        """
        video_id, url, title = video_info

        # Rate limiting delay (from GitHub patterns)
        time.sleep(BASE_DELAY + random.uniform(0, 0.5))

        try:
            # Get transcript using new API
            transcript = self.ytt_api.fetch(video_id, languages=['en'])

            # Convert to raw data format
            transcript_data = transcript.to_raw_data()

            # Convert to SRT format
            srt_content = self._format_to_srt(transcript_data)

            # Save to file
            output_file = self.output_dir / f"{video_id}.srt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)

            return video_id, True, f"{len(transcript_data)} segments"

        except TranscriptsDisabled:
            return video_id, False, "Transcripts disabled"
        except NoTranscriptFound:
            return video_id, False, "No transcript available"
        except VideoUnavailable:
            return video_id, False, "Video unavailable"
        except Exception as e:
            error_str = str(e)

            # Handle rate limiting with exponential backoff
            if "429" in error_str or "Too Many Requests" in error_str:
                if retry_count < MAX_RETRIES:
                    wait_time = (2 ** retry_count) * BASE_DELAY
                    print(f"    ⚠️  Rate limited, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    return self.download_transcript(video_info, retry_count + 1)
                return video_id, False, "Rate limited (max retries)"

            # Other errors
            return video_id, False, error_str[:80]

    def _format_to_srt(self, transcript_data: List[dict]) -> str:
        """Format transcript data to SRT format"""
        srt_content = ""
        for i, entry in enumerate(transcript_data, 1):
            start = self._format_time(entry['start'])
            duration = entry.get('duration', 0)
            end = self._format_time(entry['start'] + duration)
            srt_content += f"{i}\n{start} --> {end}\n{entry['text']}\n\n"
        return srt_content

    def _format_time(self, seconds: float) -> str:
        """Format seconds to SRT time format"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def download_batch(
        self,
        videos: List[Tuple[str, str, str]],
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        Download a batch of videos with chunked processing
        Based on patterns from multiple GitHub repos
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'videos_processed': 0,
            'start_time': time.time()
        }

        # Process in chunks to avoid overwhelming the API
        chunks = [videos[i:i+CHUNK_SIZE] for i in range(0, len(videos), CHUNK_SIZE)]

        for chunk_num, chunk in enumerate(chunks, 1):
            print(f"\n  Processing chunk {chunk_num}/{len(chunks)} ({len(chunk)} videos)...")

            # Download with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_video = {
                    executor.submit(self.download_transcript, video): video
                    for video in chunk
                }

                for future in as_completed(future_to_video):
                    video_id, url, title = future_to_video[future]
                    try:
                        vid_id, success, result = future.result()

                        if success:
                            results['successful'] += 1
                            print(f"    ✅ {vid_id}: {result}")
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"{vid_id}: {result}")
                            print(f"    ❌ {vid_id}: {result}")

                        results['videos_processed'] += 1

                        # Progress callback
                        if progress_callback:
                            progress_callback(results)

                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"{video_id}: {str(e)}")
                        print(f"    ❌ {video_id}: Unexpected error - {str(e)}")

            # Pause between chunks (rate limiting)
            if chunk_num < len(chunks):
                print(f"    Pausing {DELAY_BETWEEN_CHUNKS}s to avoid rate limiting...")
                time.sleep(DELAY_BETWEEN_CHUNKS)

        results['duration'] = time.time() - results['start_time']
        return results

def load_videos(input_file: Path) -> List[Tuple[str, str, str]]:
    """Load videos from input file"""
    videos = []
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    title = parts[0]
                    url = parts[1]
                    if 'watch?v=' in url:
                        video_id = url.split('watch?v=')[1].split('&')[0]
                        videos.append((video_id, url, title))
    return videos

def save_state(state: dict, state_file: Path):
    """Save download state for resume capability"""
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def load_state(state_file: Path) -> dict:
    """Load download state"""
    if state_file.exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def main():
    """Main download function"""

    print("🚀 Production YouTube Transcript Downloader")
    print("   Based on proven patterns from GitHub repos")
    print("=" * 60)

    # Check if rate limited
    print("\n🔍 Checking if rate limit has cleared...")
    test_vid = "Q7vyPnq_m8o"
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(test_vid, languages=['en'])
        data = transcript.to_raw_data()
        print(f"✅ Rate limit cleared! Ready to download.")
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            print(f"\n❌ Still rate limited!")
            print(f"   Please wait 10 minutes and try again.")
            return
        else:
            print(f"⚠️  Different error: {e}")
            print(f"   Continuing anyway...")

    # Load videos
    videos = load_videos(INPUT_FILE)
    print(f"\n📹 Loaded {len(videos)} videos")

    # Check for existing state (resume capability)
    state = load_state(STATE_FILE)
    if state.get('completed_videos'):
        completed_ids = set(state['completed_videos'])
        videos = [v for v in videos if v[0] not in completed_ids]
        print(f"📋 Resuming: {len(videos)} videos remaining")

    # Initialize downloader
    downloader = TranscriptDownloader(OUTPUT_DIR, max_workers=MAX_WORKERS)

    # Progress callback
    def progress_callback(results):
        rate = results['successful'] / results['duration'] if results['duration'] > 0 else 0
        print(f"    Progress: {results['videos_processed']} | "
              f"✅ {results['successful']} | "
              f"❌ {results['failed']} | "
              f"Rate: {rate:.2f} vids/sec")

    # Download all videos
    print(f"\n🎬 Starting download with {MAX_WORKERS} workers...")
    print(f"   Processing in chunks of {CHUNK_SIZE} with {DELAY_BETWEEN_CHUNKS}s delays")
    print(f"   Max retries: {MAX_RETRIES} with exponential backoff\n")

    results = downloader.download_batch(videos, progress_callback)

    # Final summary
    print("\n" + "=" * 60)
    print("📊 DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Total videos processed: {results['videos_processed']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['successful']/results['videos_processed']*100:.1f}%")
    print(f"Total time: {results['duration']/60:.1f} minutes")
    print(f"Average rate: {results['successful']/results['duration']:.2f} videos/sec")
    print(f"\n📁 Output directory: {OUTPUT_DIR}")

    # Save state
    state['completed_videos'] = [v[0] for v in videos if (OUTPUT_DIR / f"{v[0]}.srt").exists()]
    state['last_run'] = datetime.now().isoformat()
    save_state(state, STATE_FILE)

    # Show errors if any
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors'][:10]:
            print(f"   - {error}")
        if len(results['errors']) > 10:
            print(f"   ... and {len(results['errors']) - 10} more")

if __name__ == "__main__":
    main()
