#!/usr/bin/env python3
"""Build provenance manifests for collection-first transcript scanning."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

try:
    from . import collection_utils as cu
except ImportError:
    import collection_utils as cu


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "collections",
        nargs="*",
        help="Optional collection keys. Defaults to all collections using scan_strategy=manifest.",
    )
    parser.add_argument(
        "--include-appendable",
        action="store_true",
        help="Also build manifests for appendable collections when no explicit collection list is provided.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace root for transcript data, manifests, and collection-relative paths",
    )
    return parser.parse_args()


def _entry_override_for(candidate: dict, overrides: dict) -> dict:
    entries = overrides.get("entries", {})
    lookup_keys = []
    if candidate.get("video_id"):
        lookup_keys.append(candidate["video_id"])
    lookup_keys.append(candidate.get("normalized_title", ""))
    for key in lookup_keys:
        if key and key in entries:
            return dict(entries[key])
    return {}


def _dedupe_matches(matches: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for match in matches:
        deduped[match["id"]] = match
    return list(deduped.values())


def _build_aliases(candidate: dict, matched_video: dict | None) -> list[str]:
    aliases = []
    seen = set()
    for value in [candidate.get("title", ""), matched_video.get("title", "") if matched_video else ""]:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cu.normalize_title(cleaned)
        if not key or key in seen:
            continue
        aliases.append(cleaned)
        seen.add(key)
    return aliases


def _build_duplicate_groups(entries: list[dict]) -> dict:
    video_groups: dict[str, list[dict]] = {}
    title_groups: dict[str, list[dict]] = {}

    for entry in entries:
        video_id = entry.get("video_id") or ""
        if video_id:
            video_groups.setdefault(video_id, []).append(entry)

        title_key = f"{entry.get('source_channel_key', '')}::{entry.get('normalized_title', '')}"
        title_groups.setdefault(title_key, []).append(entry)

    by_video_id = []
    for video_id, group in sorted(video_groups.items()):
        if len(group) < 2:
            continue
        by_video_id.append(
            {
                "video_id": video_id,
                "count": len(group),
                "titles": sorted({item["title"] for item in group}),
                "bundle_files": sorted({item["bundle_file"] for item in group}),
            }
        )

    by_normalized_title = []
    for title_key, group in sorted(title_groups.items()):
        if len(group) < 2:
            continue
        by_normalized_title.append(
            {
                "normalized_title": group[0]["normalized_title"],
                "source_channel_key": group[0].get("source_channel_key", ""),
                "count": len(group),
                "titles": sorted({item["title"] for item in group}),
                "bundle_files": sorted({item["bundle_file"] for item in group}),
            }
        )

    return {
        "by_video_id": by_video_id,
        "by_normalized_title": by_normalized_title,
    }


def _build_stats(entries: list[dict], unresolved_titles: list[dict], bundle_records: list[dict]) -> dict:
    unique_videos = cu.unique_entries_by_video(entries)
    per_source_counts: dict[str, int] = {}
    for entry in unique_videos:
        source_key = entry.get("source_channel_key") or "unknown"
        per_source_counts[source_key] = per_source_counts.get(source_key, 0) + 1

    bundle_role_counts: dict[str, int] = {}
    for record in bundle_records:
        role = record["bundle_role"]
        bundle_role_counts[role] = bundle_role_counts.get(role, 0) + 1

    return {
        "matched_entries": len(entries),
        "unique_matched_videos": len(unique_videos),
        "unresolved_titles": len(unresolved_titles),
        "bundle_files": len(bundle_records),
        "per_source_counts": per_source_counts,
        "bundle_role_counts": bundle_role_counts,
    }


def build_manifest_for_collection(collection_key: str, collection: dict) -> dict:
    overrides = cu.load_collection_overrides(collection_key)
    source_channels = collection.get("source_channels", [])
    per_source_live, live_by_id, live_by_source_title = cu.build_live_video_index(source_channels)
    sidecar_entries = cu.load_existing_sidecar_entries(collection.get("legacy_sidecar_slug", ""))
    sidecar_source_key = collection.get("legacy_sidecar_source_key", "")
    bundle_records = cu.build_bundle_records(collection, overrides)

    bundle_records_by_name = {Path(record["path"]).name: record for record in bundle_records}
    entries: list[dict] = []
    unresolved_titles: list[dict] = []

    for bundle_path in cu.discover_bundle_files(collection):
        bundle_record = bundle_records_by_name[bundle_path.name]
        bundle_role = bundle_record["bundle_role"]
        if bundle_role == "reference_only":
            continue

        override = cu.get_bundle_override(bundle_path.name, overrides)
        default_source_keys = override.get("source_channel_keys") or bundle_record["source_channel_keys"]
        candidates = cu.extract_candidates_from_bundle(bundle_path, overrides.get("ignored_titles", []))

        for candidate in candidates:
            entry = {
                "title": candidate["title"],
                "normalized_title": candidate["normalized_title"],
                "video_id": "",
                "url": "",
                "source_channel_key": "",
                "collection_key": collection_key,
                "bundle_file": cu.display_path(bundle_path),
                "match_method": "",
                "confidence": "manual_review",
                "aliases": [],
                "notes": [],
            }

            override_entry = _entry_override_for(candidate, overrides)
            if override_entry.get("ignore"):
                continue

            if override_entry:
                entry.update(
                    {
                        "video_id": override_entry.get("video_id", candidate.get("video_id", "")),
                        "url": override_entry.get("url", candidate.get("url", "")),
                        "source_channel_key": override_entry.get("source_channel_key", ""),
                        "match_method": "override",
                        "confidence": override_entry.get("confidence", "high"),
                    }
                )
                entry["aliases"] = override_entry.get("aliases", [])
                if override_entry.get("notes"):
                    entry["notes"].append(override_entry["notes"])
                entries.append(entry)
                continue

            inline_video_id = candidate.get("video_id", "")
            inline_url = candidate.get("url", "")
            if inline_video_id:
                matched_video = live_by_id.get(inline_video_id)
                entry["video_id"] = inline_video_id
                entry["url"] = inline_url
                entry["source_channel_key"] = (
                    matched_video.get("source_channel_key", "") if matched_video else (default_source_keys[0] if len(default_source_keys) == 1 else "")
                )
                entry["match_method"] = "inline_url"
                entry["confidence"] = "high"
                entry["aliases"] = _build_aliases(candidate, matched_video)
                entries.append(entry)
                continue

            matched_candidates: list[dict] = []
            lookup_source_keys = [key for key in default_source_keys if key]
            if not lookup_source_keys:
                lookup_source_keys = [channel.get("key", "") for channel in source_channels if channel.get("key")]

            for source_key in lookup_source_keys:
                matched_candidates.extend(live_by_source_title.get((source_key, candidate["normalized_title"]), []))

            if not matched_candidates:
                sidecar_match = sidecar_entries.get(candidate["normalized_title"])
                if sidecar_match:
                    inferred_source_key = sidecar_source_key or (
                        default_source_keys[0] if default_source_keys else ""
                    )
                    matched_candidates.append(
                        {
                            "id": sidecar_match.get("video_id", ""),
                            "title": sidecar_match.get("title", candidate["title"]),
                            "url": sidecar_match.get("url", ""),
                            "source_channel_key": inferred_source_key,
                        }
                    )

            matched_candidates = _dedupe_matches(matched_candidates)
            if len(matched_candidates) == 1:
                matched_video = matched_candidates[0]
                entry["video_id"] = matched_video.get("id", "")
                entry["url"] = matched_video.get("url", "")
                entry["source_channel_key"] = matched_video.get("source_channel_key", "")
                entry["match_method"] = (
                    "legacy_anchor_match"
                    if candidate.get("source_hint") == "anchor_heading"
                    else "normalized_title_live_match"
                )
                entry["confidence"] = "high" if len(lookup_source_keys) <= 1 else "medium"
                entry["aliases"] = _build_aliases(candidate, matched_video)
                entries.append(entry)
                continue

            unresolved_titles.append(
                {
                    "title": candidate["title"],
                    "normalized_title": candidate["normalized_title"],
                    "bundle_file": cu.display_path(bundle_path),
                    "candidate_source_keys": lookup_source_keys,
                    "bundle_role": bundle_role,
                    "reason": "ambiguous_match" if matched_candidates else "no_live_match",
                }
            )

    entries.sort(key=lambda item: (item["bundle_file"], item["normalized_title"], item.get("video_id", "")))
    unresolved_titles.sort(key=lambda item: (item["bundle_file"], item["normalized_title"]))
    duplicates = _build_duplicate_groups(entries)
    stats = _build_stats(entries, unresolved_titles, bundle_records)
    stats["duplicate_video_ids"] = len(duplicates["by_video_id"])
    stats["duplicate_normalized_titles"] = len(duplicates["by_normalized_title"])
    stats["live_source_counts"] = {key: len(value) for key, value in per_source_live.items()}

    return {
        "collection_key": collection_key,
        "collection_type": collection["collection_type"],
        "generated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "generation_mode": "live_plus_local",
        "source_channels": source_channels,
        "bundle_files": bundle_records,
        "entries": entries,
        "unresolved_titles": unresolved_titles,
        "duplicates": duplicates,
        "stats": stats,
        "notes": [note for note in [collection.get("notes", "")] + overrides.get("manual_notes", []) if note],
    }


def main() -> int:
    args = parse_args()
    cu.configure_runtime_root(args.workspace)
    cu.ensure_output_dirs()
    collections = cu.load_collection_registry()

    if args.collections:
        targets = args.collections
    else:
        targets = []
        for key, collection in collections.items():
            if collection["scan_strategy"] == "manifest":
                targets.append(key)
            elif args.include_appendable and collection["collection_type"] == "single_channel_appendable":
                targets.append(key)

    if not targets:
        print("No collections selected.")
        return 0

    for collection_key in targets:
        collection = collections.get(collection_key)
        if not collection:
            print(f"WARNING: Unknown collection '{collection_key}'. Skipping.")
            continue

        manifest = build_manifest_for_collection(collection_key, collection)
        manifest_path = cu.resolve_manifest_path(collection)
        cu.save_json(manifest_path, manifest)
        print(
            f"{collection_key}: wrote {manifest_path.name} "
            f"({manifest['stats']['unique_matched_videos']} unique videos, "
            f"{manifest['stats']['unresolved_titles']} unresolved, "
            f"{manifest['stats']['duplicate_video_ids']} duplicate video IDs)"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
