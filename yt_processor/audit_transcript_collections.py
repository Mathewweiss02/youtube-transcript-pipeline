#!/usr/bin/env python3
"""Read-only audit for transcript collections and pipeline risk."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from collection_utils import (
    MAX_CHUNK_SIZE,
    REPO_ROOT,
    REPORTS_DIR,
    URL_RE,
    build_bundle_records,
    classify_bundle_role,
    discover_bundle_files,
    ensure_output_dirs,
    extract_candidates_from_bundle,
    load_collection_overrides,
    load_collection_registry,
    load_json,
    resolve_collection_raw_dir,
    resolve_collection_transcript_dir,
    resolve_manifest_path,
    save_json,
)

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _raw_dir_snapshot(raw_dir: Path | None) -> dict:
    if not raw_dir or not raw_dir.exists():
        return {
            "markdown_files": 0,
            "video_id_files": 0,
            "non_video_id_files": 0,
            "video_ids": set(),
        }

    raw_files = list(raw_dir.glob("*.md"))
    raw_video_ids = set()
    non_video_id_files = 0

    for path in raw_files:
        if VIDEO_ID_RE.fullmatch(path.stem):
            raw_video_ids.add(path.stem)
        else:
            non_video_id_files += 1

    return {
        "markdown_files": len(raw_files),
        "video_id_files": len(raw_video_ids),
        "non_video_id_files": non_video_id_files,
        "video_ids": raw_video_ids,
    }


def _local_collection_snapshot(collection_key: str, collection: dict) -> dict:
    overrides = load_collection_overrides(collection_key)
    transcript_dir = resolve_collection_transcript_dir(collection)
    raw_dir = resolve_collection_raw_dir(collection)
    raw_snapshot = _raw_dir_snapshot(raw_dir)
    bundle_files = discover_bundle_files(collection)
    bundle_records = build_bundle_records(collection, overrides)

    manifest_exists = False
    manifest_stats = {}
    if collection["scan_strategy"] == "manifest":
        manifest_path = resolve_manifest_path(collection)
        if manifest_path.exists():
            manifest_exists = True
            manifest_stats = load_json(manifest_path, default={}).get("stats", {})

    entries = []
    duplicate_video_ids: dict[str, list[str]] = {}
    duplicate_titles: dict[str, list[str]] = {}
    oversized_files = []
    bundle_role_counts: dict[str, int] = {}
    inline_url_video_ids: set[str] = set()

    for record in bundle_records:
        role = record["bundle_role"]
        bundle_role_counts[role] = bundle_role_counts.get(role, 0) + 1
        if record["size_bytes"] > MAX_CHUNK_SIZE:
            oversized_files.append(
                {
                    "path": record["path"],
                    "size_bytes": record["size_bytes"],
                    "size_mb": round(record["size_bytes"] / 1024 / 1024, 2),
                }
            )

    for bundle_path in bundle_files:
        role = classify_bundle_role(bundle_path.name, collection, overrides)
        if role == "reference_only":
            continue

        text = bundle_path.read_text(encoding="utf-8", errors="ignore")
        inline_url_video_ids.update(URL_RE.findall(text))

        candidates = extract_candidates_from_bundle(bundle_path, overrides.get("ignored_titles", []))
        for candidate in candidates:
            entry = dict(candidate)
            entry["bundle_file"] = str(bundle_path.relative_to(REPO_ROOT))
            entries.append(entry)

            video_id = entry.get("video_id") or ""
            if video_id:
                duplicate_video_ids.setdefault(video_id, []).append(entry["bundle_file"])

            duplicate_titles.setdefault(entry["normalized_title"], []).append(entry["bundle_file"])

    duplicated_video_id_count = sum(1 for files in duplicate_video_ids.values() if len(set(files)) > 1)
    duplicated_title_count = sum(1 for files in duplicate_titles.values() if len(set(files)) > 1)
    merged_video_ids = {entry["video_id"] for entry in entries if entry.get("video_id")}
    unique_video_ids = len(merged_video_ids)
    unique_titles = len({entry["normalized_title"] for entry in entries})
    raw_only_video_ids = sorted(raw_snapshot["video_ids"] - inline_url_video_ids)
    merged_only_video_ids = sorted(inline_url_video_ids - raw_snapshot["video_ids"])

    risk_flags = []
    if collection["collection_type"] != "single_channel_appendable":
        risk_flags.append("manifest_or_manual_required")
    if collection["scan_strategy"] == "manifest":
        risk_flags.append("scanner_must_use_manifest")
        if not manifest_exists:
            risk_flags.append("missing_manifest")
        elif manifest_stats.get("unresolved_titles", 0):
            risk_flags.append("manifest_has_unresolved_titles")
    if collection["update_strategy"] != "append":
        risk_flags.append("generic_updater_disabled")
    if collection["collection_type"] == "multi_channel_curated":
        risk_flags.append("mixed_source_collection")
    if collection["collection_type"] == "legacy_mixed_format":
        risk_flags.append("legacy_mixed_format")
    if oversized_files:
        risk_flags.append("oversized_bundle_files")
    if not transcript_dir.exists():
        risk_flags.append("missing_transcript_dir")
    if raw_only_video_ids:
        risk_flags.append("raw_transcripts_not_merged")
    if raw_snapshot["non_video_id_files"]:
        risk_flags.append("nonstandard_raw_filenames")

    return {
        "collection_key": collection_key,
        "collection_type": collection["collection_type"],
        "scan_strategy": collection["scan_strategy"],
        "update_strategy": collection["update_strategy"],
        "transcript_dir": str(transcript_dir),
        "transcript_dir_exists": transcript_dir.exists(),
        "raw_dir": str(raw_dir) if raw_dir else "",
        "raw_dir_exists": raw_dir.exists() if raw_dir else False,
        "raw_markdown_files": raw_snapshot["markdown_files"],
        "raw_video_id_files": raw_snapshot["video_id_files"],
        "raw_non_video_id_files": raw_snapshot["non_video_id_files"],
        "markdown_files": len(bundle_files),
        "bundle_role_counts": bundle_role_counts,
        "local_unique_video_ids": unique_video_ids,
        "local_unique_titles": unique_titles,
        "duplicate_video_id_groups": duplicated_video_id_count,
        "duplicate_normalized_title_groups": duplicated_title_count,
        "raw_only_video_ids_count": len(raw_only_video_ids),
        "merged_only_video_ids_count": len(merged_only_video_ids),
        "raw_only_video_ids_sample": raw_only_video_ids[:10],
        "merged_only_video_ids_sample": merged_only_video_ids[:10],
        "manifest_exists": manifest_exists,
        "manifest_unique_videos": manifest_stats.get("unique_matched_videos", 0),
        "manifest_unresolved_titles": manifest_stats.get("unresolved_titles", 0),
        "oversized_files": oversized_files,
        "risk_flags": sorted(set(risk_flags)),
    }


def _build_cross_collection_duplicates(collections: dict[str, dict]) -> dict:
    video_groups: dict[str, set[str]] = {}
    title_groups: dict[str, set[str]] = {}

    for collection_key, collection in collections.items():
        overrides = load_collection_overrides(collection_key)
        for bundle_path in discover_bundle_files(collection):
            role = classify_bundle_role(bundle_path.name, collection, overrides)
            if role == "reference_only":
                continue
            for candidate in extract_candidates_from_bundle(bundle_path, overrides.get("ignored_titles", [])):
                video_id = candidate.get("video_id") or ""
                if video_id:
                    video_groups.setdefault(video_id, set()).add(collection_key)
                title_groups.setdefault(candidate["normalized_title"], set()).add(collection_key)

    return {
        "video_ids": [
            {"video_id": video_id, "collections": sorted(names)}
            for video_id, names in sorted(video_groups.items())
            if len(names) > 1
        ],
        "normalized_titles": [
            {"normalized_title": title, "collections": sorted(names)}
            for title, names in sorted(title_groups.items())
            if len(names) > 1
        ],
    }


def _build_low_confidence_scan_report(pending: dict) -> list[dict]:
    findings = []
    for collection_key, record in sorted(pending.get("collections", {}).items()):
        confidence_summary = record.get("confidence_summary", {})
        reasons = []
        if confidence_summary.get("medium", 0):
            reasons.append("medium-confidence title matching still present")
        if confidence_summary.get("manual_review", 0):
            reasons.append("manual-review provenance entries still present")
        if record.get("unresolved_count", 0):
            reasons.append("unresolved titles remain in manifest coverage")
        if any("Title fallback" in note for note in record.get("scan_notes", [])):
            reasons.append("inline scan still relies on title fallback")

        if reasons:
            findings.append(
                {
                    "collection_key": collection_key,
                    "confidence_summary": confidence_summary,
                    "unresolved_count": record.get("unresolved_count", 0),
                    "reasons": reasons,
                }
            )

    return findings


def _build_markdown_report(payload: dict) -> str:
    lines = [
        "# Collection Audit",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Registry collections: {payload['summary']['registry_collections']}",
        f"- Transcript namespaces on disk: {payload['summary']['transcript_namespaces']}",
        f"- Registry-only entries: {len(payload['registry_only'])}",
        f"- Disk-only namespaces: {len(payload['disk_only'])}",
        f"- Oversized bundle files: {payload['summary']['oversized_bundle_files']}",
        f"- Auto-update blocked collections: {payload['summary']['auto_update_blocked_collections']}",
        f"- Low-confidence scan findings: {len(payload['low_confidence_scans'])}",
        f"- Raw/chunk sync findings: {len(payload['raw_sync_findings'])}",
        "",
        "## Registry Drift",
        "",
    ]

    if payload["registry_only"]:
        lines.append(f"- Registry entries missing transcript folders: {', '.join(payload['registry_only'])}")
    else:
        lines.append("- No registry entries are missing transcript folders.")

    if payload["disk_only"]:
        lines.append(f"- Transcript folders missing from the registry: {', '.join(payload['disk_only'])}")
    else:
        lines.append("- No transcript folders are missing from the registry.")

    lines.extend(["", "## Wave 1 High-Risk Collections", ""])
    for key in ["Solar_Athlete", "Alex_Kikel", "Professor_Jiang", "Huberman"]:
        collection = payload["collections"].get(key)
        if not collection:
            continue
        lines.extend(
            [
                f"### {key}",
                "",
                f"- Type: `{collection['collection_type']}`",
                f"- Scan strategy: `{collection['scan_strategy']}`",
                f"- Update strategy: `{collection['update_strategy']}`",
                f"- Markdown files: {collection['markdown_files']}",
                f"- Local unique video IDs: {collection['local_unique_video_ids']}",
                f"- Local unique titles: {collection['local_unique_titles']}",
                f"- Manifest exists: {collection['manifest_exists']}",
                f"- Manifest unique videos: {collection['manifest_unique_videos']}",
                f"- Manifest unresolved titles: {collection['manifest_unresolved_titles']}",
                f"- Duplicate title groups: {collection['duplicate_normalized_title_groups']}",
                f"- Oversized files: {len(collection['oversized_files'])}",
                f"- Raw markdown files: {collection['raw_markdown_files']}",
                f"- Raw-only video IDs: {collection['raw_only_video_ids_count']}",
                f"- Merged-only video IDs: {collection['merged_only_video_ids_count']}",
                f"- Risk flags: {', '.join(collection['risk_flags']) or 'none'}",
                "",
            ]
        )

    lines.extend(
        [
            "## Collection Summary",
            "",
            "| Collection | Type | Scan | Update | Raw MD | Raw IDs | Merged MD | Merged IDs | Raw Only | Merged Only | Manifest | Unresolved | Oversized | Risks |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
        ]
    )

    for key, collection in sorted(payload["collections"].items()):
        lines.append(
            "| {key} | {type} | {scan} | {update} | {raw_md} | {raw_ids} | {md} | {ids} | {raw_only} | {merged_only} | {manifest} | {unresolved} | {oversized} | {risks} |".format(
                key=key,
                type=collection["collection_type"],
                scan=collection["scan_strategy"],
                update=collection["update_strategy"],
                raw_md=collection["raw_markdown_files"],
                raw_ids=collection["raw_video_id_files"],
                md=collection["markdown_files"],
                ids=collection["local_unique_video_ids"],
                raw_only=collection["raw_only_video_ids_count"],
                merged_only=collection["merged_only_video_ids_count"],
                manifest="yes" if collection["manifest_exists"] else "no",
                unresolved=collection["manifest_unresolved_titles"],
                oversized=len(collection["oversized_files"]),
                risks=", ".join(collection["risk_flags"]) or "none",
            )
        )

    lines.extend(["", "## Raw vs Chunk Sync Findings", ""])
    if payload["raw_sync_findings"]:
        for item in payload["raw_sync_findings"]:
            lines.append(
                "- {key}: raw_only={raw_only}, merged_only={merged_only}, nonstandard_raw={nonstandard}, raw_only_sample={raw_sample}, merged_only_sample={merged_sample}".format(
                    key=item["collection_key"],
                    raw_only=item["raw_only_video_ids_count"],
                    merged_only=item["merged_only_video_ids_count"],
                    nonstandard=item["raw_non_video_id_files"],
                    raw_sample=", ".join(item["raw_only_video_ids_sample"]) or "none",
                    merged_sample=", ".join(item["merged_only_video_ids_sample"]) or "none",
                )
            )
    else:
        lines.append("- No raw/chunk mismatches detected.")

    lines.extend(["", "## Low-Confidence Scan Findings", ""])
    if payload["low_confidence_scans"]:
        for item in payload["low_confidence_scans"]:
            lines.append(
                "- {key}: medium={medium}, manual_review={manual_review}, unresolved={unresolved}, reasons={reasons}".format(
                    key=item["collection_key"],
                    medium=item["confidence_summary"].get("medium", 0),
                    manual_review=item["confidence_summary"].get("manual_review", 0),
                    unresolved=item.get("unresolved_count", 0),
                    reasons="; ".join(item.get("reasons", [])) or "none",
                )
            )
    else:
        lines.append("- None detected.")

    lines.extend(["", "## Auto-Update Blocked Collections", ""])
    for key in payload["auto_update_blocked"]:
        lines.append(f"- {key}")

    cross_video = payload["cross_collection_duplicates"]["video_ids"][:10]
    cross_titles = payload["cross_collection_duplicates"]["normalized_titles"][:10]

    lines.extend(["", "## Cross-Collection Duplicate Video IDs", ""])
    if cross_video:
        for item in cross_video:
            lines.append(f"- `{item['video_id']}` -> {', '.join(item['collections'])}")
    else:
        lines.append("- None detected.")

    lines.extend(["", "## Cross-Collection Duplicate Titles", ""])
    if cross_titles:
        for item in cross_titles:
            lines.append(f"- `{item['normalized_title']}` -> {', '.join(item['collections'])}")
    else:
        lines.append("- None detected.")

    return "\n".join(lines) + "\n"


def main() -> int:
    ensure_output_dirs()
    collections = load_collection_registry()
    transcript_namespaces = sorted(
        p.name
        for p in Path("transcripts").iterdir()
        if p.is_dir() and not p.name.endswith("_Raw") and "QA_Sources" not in p.name
    )

    registry_namespaces = sorted(collections.keys())
    registry_only = [name for name in registry_namespaces if not resolve_collection_transcript_dir(collections[name]).exists()]
    disk_only = [name for name in transcript_namespaces if name not in collections]

    collection_snapshots = {
        key: _local_collection_snapshot(key, collection)
        for key, collection in collections.items()
    }
    cross_duplicates = _build_cross_collection_duplicates(collections)

    pending = load_json(Path("yt_processor/pending_updates.json"), default={})
    pending_summary = {}
    for key, record in pending.get("collections", {}).items():
        pending_summary[key] = {
            "new_count": record.get("new_count", 0),
            "scan_strategy": record.get("scan_strategy"),
            "collection_type": record.get("collection_type"),
        }

    auto_update_blocked = sorted(
        key
        for key, collection in collections.items()
        if collection["collection_type"] != "single_channel_appendable" or collection["update_strategy"] != "append"
    )
    low_confidence_scans = _build_low_confidence_scan_report(pending)
    raw_sync_findings = [
        {
            "collection_key": key,
            "collection_type": snapshot["collection_type"],
            "raw_only_video_ids_count": snapshot["raw_only_video_ids_count"],
            "merged_only_video_ids_count": snapshot["merged_only_video_ids_count"],
            "raw_non_video_id_files": snapshot["raw_non_video_id_files"],
            "raw_only_video_ids_sample": snapshot["raw_only_video_ids_sample"],
            "merged_only_video_ids_sample": snapshot["merged_only_video_ids_sample"],
        }
        for key, snapshot in sorted(collection_snapshots.items())
        if snapshot["raw_only_video_ids_count"]
        or snapshot["merged_only_video_ids_count"]
        or snapshot["raw_non_video_id_files"]
    ]

    payload = {
        "generated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "summary": {
            "registry_collections": len(registry_namespaces),
            "transcript_namespaces": len(transcript_namespaces),
            "oversized_bundle_files": sum(len(item["oversized_files"]) for item in collection_snapshots.values()),
            "auto_update_blocked_collections": len(auto_update_blocked),
        },
        "registry_only": registry_only,
        "disk_only": disk_only,
        "collections": collection_snapshots,
        "cross_collection_duplicates": cross_duplicates,
        "pending_summary": pending_summary,
        "auto_update_blocked": auto_update_blocked,
        "low_confidence_scans": low_confidence_scans,
        "raw_sync_findings": raw_sync_findings,
    }

    json_path = REPORTS_DIR / "collection_audit.json"
    md_path = REPORTS_DIR / "collection_audit.md"
    save_json(json_path, payload)
    md_path.write_text(_build_markdown_report(payload), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
