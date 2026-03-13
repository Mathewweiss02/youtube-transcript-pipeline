#!/usr/bin/env python3
"""
Universal parallel transcript downloader.

Supports two input modes:
- `--input-file`: a TSV file with `title<TAB>url`
- `--channel-url`: a YouTube channel/handle URL

If no arguments are provided, it falls back to the legacy Hyperarch defaults so
existing ad-hoc usage still works.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from collection_utils import URL_RE, YT_DLP_PATH, fetch_channel_videos
from universal_chunker import chunk_transcripts, derive_default_base_name, derive_default_output_dir


DEFAULT_INPUT_FILE = Path("hyperarch_formatted.txt")
DEFAULT_OUTPUT_DIR = Path("../transcripts/Hyperarch_Fascia_Raw")
DEFAULT_WORKERS = 10
TEMP_PREFIX = "__tmp_transcript__"
VIDEO_ID_FILENAME_RE = re.compile(r"^[A-Za-z0-9_-]{11}\.md$")


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def clean_vtt_file(vtt_path: Path) -> str:
    """Parse a VTT file and extract clean transcript text."""
    with open(vtt_path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()

    cleaned_lines = []
    seen = set()

    for line in lines:
        line = line.strip()

        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if "-->" in line or line.isdigit() or line == "[Music]":
            continue

        line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line)
        line = re.sub(r"</?c>", "", line)

        if line and line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def extract_video_id(url: str) -> str:
    watch_match = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
    if watch_match:
        return watch_match.group(1)

    short_match = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if short_match:
        return short_match.group(1)

    return ""


def slugify_channel_name(channel_url: str) -> str:
    handle_match = re.search(r"youtube\.com/@([^/\s]+)", channel_url, re.IGNORECASE)
    if handle_match:
        raw = handle_match.group(1)
    else:
        raw = channel_url.rstrip("/").split("/")[-1] or "channel"

    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")
    return cleaned or "channel"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download YouTube transcripts in parallel.")
    parser.add_argument("--input-file", type=Path, help="TSV file with title<TAB>url")
    parser.add_argument("--channel-url", help="YouTube channel URL, handle URL, or /channel/ URL")
    parser.add_argument("--output-dir", type=Path, help="Directory to write raw transcript markdown files")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Parallel worker count")
    parser.add_argument("--limit", type=int, default=0, help="Optional max videos to process from a channel")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Redownload videos even when a final .md transcript already exists",
    )
    parser.add_argument(
        "--sync-chunks",
        action="store_true",
        help="After downloading, rebuild merged PART files from the raw transcript folder",
    )
    return parser.parse_args()


def resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return args.output_dir

    if args.channel_url:
        channel_slug = slugify_channel_name(args.channel_url)
        return Path("../transcripts") / f"{channel_slug}_Raw"

    return DEFAULT_OUTPUT_DIR


def load_videos_from_file(input_file: Path) -> list[tuple[str, str]]:
    videos: list[tuple[str, str]] = []

    with open(input_file, "r", encoding="utf-8") as handle:
        for line in handle:
            if "\t" not in line:
                continue

            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue

            title = parts[0].strip()
            url = parts[1].strip()
            video_id = extract_video_id(url)
            if not title or not video_id:
                continue

            videos.append((title, url))

    return videos


def load_videos_from_channel(channel_url: str, limit: int) -> list[tuple[str, str]]:
    channel_videos = fetch_channel_videos(channel_url)
    if limit > 0:
        channel_videos = channel_videos[:limit]

    return [(video["title"], video["url"]) for video in channel_videos]


def cleanup_temp_files(output_dir: Path, video_id: str):
    for path in output_dir.glob(f"{TEMP_PREFIX}{video_id}*"):
        try:
            path.unlink()
        except Exception:
            pass


def discover_existing_transcripts(output_dir: Path) -> dict[str, Path]:
    """Index existing raw transcripts by video ID from filename or embedded URL."""
    existing: dict[str, Path] = {}

    for path in sorted(output_dir.glob("*.md")):
        if not path.is_file():
            continue

        if VIDEO_ID_FILENAME_RE.match(path.name):
            existing.setdefault(path.stem, path)
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        match = URL_RE.search(text)
        if match:
            existing.setdefault(match.group(1), path)

    return existing


def download_video(
    video_data: tuple[str, str],
    output_dir: Path,
    overwrite: bool,
    existing_transcripts: dict[str, Path] | None = None,
) -> tuple[str, str, str]:
    title, url = video_data
    video_id = extract_video_id(url)
    if not video_id:
        return (title, "ERROR", "Invalid YouTube URL")

    final_md_path = output_dir / f"{video_id}.md"
    existing_path = None
    if existing_transcripts:
        existing_path = existing_transcripts.get(video_id)
    if not existing_path and final_md_path.exists():
        existing_path = final_md_path

    if existing_path and not overwrite:
        return (title, "SKIPPED", existing_path.name)

    cleanup_temp_files(output_dir, video_id)

    temp_template = output_dir / f"{TEMP_PREFIX}{video_id}.%(ext)s"
    cmd = [
        YT_DLP_PATH,
        "--write-auto-sub",
        "--sub-langs",
        "en",
        "--skip-download",
        "--no-warnings",
        "-o",
        str(temp_template),
        url,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        cleanup_temp_files(output_dir, video_id)
        return (title, "TIMEOUT", "yt-dlp timed out")
    except subprocess.CalledProcessError as exc:
        cleanup_temp_files(output_dir, video_id)
        message = (exc.stderr or exc.stdout or "yt-dlp failed").strip().splitlines()[:1]
        return (title, "FAILED", message[0] if message else "yt-dlp failed")

    vtt_files = list(output_dir.glob(f"{TEMP_PREFIX}{video_id}*.vtt"))
    if not vtt_files:
        cleanup_temp_files(output_dir, video_id)
        return (title, "NO_SUBS", "No English auto-subs available")

    try:
        cleaned_text = clean_vtt_file(vtt_files[0])
        if not cleaned_text:
            cleanup_temp_files(output_dir, video_id)
            return (title, "EMPTY", "Transcript cleaned to empty text")

        temp_md_path = output_dir / f"{TEMP_PREFIX}{video_id}.md"
        with open(temp_md_path, "w", encoding="utf-8") as handle:
            handle.write(f"# {title}\n\n")
            handle.write(f"URL: {url}\n\n")
            handle.write("---\n\n")
            handle.write(cleaned_text)
            handle.write("\n")

        temp_md_path.replace(final_md_path)
        cleanup_temp_files(output_dir, video_id)
        return (title, "SUCCESS", final_md_path.name)
    except Exception as exc:
        cleanup_temp_files(output_dir, video_id)
        return (title, "ERROR", str(exc)[:120])


def main():
    args = parse_args()
    input_file = args.input_file or DEFAULT_INPUT_FILE
    output_dir = resolve_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("UNIVERSAL PARALLEL TRANSCRIPT DOWNLOADER")
    print("=" * 80)
    print(f"Using yt-dlp: {YT_DLP_PATH}")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Workers: {args.workers}")

    if args.channel_url:
        print(f"Mode: channel URL -> {args.channel_url}")
        videos = load_videos_from_channel(args.channel_url, args.limit)
    else:
        print(f"Mode: input file -> {input_file}")
        if not input_file.exists():
            print(f"\nFile not found: {input_file}")
            print("Expected format: title<TAB>url")
            return
        videos = load_videos_from_file(input_file)

    if not videos:
        print("\nNo videos found to process.")
        return

    existing_transcripts = discover_existing_transcripts(output_dir)
    print(f"Loaded {len(videos)} videos")
    if existing_transcripts:
        print(f"Indexed {len(existing_transcripts)} existing transcripts for duplicate prevention")
    print()

    successful = []
    skipped = []
    failed = []

    started_at = time.time()
    with ThreadPoolExecutor(max_workers=max(args.workers, 1)) as executor:
        futures = {
            executor.submit(download_video, video, output_dir, args.overwrite, existing_transcripts): video
            for video in videos
        }

        for index, future in enumerate(as_completed(futures), start=1):
            title, status, message = future.result()

            if status == "SUCCESS":
                print(f"[{index}/{len(videos)}] OK      {title[:55]} -> {message}")
                successful.append(title)
            elif status == "SKIPPED":
                print(f"[{index}/{len(videos)}] SKIPPED {title[:55]} -> {message}")
                skipped.append(title)
            else:
                print(f"[{index}/{len(videos)}] FAILED  {title[:55]} -> {status}")
                failed.append((title, status, message))

    elapsed = time.time() - started_at

    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"Successful: {len(successful)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Failed: {len(failed)}")
    print(f"Time: {elapsed:.1f}s")

    if failed:
        print("\nFailed videos:")
        for title, status, message in failed[:15]:
            print(f"  - {title[:55]} ({status}: {message})")
        if len(failed) > 15:
            print(f"  ... and {len(failed) - 15} more")

    if args.sync_chunks and (successful or (not failed and skipped)):
        chunk_output_dir = derive_default_output_dir(output_dir)
        chunk_base_name = derive_default_base_name(output_dir)
        print()
        print("=" * 80)
        print("SYNCING CHUNKS")
        print("=" * 80)
        print(f"Raw input: {output_dir.resolve()}")
        print(f"Chunk output: {chunk_output_dir.resolve()}")
        print(f"Base name: {chunk_base_name}")

        try:
            chunk_result = chunk_transcripts(
                input_dir=output_dir,
                output_dir=chunk_output_dir,
                base_name=chunk_base_name,
                sort_mode="mtime",
                replace_existing=True,
            )
            print(
                f"Chunk sync complete: {len(chunk_result['written_paths'])} files written"
                + (
                    f", {len(chunk_result['deleted_files'])} old chunk files deleted"
                    if chunk_result["deleted_files"]
                    else ""
                )
            )
        except Exception as exc:
            print(f"Chunk sync failed: {exc}")


if __name__ == "__main__":
    main()
