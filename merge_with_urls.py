#!/usr/bin/env python3
"""
Merge transcripts with YouTube URLs included.
Reads from URL map JSON and adds URLs under each transcript title.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple

def slugify(title: str) -> str:
    """Create a URL-safe anchor ID from title."""
    title = title.replace(".en.txt", "").replace(".txt", "")
    title = title.lstrip("0123456789-. ")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    if slug and slug[0].isdigit():
        slug = "ep-" + slug
    return slug or "anchor"

def load_url_map(map_path: Path) -> Dict[str, str]:
    """Load video title -> URL mapping from JSON."""
    with open(map_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create flexible lookup (title -> url)
    url_lookup = {}
    for title, info in data.get('videos', {}).items():
        url = info.get('url', '')
        url_lookup[title] = url
        url_lookup[title.lower()] = url
        url_lookup[title.replace(':', '').strip()] = url
        url_lookup[title.lower().replace(':', '').strip()] = url
        # Remove common suffixes
        for suffix in [' - Predictive History', ' | Predictive History', ' Predictive History']:
            clean = title.replace(suffix, '').strip()
            url_lookup[clean] = url
            url_lookup[clean.lower()] = url
    return url_lookup

def find_url(title: str, url_lookup: Dict[str, str], raw_files: Dict[str, str]) -> Optional[str]:
    """Find YouTube URL for a transcript title."""
    # Try direct match
    if title in url_lookup:
        return url_lookup[title]
    if title.lower() in url_lookup:
        return url_lookup[title.lower()]
    
    # Try matching by video ID from raw filename
    for raw_name, url in raw_files.items():
        vid_id = raw_name.replace('.md', '').replace('.txt', '')
        if vid_id in url:
            return url
    
    # Try partial title match
    title_clean = title.lower().replace(':', '').replace('-', ' ').strip()
    for mapped_title, url in url_lookup.items():
        mapped_clean = mapped_title.lower().replace(':', '').replace('-', ' ').strip()
        if title_clean in mapped_clean or mapped_clean in title_clean:
            return url
    
    return None

def build_toc(entries: List[Tuple[str, str]]) -> str:
    """Build markdown TOC from list of (title, anchor)."""
    lines = ["## Table of Contents\n"]
    for title, anchor in entries:
        lines.append(f"- [{title}](#{anchor})")
    return "\n".join(lines) + "\n\n"

def merge_transcripts_with_urls(
    transcript_dir: Path,
    raw_dir: Path,
    output_path: Path,
    url_map_path: Path,
    title: str,
    description: str,
    channel_url: str = ""
) -> None:
    """Merge all transcript files with YouTube URLs."""
    
    # Load URL mapping
    url_lookup = load_url_map(url_map_path)
    
    # Get raw files (for video ID matching)
    raw_files = {}
    if raw_dir.exists():
        for f in raw_dir.iterdir():
            if f.is_file() and (f.suffix == '.md' or f.suffix == '.txt'):
                raw_files[f.name] = f"https://www.youtube.com/watch?v={f.stem}"
    
    # Get transcript files
    transcript_files = []
    for f in transcript_dir.iterdir():
        if f.is_file() and (f.suffix == '.txt' or f.suffix == '.md'):
            if 'MERGED' not in f.name and 'INDEX' not in f.name:
                transcript_files.append(f)
    
    transcript_files.sort()
    
    # Prepare TOC entries
    toc_entries = []
    for p in transcript_files:
        clean_name = p.stem if p.suffix in ['.txt', '.md'] else p.name
        anchor = slugify(clean_name)
        toc_entries.append((clean_name, anchor))
    
    # Write markdown
    with output_path.open("w", encoding="utf-8") as out:
        out.write(f"# {title}\n\n")
        out.write(f"{description}\n\n")
        if channel_url:
            out.write(f"**Channel:** {channel_url}\n\n")
        out.write("---\n\n")
        out.write(build_toc(toc_entries))
        
        for p in transcript_files:
            clean_name = p.stem if p.suffix in ['.txt', '.md'] else p.name
            anchor = slugify(clean_name)
            
            # Find URL
            url = find_url(clean_name, url_lookup, raw_files)
            
            # Write header with URL
            out.write(f"### <a id=\"{anchor}\"></a>{clean_name}\n\n")
            if url:
                out.write(f"**YouTube:** {url}\n\n")
            
            # Write content
            content = p.read_text("utf-8").strip()
            out.write(content)
            out.write("\n\n---\n\n")
    
    print(f"Wrote {output_path} with {len(transcript_files)} transcripts")

def main():
    base = Path("C:/Users/aweis/Downloads/YouTube_Tools_Scripts")
    
    # Professor Jiang
    merge_transcripts_with_urls(
        transcript_dir=base / "transcripts" / "Professor_Jiang",
        raw_dir=base / "transcripts" / "Professor_Jiang_Raw",
        output_path=base / "transcripts" / "Professor_Jiang" / "MERGED_ALL_Prof_JIANG_TRANSCRIPTS.md",
        url_map_path=base / "yt_processor" / "prof_jiang_url_map.json",
        title="Complete Transcripts Collection - Professor Jiang's Lectures",
        description="All transcripts from Professor Jiang's Predictive History channel, organized by series.",
        channel_url="https://www.youtube.com/@PredictiveHistory"
    )

if __name__ == "__main__":
    main()
