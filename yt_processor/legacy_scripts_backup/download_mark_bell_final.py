#!/usr/bin/env python3
"""
Robust transcript downloader with Safe/Turbo modes.

Key goals:
- Avoid 429 rate limits by pacing requests (stagger + sleep_requests).
- Support cookies (recommended) and optional JS runtime hints.
- Offer Safe (10 workers) and Turbo (25 workers) presets.
- Keep compatibility with the existing mark_bell_filtered_list.txt format.
"""

import argparse
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import yt_dlp

DEFAULT_LIST = Path("yt_processor/mark_bell_filtered_list.txt")
DEFAULT_OUT = Path("yt_processor/downloads_final")

# Presets tuned from prior stress tests
PRESETS = {
    "safe": {"workers": 10, "sleep_requests": 1.0, "stagger": 1.5},
    "turbo": {"workers": 25, "sleep_requests": 0.35, "stagger": 0.5},
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def load_video_list(path: Path, start: int, end: Optional[int]) -> List[Tuple[str, str, str]]:
    videos: List[Tuple[str, str, str]] = []
    if not path.exists():
        raise FileNotFoundError(f"Video list not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if "\t" not in line:
                continue
            title, url, *_ = line.strip().split("\t")
            if "v=" not in url:
                continue
            vid = url.split("v=")[1].split("&")[0]
            videos.append((vid, url, title))
    end_idx = len(videos) if end is None else min(end, len(videos))
    return videos[start:end_idx]


def build_opts(output_dir: Path, cookies: Optional[Path], sleep_requests: float, js_runtime: Optional[str]) -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "skip_download": True,
        "write_auto_subs": True,
        "sub_langs": ["en"],
        "sub_format": "vtt",
        "convert_subs": "srt",
        "sleep_requests": sleep_requests,
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    if cookies and cookies.exists():
        opts["cookiefile"] = str(cookies)
    elif os.environ.get("YTDLP_COOKIES") and Path(os.environ["YTDLP_COOKIES"]).exists():
        opts["cookiefile"] = os.environ["YTDLP_COOKIES"]
    # JS runtime hint (optional; only if available on system)
    runtime = js_runtime or os.environ.get("YTDLP_JS_RUNTIME")
    if runtime:
        opts["js_runtimes"] = {runtime: {}}
    return opts


def download_one(video: Tuple[str, str, str], base_opts: Dict[str, Any], output_dir: Path, stagger: float, max_retries: int = 4) -> Tuple[str, bool, str]:
    vid, url, title = video
    attempt = 0
    while attempt < max_retries:
        jitter = random.random() * stagger
        time.sleep(jitter)
        try:
            opts = dict(base_opts)
            # Randomize UA slightly to avoid identical fingerprints
            opts["http_headers"] = dict(base_opts["http_headers"])
            opts["http_headers"]["User-Agent"] = USER_AGENT + f" rv={random.randint(1000,9999)}"
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            expected = output_dir / f"{vid}.en.srt"
            if expected.exists():
                return vid, True, "ok"
            return vid, False, "SRT missing after download"
        except Exception as e:  # pragma: no cover - network dependent
            msg = str(e)
            if "429" in msg or "Too Many Requests" in msg:
                wait = (2 ** attempt) + random.random()
                time.sleep(wait)
                attempt += 1
                continue
            return vid, False, msg
    return vid, False, "Max retries hit (likely rate limited)"


def run_batch(
    videos: List[Tuple[str, str, str]],
    output_dir: Path,
    workers: int,
    sleep_requests: float,
    stagger: float,
    cookies: Optional[Path],
    js_runtime: Optional[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    opts = build_opts(output_dir, cookies, sleep_requests, js_runtime)

    start = time.time()
    success = 0
    failed = 0

    print(f"Starting batch: {len(videos)} videos | workers={workers} | sleep_requests={sleep_requests}s | stagger={stagger}s")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download_one, v, opts, output_dir, stagger): v for v in videos}
        for fut in as_completed(futures):
            vid, ok, info = fut.result()
            if ok:
                success += 1
            else:
                failed += 1
                print(f"  [WARN] {vid} -> {info}")
    elapsed = time.time() - start
    rate = success / elapsed if elapsed else 0.0
    print("\n=== COMPLETE ===")
    print(f"Success: {success} | Failed: {failed} | Elapsed: {elapsed:.1f}s | Rate: {rate:.2f} vids/sec")
    print(f"Output: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rate-limit-aware transcript downloader")
    parser.add_argument("--mode", choices=list(PRESETS.keys()), default="safe", help="Preset worker/sleep settings")
    parser.add_argument("--workers", type=int, help="Override worker count")
    parser.add_argument("--sleep-requests", type=float, help="Override sleep between requests (seconds)")
    parser.add_argument("--stagger", type=float, help="Override per-task jitter (seconds)")
    parser.add_argument("--cookies", type=Path, help="Path to cookies.txt (recommended)")
    parser.add_argument("--js-runtime", type=str, help="JS runtime name (node, deno, quickjs) if installed")
    parser.add_argument("--list", type=Path, default=DEFAULT_LIST, help="Tab-separated video list file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT, help="Directory for transcripts")
    parser.add_argument("--start", type=int, default=0, help="Start index (0-based, inclusive)")
    parser.add_argument("--end", type=int, help="End index (0-based, exclusive)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preset = PRESETS[args.mode]
    workers = args.workers or preset["workers"]
    sleep_requests = args.sleep_requests or preset["sleep_requests"]
    stagger = args.stagger or preset["stagger"]

    videos = load_video_list(args.list, args.start, args.end)
    if not videos:
        print("No videos found in the specified range.")
        return

    run_batch(
        videos=videos,
        output_dir=args.output,
        workers=workers,
        sleep_requests=sleep_requests,
        stagger=stagger,
        cookies=args.cookies,
        js_runtime=args.js_runtime,
    )


if __name__ == "__main__":
    main()
