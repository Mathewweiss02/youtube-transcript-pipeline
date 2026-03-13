#!/usr/bin/env python3
"""
Universal transcript chunker.

Supports:
- `--collection` for appendable collections in `collection_registry.json`
- `--input-dir` / `--output-dir` / `--base-name` for manual use

If no arguments are provided, it falls back to the legacy Hyperarch defaults.
"""

from __future__ import annotations

import argparse
import re
import shutil
import tempfile
from pathlib import Path

from collection_utils import (
    MAX_CHUNK_SIZE,
    load_collection_registry,
    resolve_collection_raw_dir,
    resolve_collection_transcript_dir,
)


CHUNK_FILE_RE = re.compile(r"(?:PART|CHUNK|CONSOLIDATED_PART)_(\d+)\.md$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chunk raw transcript markdown files into merged PART files.")
    parser.add_argument("--collection", help="Appendable collection key from collection_registry.json")
    parser.add_argument("--input-dir", type=Path, help="Directory containing raw transcript .md files")
    parser.add_argument("--output-dir", type=Path, help="Directory to write merged chunk files")
    parser.add_argument("--base-name", help="Base name used in chunk titles and filenames")
    parser.add_argument("--chunk-file-template", help="Optional filename template, e.g. 'NAME_PART_{num:02d}.md'")
    parser.add_argument(
        "--sort",
        choices=("mtime", "name"),
        default="mtime",
        help="Sort raw files by modified time or filename before chunking",
    )
    parser.add_argument(
        "--max-chunk-size-mb",
        type=float,
        default=MAX_CHUNK_SIZE / 1024 / 1024,
        help="Maximum chunk size in megabytes",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing PART/CHUNK files in the output directory after a successful staged build",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written without touching files")
    return parser.parse_args()


def derive_default_output_dir(input_dir: Path) -> Path:
    if input_dir.name.endswith("_Raw"):
        return input_dir.parent / input_dir.name[: -len("_Raw")]
    return input_dir.parent / f"{input_dir.name}_chunked"


def derive_default_base_name(input_dir: Path) -> str:
    name = input_dir.name
    if name.endswith("_Raw"):
        name = name[: -len("_Raw")]
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return name.replace("-", "_").replace(" ", "_").upper()


def resolve_collection_settings(collection_key: str) -> dict:
    collections = load_collection_registry()
    lower_map = {key.lower(): key for key in collections}
    resolved_key = collection_key if collection_key in collections else lower_map.get(collection_key.lower())
    if not resolved_key:
        raise ValueError(f"Collection '{collection_key}' not found in collection_registry.json")

    collection = collections[resolved_key]
    if collection["collection_type"] != "single_channel_appendable" or collection["update_strategy"] != "append":
        raise ValueError(
            f"Collection '{resolved_key}' is not append-safe. Use explicit --input-dir/--output-dir for manual chunking."
        )

    input_dir = resolve_collection_raw_dir(collection)
    if input_dir is None:
        raise ValueError(f"Collection '{resolved_key}' does not define raw_dir")

    return {
        "collection_key": resolved_key,
        "input_dir": input_dir,
        "output_dir": resolve_collection_transcript_dir(collection),
        "base_name": collection.get("base_name", resolved_key),
        "chunk_file_template": collection.get("chunk_file_template"),
    }


def resolve_settings(args: argparse.Namespace) -> dict:
    if args.collection:
        settings = resolve_collection_settings(args.collection)
        input_dir = settings["input_dir"]
        output_dir = settings["output_dir"]
        base_name = settings["base_name"]
        chunk_file_template = settings["chunk_file_template"]
    else:
        if args.input_dir is None:
            raise ValueError("Either --collection or --input-dir is required.")
        input_dir = args.input_dir
        output_dir = args.output_dir or derive_default_output_dir(input_dir)
        base_name = args.base_name or derive_default_base_name(input_dir)
        chunk_file_template = args.chunk_file_template

    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "base_name": base_name,
        "chunk_file_template": chunk_file_template,
        "sort_mode": args.sort,
        "max_chunk_size": int(args.max_chunk_size_mb * 1024 * 1024),
        "replace_existing": args.replace_existing,
        "dry_run": args.dry_run,
    }


