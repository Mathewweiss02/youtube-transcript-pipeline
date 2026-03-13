#!/usr/bin/env python3
"""
Benchmark youtube-transcript-api vs yt-dlp for maximum download speed.
Tests if a lightweight API-only approach can outperform the full yt-dlp process.
"""
import os
import time
import json
import statistics
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass, asdict
from youtube_transcript_api import YouTubeTranscriptApi
import concurrent.futures

@dataclass
class ComparisonMetrics:
    video_id: str
    yta_time: float
    ytdlp_time: float
    yta_success: bool
    ytdlp_success: bool
    yta_words: int
    ytdlp_words: int

class SpeedResearchBenchmark:
    def __init__(self, yt_dlp_path: str, output_dir: Path):
        self.yt_dlp_path = yt_dlp_path
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def download_with_yta(self, video_id: str) -> Tuple[float, bool, int]:
        """Download using youtube-transcript-api."""
        start = time.time()
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([entry['text'] for entry in transcript])
            word_count = len(text.split())
            return time.time() - start, True, word_count
        except Exception:
            try:
                # Try auto-generated
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_generated_transcript(['en']).fetch()
                text = " ".join([entry['text'] for entry in transcript])
                word_count = len(text.split())
                return time.time() - start, True, word_count
            except Exception:
                return time.time() - start, False, 0

    def download_with_ytdlp(self, video_url: str, video_id: str) -> Tuple[float, bool, int]:
        """Download using yt-dlp (single process)."""
        import subprocess
        start = time.time()
        try:
            cmd = [
                'python', '-m', 'yt_dlp',
                '--skip-download',
                '--write-auto-subs',
                '--sub-langs', 'en',
                '--sub-format', 'vtt',
                '--convert-subs', 'srt',
                '--output', str(self.output_dir / f"bench_{video_id}.%(ext)s"),
                video_url
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)
            srt_file = self.output_dir / f"bench_{video_id}.en.srt"
            if srt_file.exists():
                with open(srt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # Simplified word count
                words = len(content.split())
                return time.time() - start, True, words
            return time.time() - start, False, 0
        except Exception:
            return time.time() - start, False, 0

    def run_comparison(self, videos: List[Tuple[str, str]], sample_size: int = 5):
        print(f"\n{'='*80}")
        print(f"SPEED RESEARCH: youtube-transcript-api vs yt-dlp")
        print(f"{'='*80}\n")
        
        results = []
        for i, (video_id, url) in enumerate(videos[:sample_size], 1):
            print(f"[{i}/{sample_size}] Researching {video_id}...")
            
            yta_time, yta_success, yta_words = self.download_with_yta(video_id)
            print(f"  → youtube-transcript-api: {yta_time:.2f}s ({'✅' if yta_success else '❌'})")
            
            ytdlp_time, ytdlp_success, ytdlp_words = self.download_with_ytdlp(url, video_id)
            print(f"  → yt-dlp: {ytdlp_time:.2f}s ({'✅' if ytdlp_success else '❌'})")
            
            results.append(ComparisonMetrics(
                video_id=video_id,
                yta_time=yta_time,
                ytdlp_time=ytdlp_time,
                yta_success=yta_success,
                ytdlp_success=ytdlp_success,
                yta_words=yta_words,
                ytdlp_words=ytdlp_words
            ))
            
        return results

def main():
    BASE_DIR = Path(r'C:\Users\aweis\Downloads\YouTube_Tools_Scripts\yt_processor')
    input_file = BASE_DIR / 'mark_bell_filtered_list.txt'
    
    videos = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '\t' in line:
                title, url = line.strip().split('\t', 1)
                video_id = url.split('v=')[1].split('&')[0] if 'v=' in url else None
                if video_id:
                    videos.append((video_id, url))
    
    output_dir = BASE_DIR / 'research_downloads'
    benchmark = SpeedResearchBenchmark('python -m yt_dlp', output_dir)
    
    # Run a small comparison to see the potential speedup
    comparison_results = benchmark.run_comparison(videos, sample_size=5)
    
    # Calculate summary
    yta_times = [r.yta_time for r in comparison_results if r.yta_success]
    ytdlp_times = [r.ytdlp_time for r in comparison_results if r.ytdlp_success]
    
    if yta_times and ytdlp_times:
        avg_yta = statistics.mean(yta_times)
        avg_ytdlp = statistics.mean(ytdlp_times)
        speedup = avg_ytdlp / avg_yta
        
        print(f"\n{'='*80}")
        print(f"RESEARCH FINDINGS")
        print(f"{'='*80}")
        print(f"Average youtube-transcript-api time: {avg_yta:.2f}s")
        print(f"Average yt-dlp time: {avg_ytdlp:.2f}s")
        print(f"Potential Speedup: {speedup:.1f}x faster")
        print(f"{'='*80}\n")
        
        if speedup > 2:
            print("🚀 MASSIVE SPEEDUP DETECTED!")
            print("The youtube-transcript-api approach is significantly faster because it bypasses")
            print("the heavy overhead of spawning a full yt-dlp process and negotiating formats.")
    else:
        print("\nCould not complete comparison due to failures.")

if __name__ == "__main__":
    main()
