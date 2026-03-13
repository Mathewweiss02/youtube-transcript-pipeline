#!/usr/bin/env python3
"""Collection-first transcript scanner."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone

from collection_utils import (
    PENDING_PATH,
    YT_DLP_PATH,
    extract_candidates_from_bundle,
    fetch_channel_videos,
    load_collection_overrides,
    load_collection_registry,
    load_json,
    resolve_canonical_source_files,
    resolve_manifest_path,
    save_json,
    unique_entries_by_video,
)

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


SCHEMA_VERSION = 2


def load_pending() -> dict:
    default = {"schema_version": SCHEMA_VERSION, "last_scan": None, "collections": {}, "channels": {}}
    if not PENDING_PATH.exists():
        return default

    try:
        payload = load_json(PENDING_PATH, default=default)
    except json.JSONDecodeError:
        return default

    if "collections" not in payload:
        return default
    payload.setdefault("schema_version", SCHEMA_VERSION)
    payload.setdefault("last_scan", None)
    payload.setdefault("channels", {})
    return payload


def _base_result(collection_key: str, collection: dict) -> dict:
    return {
        "collection_key": collection_key,
        "display_name": collection.get("display_name", collection_key),
        "collection_type": collection["collection_type"],
        "scan_strategy": collection["scan_strategy"],
        "update_strategy": collection["update_strategy"],
        "scan_mode_used": collection["scan_strategy"],
        "source_channels": collection.get("source_channels", []),
        "total_on_sources": 0,
        "total_indexed": 0,
        "new_count": 0,
        "new_videos": [],
        "unresolved_count": 0,
        "confidence_summary": {"high": 0, "medium": 0, "manual_review": 0},
        "source_summaries": [],
        "scan_notes": [],
    }


def _compat_channel_record(result: dict) -> dict | None:
    if result["collection_type"] != "single_channel_appendable":
        return None
    source_channels = result.get("source_channels", [])
    if len(source_channels) != 1:
        return None

    source = source_channels[0]
    return {
        "channel_name": result["collection_key"],
        "channel_url": source.get("youtube_url", ""),
        "total_on_youtube": result["total_on_sources"],
        "total_transcribed": result["total_indexed"],
        "new_count": result["new_count"],
        "new_videos": result["new_videos"],
        "match_mode": "collection_inline_urls",
    }


def scan_manual_collection(collection_key: str, collection: dict) -> dict:
    result = _base_result(collection_key, collection)
    result["scan_mode_used"] = "manual"
    reason = collection.get("manual_reason") or collection.get("notes") or "Manual-only collection."
    result["scan_notes"].append(reason)
    return result


def scan_inline_collection(collection_key: str, collection: dict) -> dict:
    result = _base_result(collection_key, collection)
    source_channels = collection.get("source_channels", [])
    source_key = source_channels[0].get("key", "") if source_channels else ""
    overrides = load_collection_overrides(collection_key)
    canonical_files = resolve_canonical_source_files(collection)

    indexed_entries = []
    indexed_ids: set[str] = set()
    indexed_titles: set[str] = set()

    if not canonical_files:
        result["scan_notes"].append("No canonical source files found for inline scan.")
        return result

    for file_path in canonical_files:
        for candidate in extract_candidates_from_bundle(file_path, overrides.get("ignored_titles", [])):
            indexed_entries.append(
                {
                    "video_id": candidate.get("video_id", ""),
                    "normalized_title": candidate.get("normalized_title", ""),
                    "source_channel_key": source_key,
                }
            )
            if candidate.get("video_id"):
                indexed_ids.add(candidate["video_id"])
            if candidate.get("normalized_title"):
                indexed_titles.add(candidate["normalized_title"])

    unique_indexed = unique_entries_by_video(indexed_entries)
    live_videos = []
    if source_channels:
        live_videos = fetch_channel_videos(source_channels[0].get("youtube_url", ""))
    else:
        result["scan_notes"].append("No live source channel configured for inline scan.")

    new_videos = []
    for video in live_videos:
        if video["id"] in indexed_ids:
            continue
        if video["normalized_title"] in indexed_titles:
            continue
        new_videos.append(
            {
                "id": video["id"],
                "title": video["title"],
                "url": video["url"],
                "source_channel_key": source_key,
            }
        )

    result["total_on_sources"] = len(live_videos)
    result["total_indexed"] = len(unique_indexed)
    result["new_count"] = len(new_videos)
    result["new_videos"] = new_videos
    result["source_summaries"] = [
        {
            "source_channel_key": source_key,
            "total_on_source": len(live_videos),
            "indexed_on_source": len(unique_indexed),
            "new_count": len(new_videos),
        }
    ]
    result["confidence_summary"] = {
        "high": len(indexed_ids),
        "medium": max(len(indexed_titles) - len(indexed_ids), 0),
        "manual_review": 0,
    }

    if len(indexed_titles) > len(indexed_ids):
        result["scan_notes"].append("Title fallback remains active for some inline-url scans.")
    if collection.get("notes"):
        result["scan_notes"].append(collection["notes"])

    return result


def scan_manifest_collection(collection_key: str, collection: dict) -> dict:
    result = _base_result(collection_key, collection)
    manifest_path = resolve_manifest_path(collection)
    if not manifest_path.exists():
        result["scan_notes"].append(f"Manifest missing: {manifest_path}")
        return result

    manifest = load_json(manifest_path, default={})
    manifest_entries = unique_entries_by_video(manifest.get("entries", []))
    manifest_stats = manifest.get("stats", {})

    indexed_ids = {entry["video_id"] for entry in manifest_entries if entry.get("video_id")}
    indexed_titles = {
        (entry.get("source_channel_key", ""), entry.get("normalized_title", ""))
        for entry in manifest_entries
        if entry.get("normalized_title") and entry.get("source_channel_key")
    }

    per_source_counts = manifest_stats.get("per_source_counts", {})
    source_summaries = []
    total_on_sources = 0
    new_videos = []

    for source in collection.get("source_channels", []):
        source_key = source.get("key", "")
        youtube_url = source.get("youtube_url", "")
        if not youtube_url:
            source_summaries.append(
                {
                    "source_channel_key": source_key,
                    "total_on_source": 0,
                    "indexed_on_source": per_source_counts.get(source_key, 0),
                    "new_count": 0,
                    "note": "No live source URL configured.",
                }
            )
            continue

        live_videos = fetch_channel_videos(youtube_url)
        total_on_sources += len(live_videos)
        source_new = []
        for video in live_videos:
            if video["id"] in indexed_ids:
                continue
            if (source_key, video["normalized_title"]) in indexed_titles:
                continue
            source_new.append(
                {
                    "id": video["id"],
                    "title": video["title"],
                    "url": video["url"],
                    "source_channel_key": source_key,
                }
            )

        new_videos.extend(source_new)
        source_summaries.append(
            {
                "source_channel_key": source_key,
                "total_on_source": len(live_videos),
                "indexed_on_source": per_source_counts.get(source_key, 0),
                "new_count": len(source_new),
            }
        )

    result["total_on_sources"] = total_on_sources
    result["total_indexed"] = manifest_stats.get("unique_matched_videos", len(indexed_ids))
    result["new_count"] = len(new_videos)
    result["new_videos"] = new_videos
    result["unresolved_count"] = manifest_stats.get("unresolved_titles", len(manifest.get("unresolved_titles", [])))
    result["confidence_summary"] = {
        "high": sum(1 for entry in manifest_entries if entry.get("confidence") == "high"),
        "medium": sum(1 for entry in manifest_entries if entry.get("confidence") == "medium"),
        "manual_review": sum(1 for entry in manifest_entries if entry.get("confidence") == "manual_review"),
    }
    result["source_summaries"] = source_summaries

    duplicate_video_ids = manifest_stats.get("duplicate_video_ids", 0)
    duplicate_titles = manifest_stats.get("duplicate_normalized_titles", 0)
    if duplicate_video_ids:
        result["scan_notes"].append(f"Manifest tracks {duplicate_video_ids} duplicate video-id groups across bundle files.")
    if duplicate_titles:
        result["scan_notes"].append(f"Manifest tracks {duplicate_titles} duplicate title groups across bundle files.")
    if result["unresolved_count"]:
        result["scan_notes"].append(f"Manifest still has {result['unresolved_count']} unresolved title matches.")

    for note in manifest.get("notes", []):
        if note:
            result["scan_notes"].append(note)
    if collection.get("notes"):
        result["scan_notes"].append(collection["notes"])

    return result


def scan_collection(collection_key: str, collection: dict) -> dict:
    strategy = collection["scan_strategy"]
    print(f"\n{'=' * 72}")
    print(f"  Scanning: {collection_key}")
    print(f"  Type:     {collection['collection_type']}")
    print(f"  Strategy: {strategy}")
    print(f"{'=' * 72}")

    if strategy == "manual":
        return scan_manual_collection(collection_key, collection)
    if strategy == "manifest":
        return scan_manifest_collection(collection_key, collection)
    return scan_inline_collection(collection_key, collection)


def print_report(pending: dict):
    print("\n" + "=" * 78)
    print("  TRANSCRIPT COLLECTION SCAN REPORT")
    print(f"  Last scan: {pending.get('last_scan', 'never')}")
    print("=" * 78)

    total_new = 0
    for collection_key, result in pending.get("collections", {}).items():
        total_new += result.get("new_count", 0)
        if result["scan_mode_used"] == "manual":
            status = "MANUAL"
        elif result.get("new_count", 0) == 0:
            status = "UP TO DATE"
        else:
            status = f"{result['new_count']} NEW"

        print(f"\n  {collection_key}: {status}")
        print(
            f"    Type: {result['collection_type']} | "
            f"Strategy: {result['scan_mode_used']} | "
            f"Indexed: {result['total_indexed']} | "
            f"Live: {result['total_on_sources']}"
        )

        if result.get("new_videos"):
            for i, video in enumerate(result["new_videos"][:5], start=1):
                print(f"      {i}. {video['title'][:78]}")
            if result["new_count"] > 5:
                print(f"      ... and {result['new_count'] - 5} more")

        for note in result.get("scan_notes", [])[:3]:
            print(f"    Note: {note}")

    print(f"\n{'=' * 78}")
    print(f"  TOTAL NEW VIDEOS ACROSS COLLECTIONS: {total_new}")
    print("=" * 78)


def resolve_targets(argv: list[str], collections: dict[str, dict]) -> dict[str, dict]:
    if not argv:
        return dict(collections)

    targets: dict[str, dict] = {}
    lower_map = {key.lower(): key for key in collections}
    for value in argv:
        key = collections.get(value)
        if key:
            targets[value] = collections[value]
            continue

        resolved = lower_map.get(value.lower())
        if resolved:
            targets[resolved] = collections[resolved]
            continue

        print(f"WARNING: Collection '{value}' not found in collection_registry.json")
    return targets


def main():
    collections = load_collection_registry()
    args = sys.argv[1:]

    if "--report" in args:
        pending = load_pending()
        print_report(pending)
        return

    raw_targets = [arg for arg in args if not arg.startswith("--")]
    targets = resolve_targets(raw_targets, collections)
    if not targets:
        print("No collections selected.")
        return

    print("=" * 78)
    print("  TRANSCRIPT COLLECTION SCANNER")
    print(f"  Collections: {len(targets)}")
    print(f"  Using yt-dlp: {YT_DLP_PATH}")
    print("=" * 78)

    pending = load_pending()
    pending["schema_version"] = SCHEMA_VERSION
    pending["collections"] = {
        key: value for key, value in pending.get("collections", {}).items() if key in collections
    }
    pending["channels"] = {
        key: value for key, value in pending.get("channels", {}).items() if key in collections
    }

    start = time.time()
    if raw_targets:
        new_collection_payload = dict(pending["collections"])
        compat_channels = dict(pending["channels"])
    else:
        new_collection_payload = {}
        compat_channels = {}

    for collection_key, collection in targets.items():
        result = scan_collection(collection_key, collection)
        new_collection_payload[collection_key] = result

        compat = _compat_channel_record(result)
        if compat:
            compat_channels[collection_key] = compat
        elif collection_key in compat_channels:
            del compat_channels[collection_key]

    pending["collections"] = new_collection_payload
    pending["channels"] = compat_channels
    pending["last_scan"] = datetime.now(timezone.utc).isoformat()
    save_json(PENDING_PATH, pending)

    elapsed = time.time() - start
    print(f"\n  Scan completed in {elapsed:.1f}s")
    print(f"  Results saved to: {PENDING_PATH}")
    print_report(pending)


if __name__ == "__main__":
    main()