def list_raw_markdown_files(input_dir: Path, sort_mode: str) -> list[Path]:
    files = [path for path in input_dir.glob("*.md") if path.is_file()]
    if sort_mode == "name":
        return sorted(files, key=lambda path: path.name.lower())
    return sorted(files, key=lambda path: (path.stat().st_mtime, path.name.lower()))


def parse_transcript_file(path: Path) -> dict | None:
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    title = None
    url = None
    transcript_lines: list[str] = []

    for index, line in enumerate(lines):
        if line.startswith("# ") and title is None:
            title = line.lstrip("#").strip()
        elif line.startswith("URL: ") and url is None:
            url = line.replace("URL: ", "", 1).strip()
        elif line.strip() == "---":
            transcript_lines = lines[index + 1 :]
            break

    if not title or not url:
        return None

    transcript_text = "\n".join(transcript_lines).strip()
    if not transcript_text:
        return None

    transcript_text = re.sub(r"\[Music\]", "", transcript_text)
    transcript_text = transcript_text.strip()
    if not transcript_text:
        return None

    return {
        "source_file": path.name,
        "title": title,
        "url": url,
        "content": transcript_text,
    }


def parse_transcripts(input_dir: Path, sort_mode: str) -> tuple[list[dict], list[str]]:
    sections: list[dict] = []
    skipped: list[str] = []

    for md_file in list_raw_markdown_files(input_dir, sort_mode):
        parsed = parse_transcript_file(md_file)
        if parsed is None:
            skipped.append(md_file.name)
            continue
        sections.append(parsed)

    return sections, skipped


def format_video_section(section: dict) -> str:
    return (
        f"# {section['title']}\n\n"
        f"URL: {section['url']}\n\n"
        "---\n\n"
        f"{section['content']}\n"
    )


def build_chunk_filename(chunk_num: int, base_name: str, chunk_file_template: str | None) -> str:
    if chunk_file_template:
        return chunk_file_template.format(num=chunk_num)
    return f"{base_name.replace(' ', '_')}_PART_{chunk_num:02d}.md"


def render_chunk_content(base_name: str, chunk_num: int, videos: list[dict]) -> str:
    title_lines = "\n".join(f"{index}. {video['title']}" for index, video in enumerate(videos, start=1))
    body = "\n\n---\n\n".join(format_video_section(video).strip() for video in videos)
    return (
        f"# {base_name} - Part {chunk_num:02d}\n"
        "## Table of Contents\n\n"
        f"{title_lines}\n\n"
        + "=" * 80
        + "\n\n"
        + body
        + "\n"
    )


def build_chunk_plan(
    sections: list[dict],
    base_name: str,
    chunk_file_template: str | None,
    max_chunk_size: int,
) -> list[dict]:
    plan: list[dict] = []
    current_videos: list[dict] = []
    chunk_num = 1

    for section in sections:
        candidate_videos = current_videos + [section]
        candidate_content = render_chunk_content(base_name, chunk_num, candidate_videos)
        candidate_size = len(candidate_content.encode("utf-8"))

        if candidate_size > max_chunk_size and current_videos:
            final_content = render_chunk_content(base_name, chunk_num, current_videos)
            plan.append(
                {
                    "chunk_num": chunk_num,
                    "filename": build_chunk_filename(chunk_num, base_name, chunk_file_template),
                    "content": final_content,
                    "video_count": len(current_videos),
                    "size_bytes": len(final_content.encode("utf-8")),
                }
            )
            chunk_num += 1
            current_videos = [section]
        else:
            current_videos = candidate_videos

    if current_videos:
        final_content = render_chunk_content(base_name, chunk_num, current_videos)
        plan.append(
            {
                "chunk_num": chunk_num,
                "filename": build_chunk_filename(chunk_num, base_name, chunk_file_template),
                "content": final_content,
                "video_count": len(current_videos),
                "size_bytes": len(final_content.encode("utf-8")),
            }
        )

    return plan


def find_existing_chunk_files(output_dir: Path) -> list[Path]:
    if not output_dir.exists():
        return []
    return sorted(
        [
            path
            for path in output_dir.glob("*.md")
            if path.is_file() and CHUNK_FILE_RE.search(path.name)
        ],
        key=lambda path: path.name.lower(),
    )


