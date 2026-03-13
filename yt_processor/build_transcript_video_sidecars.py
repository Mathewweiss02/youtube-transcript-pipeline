#!/usr/bin/env python3
"""
Generate transcript sidecar metadata for channels whose transcript bundles do not
store per-video YouTube URLs inline.

The output file is consumed by the Next.js app to restore direct embeds without
rewriting transcript sources.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "youtuber wiki apps" / "my-app"
APP_REGISTRY_PATH = APP_DIR / "data" / "channel-registry.json"
OUTPUT_PATH = APP_DIR / "data" / "transcript-video-sidecars.json"
OVERRIDES_PATH = APP_DIR / "data" / "transcript-video-sidecar-overrides.json"
TRANSCRIPTS_ROOT = ROOT / "transcripts"
SLASH_VARIANTS = r"[\u002f\u2044\u2215\u2571\u29f8\uff0f]"
BAR_VARIANTS = r"[\u007c\uff5c]"


def clean_title(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"^#{1,6}\s+", "", normalized)
    normalized = re.sub(r"^mindpump[_\s-]+", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^Video\s+\d+\s*:\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^\d+\s*[-:]\s+", "", normalized)
    normalized = re.sub(r"\.en$", "", normalized, flags=re.IGNORECASE)
    normalized = unicodedata.normalize("NFKC", normalized)
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(
        rf"\bw\s*{SLASH_VARIANTS}\s*",
        " with ",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        rf"\s*{BAR_VARIANTS}\s*(the\s+)?jay\s+campbell\s+(podcast|pc)\b",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"['\"`]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_title(value: str) -> str:
    normalized = clean_title(value)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return normalized


def split_heading(line: str) -> str | None:
    match = re.match(r"^#{2,6}\s+(.+)$", line.strip())
    if not match:
        return None

    raw = match.group(1).strip()
    inline_match = re.match(r"^(.*?\.en)(.*)$", raw, flags=re.IGNORECASE)
    title = inline_match.group(1) if inline_match else raw
    title = title.strip()

    if not title or "table of contents" in title.lower():
        return None

    return title


def build_aliases(transcript_title: str, video_title: str) -> list[str]:
    candidates = [
        transcript_title,
        clean_title(transcript_title),
        video_title,
        clean_title(video_title),
    ]
    aliases: list[str] = []
    seen_keys = {normalize_title(transcript_title)}

    for candidate in candidates:
        if not candidate:
            continue

        key = normalize_title(candidate)
        if not key or key in seen_keys:
            continue

        aliases.append(candidate)
        seen_keys.add(key)

    return aliases


def iter_transcript_titles(transcript_dir: Path) -> Iterable[str]:
    for path in sorted(transcript_dir.glob("*.md")):
        if path.name.lower().startswith(("readme", "index")):
            continue

        content = path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            title = split_heading(line)
            if title:
                yield title


def build_channel_video_url(channel_url: str) -> str:
    trimmed = channel_url.rstrip("/")
    if trimmed.endswith("/videos"):
        return trimmed
    return f"{trimmed}/videos"


def fetch_channel_videos(channel_url: str) -> list[dict[str, str]]:
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--dump-single-json", build_channel_video_url(channel_url)],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    entries = payload.get("entries") or []

    videos: list[dict[str, str]] = []
    for entry in entries:
        video_id = entry.get("id") or ""
        title = entry.get("title") or ""
        if not video_id or not title:
            continue

        videos.append(
            {
                "title": title,
                "videoId": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )

    return videos


def load_registry() -> dict:
    return json.loads(APP_REGISTRY_PATH.read_text(encoding="utf-8"))


def load_existing_output(output_path: Path) -> dict:
    if not output_path.exists():
        return {"channels": {}}

    return json.loads(output_path.read_text(encoding="utf-8"))


def load_overrides(overrides_path: Path) -> dict:
    if not overrides_path.exists():
        return {"channels": {}}

    return json.loads(overrides_path.read_text(encoding="utf-8"))


def build_entries_for_channel(
    channel_slug: str,
    channel_url: str,
    slug_to_namespace: dict[str, str],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    transcript_dir = TRANSCRIPTS_ROOT / slug_to_namespace[channel_slug]

    transcript_titles = list(iter_transcript_titles(transcript_dir))
    transcript_title_map: dict[str, str] = {}
    for title in transcript_titles:
        transcript_title_map.setdefault(normalize_title(title), title)

    videos = fetch_channel_videos(channel_url)
    entries: list[dict[str, str]] = []

    for video in videos:
        key = normalize_title(video["title"])
        transcript_title = transcript_title_map.get(key)
        if not transcript_title:
            continue

        entry: dict[str, object] = {
            "title": transcript_title,
            "url": video["url"],
            "videoId": video["videoId"],
        }
        aliases = build_aliases(transcript_title, video["title"])
        if aliases:
            entry["aliases"] = aliases

        entries.append(entry)

    entries.sort(key=lambda item: normalize_title(item["title"]))
    stats = {
        "transcript_titles": len(transcript_titles),
        "channel_videos": len(videos),
        "matched_entries": len(entries),
    }
    return entries, stats


def merge_override_entries(
    generated_entries: list[dict[str, object]],
    override_entries: list[dict[str, object]],
) -> tuple[list[dict[str, object]], int]:
    merged: dict[str, dict[str, object]] = {
        normalize_title(str(entry["title"])): entry
        for entry in generated_entries
    }
    override_count = 0

    for entry in override_entries:
        key = normalize_title(str(entry["title"]))
        if not key:
            continue

        merged[key] = entry
        override_count += 1

    entries = list(merged.values())
    entries.sort(key=lambda item: normalize_title(str(item["title"])))
    return entries, override_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--channels",
        nargs="+",
        required=True,
        help="Channel slugs from the Next.js app registry, e.g. solar-athlete jay-campbell",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Output JSON file path",
    )
    parser.add_argument(
        "--overrides",
        default=str(OVERRIDES_PATH),
        help="Optional JSON file containing curated sidecar overrides",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_registry()
    slug_to_channel = {
        channel["slug"]: channel
        for channel in registry["channels"].values()
    }
    slug_to_namespace = {
        channel["slug"]: namespace
        for namespace, channel in registry["channels"].items()
    }

    output_path = Path(args.output)
    payload = load_existing_output(output_path)
    payload.setdefault("channels", {})
    overrides_path = Path(args.overrides)
    overrides_payload = load_overrides(overrides_path)
    overrides_payload.setdefault("channels", {})

    for channel_slug in args.channels:
        channel = slug_to_channel.get(channel_slug)
        if not channel:
            print(f"Unknown channel slug: {channel_slug}", file=sys.stderr)
            return 1

        entries, stats = build_entries_for_channel(
            channel_slug,
            channel["youtubeUrl"],
            slug_to_namespace,
        )
        override_entries = (
            overrides_payload["channels"].get(channel_slug, {}).get("entries") or []
        )
        entries, override_count = merge_override_entries(entries, override_entries)
        payload["channels"][channel_slug] = {
            "generatedAt": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "source": "yt-dlp normalized title match + curated overrides",
            "entries": entries,
        }
        print(
            f"{channel_slug}: matched {stats['matched_entries']} / {stats['transcript_titles']} transcript headings"
            f" against {stats['channel_videos']} channel videos"
            f" (+{override_count} curated overrides)"
        )

    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
