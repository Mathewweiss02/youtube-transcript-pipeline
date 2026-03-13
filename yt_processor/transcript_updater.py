#!/usr/bin/env python3
"""Collection-first transcript updater for append-safe collections only."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from collection_utils import (
    MAX_CHUNK_SIZE,
    PENDING_PATH,
    REPO_ROOT,
    YT_DLP_PATH,
    load_collection_registry,
    load_json,
    resolve_collection_raw_dir,
    save_json,
)

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import re
import subprocess


WORKERS = 10


def clean_vtt_file(vtt_path: Path) -> str:
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

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

    return "\n".join(cleaned_lines)


def download_single_transcript(video_data: dict, output_dir: Path) -> dict:
    video_id = video_data["id"]
    title = video_data["title"]
    url = video_data["url"]

    for ext in [".en.vtt", ".vtt", ".md"]:
        path = output_dir / f"{video_id}{ext}"
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass

    for attempt in range(3):
        try:
            for part_file in output_dir.glob(f"{video_id}.*.part"):
                part_file.unlink()
            break
        except Exception:
            if attempt < 2:
                time.sleep(1)

    temp_template = output_dir / f"{video_id}.%(ext)s"
    cmd = [
        YT_DLP_PATH,
        "--write-auto-sub",
        "--sub-langs",
        "en",
        "--skip-download",
        "-o",
        str(temp_template),
        "--no-warnings",
        url,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {"id": video_id, "title": title, "status": "TIMEOUT", "file": None}
    except subprocess.CalledProcessError:
        return {"id": video_id, "title": title, "status": "FAILED", "file": None}

    vtt_files = list(output_dir.glob(f"{video_id}*.vtt"))
    if not vtt_files:
        return {"id": video_id, "title": title, "status": "NO_SUBS", "file": None}

    vtt_path = vtt_files[0]
    try:
        cleaned_text = clean_vtt_file(vtt_path)
        md_path = output_dir / f"{video_id}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"URL: {url}\n\n")
            f.write("---\n\n")
            f.write(cleaned_text)
        vtt_path.unlink()
        return {"id": video_id, "title": title, "status": "SUCCESS", "file": str(md_path)}
    except Exception as exc:
        return {"id": video_id, "title": title, "status": "ERROR", "file": None, "error": str(exc)[:100]}


def find_last_chunk(transcript_dir: Path, chunk_pattern: str) -> tuple[Path | None, int]:
    if not transcript_dir.exists():
        return None, 0

    chunks = []
    for path in transcript_dir.glob(chunk_pattern):
        nums = re.findall(r"(\d+)", path.stem)
        if nums:
            chunks.append((path, int(nums[-1])))

    if not chunks:
        for path in transcript_dir.glob("*.md"):
            nums = re.findall(r"(?:PART|CHUNK|CONSOLIDATED_PART)_(\d+)", path.name)
            if nums:
                chunks.append((path, int(nums[-1])))

    if not chunks:
        return None, 0

    chunks.sort(key=lambda item: item[1])
    return chunks[-1]


def build_chunk_path(transcript_dir: Path, base_name: str, chunk_num: int, chunk_file_template: str | None = None) -> Path:
    if chunk_file_template:
        return transcript_dir / chunk_file_template.format(num=chunk_num)
    return transcript_dir / f"{base_name.replace(' ', '_')}_PART_{chunk_num:02d}.md"


def format_video_section(title: str, url: str, content: str) -> str:
    return f"\n\n---\n\n# {title}\n\nURL: {url}\n\n---\n\n{content.strip()}\n"


def parse_chunk_document(content: str, default_title: str) -> tuple[str, str]:
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    chunk_title = title_match.group(1).strip() if title_match else default_title
    separator_match = re.search(r"^={20,}\s*$", content, re.MULTILINE)
    if separator_match:
        body = content[separator_match.end():].strip()
    else:
        body = content.strip()
    return chunk_title, body


def render_chunk_document(chunk_title: str, body: str) -> str:
    cleaned_body = body.strip()
    titles = [m.group(1).strip() for m in re.finditer(r"^# (.+)$", cleaned_body, re.MULTILINE)]
    toc_lines = "\n".join(f"{i}. {title}" for i, title in enumerate(titles, start=1))
    return (
        f"# {chunk_title}\n"
        "## Table of Contents\n\n"
        f"{toc_lines}\n\n"
        + "=" * 80
        + "\n\n"
        + cleaned_body
        + "\n"
    )


def write_chunk_document(chunk_path: Path, chunk_title: str, body: str):
    with open(chunk_path, "w", encoding="utf-8") as f:
        f.write(render_chunk_document(chunk_title, body))


def append_to_chunks(
    transcript_dir: Path,
    chunk_pattern: str,
    base_name: str,
    downloaded_files: list[dict],
    chunk_file_template: str | None = None,
) -> tuple[int, int]:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    last_chunk_path, last_chunk_num = find_last_chunk(transcript_dir, chunk_pattern)

    if last_chunk_path is None:
        current_chunk_num = 1
        current_chunk_title = f"{base_name} - Part {current_chunk_num:02d}"
        current_chunk_path = build_chunk_path(transcript_dir, base_name, current_chunk_num, chunk_file_template)
        current_body = ""
    else:
        current_chunk_num = last_chunk_num
        current_chunk_path = last_chunk_path
        with open(last_chunk_path, "r", encoding="utf-8") as f:
            current_content = f.read()
        current_chunk_title, current_body = parse_chunk_document(
            current_content, f"{base_name} - Part {current_chunk_num:02d}"
        )

    appended_count = 0
    new_chunks = 0
    original_last_chunk = last_chunk_path

    for file_info in downloaded_files:
        md_path = Path(file_info["file"])
        if not md_path.exists():
            continue

        content = md_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        title = ""
        url = ""
        transcript_lines = []

        for index, line in enumerate(lines):
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            elif line.startswith("URL: ") and not url:
                url = line.replace("URL: ", "", 1).strip()
            elif line.strip() == "---":
                transcript_lines = lines[index + 1 :]
                break

        if not title or not url:
            continue

        section = format_video_section(title, url, "\n".join(transcript_lines))
        candidate_body = (current_body + section).strip()
        candidate_document = render_chunk_document(current_chunk_title, candidate_body)

        if len(candidate_document.encode("utf-8")) > MAX_CHUNK_SIZE and current_body.strip():
            write_chunk_document(current_chunk_path, current_chunk_title, current_body)
            current_chunk_num += 1
            new_chunks += 1
            current_chunk_title = f"{base_name} - Part {current_chunk_num:02d}"
            current_chunk_path = build_chunk_path(transcript_dir, base_name, current_chunk_num, chunk_file_template)
            current_body = section.strip()
        else:
            current_body = candidate_body

        appended_count += 1

    if appended_count:
        write_chunk_document(current_chunk_path, current_chunk_title, current_body)
        if original_last_chunk and current_chunk_path == original_last_chunk:
            print(f"    Updated: {current_chunk_path.name} (+{appended_count} videos)")
        else:
            size_mb = current_chunk_path.stat().st_size / 1024 / 1024
            print(f"    Created: {current_chunk_path.name} ({size_mb:.2f} MB)")

    return appended_count, new_chunks


def load_pending() -> dict:
    payload = load_json(PENDING_PATH, default={})
    payload.setdefault("collections", {})
    payload.setdefault("channels", {})
    return payload


def resolve_targets(args: list[str], collections: dict[str, dict], pending: dict) -> dict[str, dict]:
    if args:
        targets = {}
        lower_map = {key.lower(): key for key in collections}
        for value in args:
            key = value if value in collections else lower_map.get(value.lower())
            if not key:
                print(f"WARNING: Collection '{value}' not found in collection_registry.json")
                continue
            targets[key] = collections[key]
        return targets

    targets = {}
    for key, collection in collections.items():
        if collection["collection_type"] != "single_channel_appendable":
            continue
        if collection["update_strategy"] != "append":
            continue
        pending_record = pending.get("collections", {}).get(key, {})
        if pending_record.get("new_count", 0) > 0:
            targets[key] = collection
    return targets


def update_collection(collection_key: str, collection: dict, pending: dict, dry_run: bool = False) -> dict:
    result = {"collection": collection_key, "downloaded": 0, "failed": 0, "appended": 0, "new_chunks": 0}

    if collection["collection_type"] != "single_channel_appendable" or collection["update_strategy"] != "append":
        print(
            f"\n  {collection_key}: Refusing to update; "
            f"collection_type={collection['collection_type']}, "
            f"update_strategy={collection['update_strategy']}."
        )
        return result

    pending_record = pending.get("collections", {}).get(collection_key, {})
    new_videos = list(pending_record.get("new_videos", []))
    if not new_videos:
        print(f"\n  {collection_key}: No pending videos to update.")
        return result

    print(f"\n{'=' * 72}")
    print(f"  Updating: {collection_key}")
    print(f"  Videos to download: {len(new_videos)}")
    print(f"{'=' * 72}")

    if dry_run:
        print("  [DRY RUN] Would download:")
        for index, video in enumerate(new_videos[:10], start=1):
            print(f"    {index}. {video['title'][:78]}")
        if len(new_videos) > 10:
            print(f"    ... and {len(new_videos) - 10} more")
        result["dry_run"] = True
        return result

    raw_dir = resolve_collection_raw_dir(collection)
    if raw_dir is None:
        print(f"  ERROR: No raw_dir configured for {collection_key}")
        return result
    raw_dir.mkdir(parents=True, exist_ok=True)

    successful = []
    failed = []
    print(f"  [1/2] Downloading transcripts ({WORKERS} workers)...")
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(download_single_transcript, video, raw_dir): video for video in new_videos}
        for index, future in enumerate(as_completed(futures), start=1):
            outcome = future.result()
            if outcome["status"] == "SUCCESS":
                print(f"    [{index}/{len(new_videos)}] OK  {outcome['title'][:60]}")
                successful.append(outcome)
            else:
                print(f"    [{index}/{len(new_videos)}] NO  {outcome['title'][:60]} ({outcome['status']})")
                failed.append(outcome)

    result["downloaded"] = len(successful)
    result["failed"] = len(failed)
    print(f"\n  Downloaded: {len(successful)} | Failed: {len(failed)}")

    if not successful:
        print("  No transcripts downloaded. Skipping append step.")
        return result

    print("  [2/2] Appending to canonical chunk files...")
    transcript_dir = REPO_ROOT / collection["transcript_dir"]
    appended, new_chunks = append_to_chunks(
        transcript_dir=transcript_dir,
        chunk_pattern=collection.get("chunk_pattern", "*.md"),
        base_name=collection.get("base_name", collection_key),
        downloaded_files=successful,
        chunk_file_template=collection.get("chunk_file_template"),
    )

    successful_ids = {item["id"] for item in successful}
    remaining = [video for video in new_videos if video["id"] not in successful_ids]
    pending_record["new_videos"] = remaining
    pending_record["new_count"] = len(remaining)
    pending_record["last_updated"] = datetime.now(timezone.utc).isoformat()

    if collection_key in pending.get("channels", {}):
        pending["channels"][collection_key]["new_videos"] = remaining
        pending["channels"][collection_key]["new_count"] = len(remaining)

    result["appended"] = appended
    result["new_chunks"] = new_chunks
    return result


def main():
    collections = load_collection_registry()
    pending = load_pending()

    if not pending.get("collections"):
        print("No collection-oriented pending updates found. Run transcript_scanner.py first.")
        return

    args = [value for value in sys.argv[1:] if not value.startswith("--")]
    dry_run = "--dry-run" in sys.argv[1:]
    targets = resolve_targets(args, collections, pending)
    if not targets:
        print("No append-safe collections with pending updates.")
        return

    print("=" * 78)
    print("  TRANSCRIPT COLLECTION UPDATER")
    if dry_run:
        print("  MODE: DRY RUN")
    print(f"  Collections: {len(targets)}")
    print(f"  Using yt-dlp: {YT_DLP_PATH}")
    print("=" * 78)

    start = time.time()
    results = []
    for collection_key, collection in targets.items():
        results.append(update_collection(collection_key, collection, pending, dry_run=dry_run))

    elapsed = time.time() - start
    total_downloaded = sum(item["downloaded"] for item in results)
    total_failed = sum(item["failed"] for item in results)
    total_appended = sum(item["appended"] for item in results)

    print(f"\n{'=' * 78}")
    print("  UPDATE COMPLETE")
    print(f"{'=' * 78}")
    print(f"  Downloaded: {total_downloaded} | Failed: {total_failed} | Appended: {total_appended}")
    print(f"  Time: {elapsed:.1f}s")

    if not dry_run:
        save_json(PENDING_PATH, pending)
        print(f"  Updated pending log: {PENDING_PATH}")


if __name__ == "__main__":
    main()
