#!/usr/bin/env python3
"""
Inject YouTube URLs into existing merged transcript files.
Reads the merged file, matches titles with URL map, adds URLs under headers.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional

def load_url_map(map_path: Path) -> Dict[str, str]:
    """Load video title -> URL mapping from JSON."""
    with open(map_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    url_lookup = {}
    for title, info in data.get('videos', {}).items():
        url = info.get('url', '')
        # Multiple variations for matching
        url_lookup[title] = url
        url_lookup[title.lower()] = url
        url_lookup[title.replace(':', '').strip()] = url
        url_lookup[title.lower().replace(':', '').strip()] = url
        # Remove series prefixes for matching
        for prefix in ['Civilization #', 'Secret History #', 'Geo-Strategy #', 'Game Theory #', 'Great Books #']:
            if prefix in title:
                # Extract just the title part
                match = re.search(rf'{re.escape(prefix)}\d*\s*(.+)', title)
                if match:
                    subtitle = match.group(1).strip()
                    url_lookup[subtitle] = url
                    url_lookup[subtitle.lower()] = url
        # Remove channel suffix
        for suffix in [' - Predictive History', ' | Predictive History', ' Predictive History']:
            clean = title.replace(suffix, '').strip()
            url_lookup[clean] = url
            url_lookup[clean.lower()] = url
    return url_lookup

def find_url_for_title(title: str, url_lookup: Dict[str, str]) -> Optional[str]:
    """Find YouTube URL for a transcript title."""
    # Clean the title
    title_clean = title.strip()
    
    # Direct match
    if title_clean in url_lookup:
        return url_lookup[title_clean]
    if title_clean.lower() in url_lookup:
        return url_lookup[title_clean.lower()]
    
    # Remove common variations
    title_variations = [
        title_clean,
        title_clean.lower(),
        title_clean.replace(':', '').strip(),
        title_clean.lower().replace(':', '').strip(),
        re.sub(r'\s+', ' ', title_clean),  # normalize spaces
    ]
    
    for var in title_variations:
        if var in url_lookup:
            return url_lookup[var]
        # Try partial match
        for mapped_title, url in url_lookup.items():
            if var and mapped_title:
                # Check if one contains the other (at least 10 chars to avoid false matches)
                if len(var) > 10 and (var in mapped_title or mapped_title in var):
                    return url
    
    return None

def inject_urls_into_merged(
    merged_path: Path,
    output_path: Path,
    url_map_path: Path,
    channel_url: str = ""
) -> None:
    """Read merged file, inject URLs under each header, write new file."""
    
    url_lookup = load_url_map(url_map_path)
    
    with open(merged_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    output_lines = []
    
    # Pattern for transcript headers: ### <a id="..."></a>Title
    header_pattern = re.compile(r'^###\s*<a\s+id="([^"]+)"></a>(.+)$')
    
    injected_count = 0
    for i, line in enumerate(lines):
        output_lines.append(line)
        
        match = header_pattern.match(line)
        if match:
            anchor = match.group(1)
            title = match.group(2).strip()
            
            url = find_url_for_title(title, url_lookup)
            
            if url:
                # Check if next line is already a URL
                if i + 1 < len(lines) and 'youtube.com' not in lines[i + 1]:
                    output_lines.append(f"\n**YouTube:** {url}\n")
                    injected_count += 1
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Injected {injected_count} YouTube URLs")
    print(f"Output: {output_path}")

def main():
    base = Path("C:/Users/aweis/Downloads/YouTube_Tools_Scripts")
    
    # Professor Jiang
    inject_urls_into_merged(
        merged_path=Path("C:/Users/aweis/Downloads/Professor_Jiang_Secret_History/MERGED_ALL_Prof_JIANG_TRANSCRIPTS.md"),
        output_path=base / "transcripts" / "Professor_Jiang" / "MERGED_ALL_Prof_JIANG_TRANSCRIPTS_WITH_URLS.md",
        url_map_path=base / "yt_processor" / "prof_jiang_url_map.json",
        channel_url="https://www.youtube.com/@PredictiveHistory"
    )

if __name__ == "__main__":
    main()
