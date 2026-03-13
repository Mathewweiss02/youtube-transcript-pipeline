#!/usr/bin/env python3
"""Normalize raw transcript filenames to YouTube video IDs.

This is designed for legacy raw folders that contain title-named markdown files.
If a title-named file already has a canonical `VIDEOID.md` counterpart, the
legacy file is moved into an archive directory instead of being deleted.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from . import collection_utils as cu
except ImportError:
    import collection_utils as cu


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize raw transcript filenames to YouTube IDs.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Raw transcript directory to normalize")
    parser.add_argument(
        "--archive-dir",
        type=Path,
        help="Directory to move legacy duplicate files into (defaults to sibling *_Legacy folder)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without moving files")
    return parser.parse_args()


def is_canonical_video_file(path: Path) -> bool:
    return len(path.stem) == 11 and path.suffix.lower() == ".md"


def extract_video_id_from_file(path: Path) -> str:
    if is_canonical_video_file(path):
        return path.stem

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    match = cu.URL_RE.search(text)
    return match.group(1) if match else ""


def normalize_raw_transcripts(input_dir: Path, archive_dir: Path, dry_run: bool = False) -> dict[str, int]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    summary = {
        "kept_canonical": 0,
        "renamed_to_canonical": 0,
        "archived_duplicates": 0,
        "skipped_without_video_id": 0,
    }

    planned_archives: list[tuple[Path, Path]] = []
    planned_renames: list[tuple[Path, Path]] = []

    for path in sorted(input_dir.glob("*.md")):
        if not path.is_file():
            continue

        video_id = extract_video_id_from_file(path)
        if not video_id:
            summary["skipped_without_video_id"] += 1
            continue

        canonical_path = input_dir / f"{video_id}.md"
        if path == canonical_path:
            summary["kept_canonical"] += 1
            continue

        if canonical_path.exists():
            planned_archives.append((path, archive_dir / path.name))
            summary["archived_duplicates"] += 1
        else:
            planned_renames.append((path, canonical_path))
            summary["renamed_to_canonical"] += 1

    if dry_run:
        return summary

    archive_dir.mkdir(parents=True, exist_ok=True)

    for source, target in planned_archives:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)

    for source, target in planned_renames:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)

    return summary


def main() -> int:
    args = parse_args()
    archive_dir = args.archive_dir or (args.input_dir.parent / f"{args.input_dir.name}_Legacy")
    summary = normalize_raw_transcripts(args.input_dir, archive_dir, dry_run=args.dry_run)

    print("=" * 80)
    print("RAW TRANSCRIPT NORMALIZATION")
    print("=" * 80)
    print(f"Input: {args.input_dir.resolve()}")
    print(f"Archive: {archive_dir.resolve()}")
    print(f"Dry run: {'yes' if args.dry_run else 'no'}")
    print()
    print(f"Canonical already kept: {summary['kept_canonical']}")
    print(f"Renamed to canonical: {summary['renamed_to_canonical']}")
    print(f"Archived duplicate legacy files: {summary['archived_duplicates']}")
    print(f"Skipped without video ID: {summary['skipped_without_video_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
