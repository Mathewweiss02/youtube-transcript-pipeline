#!/usr/bin/env python3
"""
Merge cleaned transcripts into markdown files with TOC and headers.
- Solar Athlete: numeric order (1-144)
- Jay Campbell: alphabetical order (order doesn't matter)
Outputs: MERGED_Solar_Athlete.md and MERGED_Jay_Campbell.md in project root.
"""

import re
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path("C:/Users/aweis/Downloads/New folder (3)")
TRANSCRIPTS_ROOT = PROJECT_ROOT / "transcripts"

def extract_episode_number(name: str) -> Tuple[int, str]:
    """
    Extract numeric episode order from filename.
    Handles patterns like "Vlog 1", "Ep 144", "BSH Ep 128", etc.
    Returns (order, cleaned_name). If no number, returns (999999, name).
    """
    # Try to match patterns like "Vlog 1", "Ep 144", "BSH Ep 128"
    m = re.search(r"(?:Vlog|Ep|BSH Ep)\s*(\d+)", name, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        return num, name
    # Fallback: any number in filename
    m = re.search(r"(\d+)", name)
    if m:
        num = int(m.group(1))
        return num, name
    return 999999, name

def slugify(title: str) -> str:
    """Create a URL-safe anchor ID from title."""
    # Remove file extension
    title = title.replace(".en.txt", "")
    # Strip leading numbers, dashes, spaces
    title = title.lstrip("0123456789-. ")
    # Replace non-alphanumeric with dash, lowercase
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    # Ensure anchor doesn't start with a digit (prepend 'ep-' if it does)
    if slug and slug[0].isdigit():
        slug = "ep-" + slug
    return slug or "anchor"

def list_clean_files(folder: Path) -> List[Path]:
    """Return list of .en.txt files in a folder."""
    if not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")
    return sorted([p for p in folder.iterdir() if p.is_file() and p.name.endswith(".en.txt")])

def build_toc(entries: List[Tuple[str, str]]) -> str:
    """Build markdown TOC from list of (title, anchor)."""
    lines = ["## Table of Contents\n"]
    for title, anchor in entries:
        lines.append(f"- [{title}](#{anchor})")
    return "\n".join(lines) + "\n\n"

def merge_folder(
    folder: Path,
    output_path: Path,
    title: str,
    description: str,
    numeric_sort: bool = False,
) -> None:
    """Merge all .en.txt files in folder into a single markdown file."""
    files = list_clean_files(folder)
    if not files:
        raise SystemExit(f"No .en.txt files found in {folder}")

    # Sort files
    if numeric_sort:
        files.sort(key=lambda p: extract_episode_number(p.name)[0])
    else:
        files.sort()

    # Prepare TOC entries
    toc_entries = []
    for p in files:
        clean_name = p.name.replace(".en.txt", "")
        anchor = slugify(clean_name)
        toc_entries.append((clean_name, anchor))

    # Write markdown
    with output_path.open("w", encoding="utf-8") as out:
        out.write(f"# {title}\n\n")
        out.write(f"{description}\n\n---\n\n")
        out.write(build_toc(toc_entries))
        for p in files:
            clean_name = p.name.replace(".en.txt", "")
            anchor = slugify(clean_name)
            out.write(f"### <a id=\"{anchor}\"></a>{clean_name}\n\n")
            content = p.read_text("utf-8").strip()
            out.write(content)
            out.write("\n\n---\n\n")
    print(f"Wrote {output_path} with {len(files)} transcripts")

def main() -> None:
    # Paths
    solar_clean = TRANSCRIPTS_ROOT / "solar athlete info" / "clean"
    jay_clean = TRANSCRIPTS_ROOT / "jay_campbell_playlist" / "playlist_transcripts"

    # Output files in project root
    out_solar = PROJECT_ROOT / "MERGED_Solar_Athlete.md"
    out_jay = PROJECT_ROOT / "MERGED_Jay_Campbell.md"

    # Merge Solar Athlete (numeric order)
    merge_folder(
        solar_clean,
        out_solar,
        title="Solar Athlete (Juris Skribans) Series",
        description="Complete transcript collection of the BSH and Vlog episodes in numeric order.",
        numeric_sort=True,
    )

    # Merge Jay Campbell (alphabetical)
    merge_folder(
        jay_clean,
        out_jay,
        title="Jay Campbell Podcast Series",
        description="Complete transcript collection of Jay Campbell podcast episodes.",
        numeric_sort=False,
    )

if __name__ == "__main__":
    main()