def write_chunk_plan(output_dir: Path, plan: list[dict], replace_existing: bool) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".chunk_build_", dir=str(output_dir.parent)))
    written_paths: list[Path] = []
    deleted_files: list[str] = []

    try:
        staged_paths: list[Path] = []
        for item in plan:
            staged_path = temp_dir / item["filename"]
            staged_path.write_text(item["content"], encoding="utf-8")
            staged_paths.append(staged_path)

        existing_files = find_existing_chunk_files(output_dir) if replace_existing else []

        for staged_path in staged_paths:
            final_path = output_dir / staged_path.name
            staged_path.replace(final_path)
            written_paths.append(final_path)

        if replace_existing:
            written_names = {path.name for path in written_paths}
            for existing_path in existing_files:
                if existing_path.name in written_names:
                    continue
                try:
                    existing_path.unlink()
                    deleted_files.append(existing_path.name)
                except OSError:
                    pass
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return {
        "written_paths": written_paths,
        "deleted_files": deleted_files,
    }


def chunk_transcripts(
    input_dir: Path,
    output_dir: Path,
    base_name: str,
    chunk_file_template: str | None = None,
    sort_mode: str = "mtime",
    max_chunk_size: int = MAX_CHUNK_SIZE,
    replace_existing: bool = False,
    dry_run: bool = False,
) -> dict:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    sections, skipped_files = parse_transcripts(input_dir, sort_mode)
    if not sections:
        raise ValueError(f"No valid transcript files found in {input_dir}")

    plan = build_chunk_plan(sections, base_name, chunk_file_template, max_chunk_size)
    result = {
        "section_count": len(sections),
        "skipped_files": skipped_files,
        "plan": plan,
        "written_paths": [],
        "deleted_files": [],
    }

    if dry_run:
        return result

    write_result = write_chunk_plan(output_dir, plan, replace_existing)
    result["written_paths"] = write_result["written_paths"]
    result["deleted_files"] = write_result["deleted_files"]
    return result


def print_summary(settings: dict, result: dict):
    print("=" * 80)
    print("UNIVERSAL TRANSCRIPT CHUNKER")
    print("=" * 80)
    print(f"Input directory: {settings['input_dir'].resolve()}")
    print(f"Output directory: {settings['output_dir'].resolve()}")
    print(f"Base name: {settings['base_name']}")
    print(f"Sort mode: {settings['sort_mode']}")
    print(f"Max chunk size: {settings['max_chunk_size'] / 1024 / 1024:.2f} MB")
    if settings["dry_run"]:
        print("Mode: DRY RUN")
    print()
    print(f"Valid transcript files: {result['section_count']}")
    print(f"Skipped files: {len(result['skipped_files'])}")
    print(f"Chunks planned: {len(result['plan'])}")
    print()

    for item in result["plan"]:
        print(
            f"  -> {item['filename']} "
            f"({item['size_bytes'] / 1024 / 1024:.2f} MB, {item['video_count']} videos)"
        )

    if result["skipped_files"]:
        print()
        print("Skipped files:")
        for name in result["skipped_files"][:15]:
            print(f"  - {name}")
        if len(result["skipped_files"]) > 15:
            print(f"  ... and {len(result['skipped_files']) - 15} more")

    if settings["dry_run"]:
        return

    print()
    print("=" * 80)
    print("CHUNKING COMPLETE")
    print("=" * 80)
    print(f"Written chunks: {len(result['written_paths'])}")
    if result["deleted_files"]:
        print(f"Deleted old chunk files: {len(result['deleted_files'])}")
    print(f"Output directory: {settings['output_dir'].resolve()}")


def main() -> int:
    args = parse_args()
    settings = resolve_settings(args)

    result = chunk_transcripts(
        input_dir=settings["input_dir"],
        output_dir=settings["output_dir"],
        base_name=settings["base_name"],
        chunk_file_template=settings["chunk_file_template"],
        sort_mode=settings["sort_mode"],
        max_chunk_size=settings["max_chunk_size"],
        replace_existing=settings["replace_existing"],
        dry_run=settings["dry_run"],
    )
    print_summary(settings, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
