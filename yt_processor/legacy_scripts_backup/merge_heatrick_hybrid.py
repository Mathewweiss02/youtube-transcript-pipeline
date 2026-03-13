#!/usr/bin/env python3
"""
Merge @heatrick transcripts using hybrid approach for NotebookLM.
Creates ~9 combined source files under 450k words each.
"""

import os
from pathlib import Path
from datetime import datetime

TRANSCRIPTS_ROOT = Path(r'C:\Users\aweis\Downloads\anything youtube\transcripts\heatrick')
OUTPUT_DIR = Path(r'C:\Users\aweis\Downloads\anything youtube\transcripts\heatrick_merged')
OUTPUT_DIR.mkdir(exist_ok=True)

# Hybrid grouping configuration
# Format: (output_filename, [list of folder names to merge])
MERGE_CONFIG = [
    # Big playlists - keep separate
    ("01_Podcast.txt", ["Podcast"]),
    ("02_Muay_Thai_SC_Info.txt", ["Muay Thai Strength and Conditioning Info"]),
    ("03_MuayThai_Tube_Interviews.txt", ["MuayThai Tube Interviews"]),
    ("04_Science_of_Building_Champions.txt", ["The Science of Building Champions Podcast"]),
    
    # Merged groups
    ("05_Coachs_Quick_Content.txt", [
        "Coach_s Quick Chat Episodes",
        "Coachs Quick Chat Episodes",  # duplicate folder from extras
        "MT_S_C Q_A Episodes",
        "Train Smarter_ Not Softer_",
    ]),
    ("06_SC_Exercises_Biomechanics.txt", [
        "Muay Thai Strength and Conditioning Exercises _ Routines",
        "Muay Thai Strength and Conditioning Exercises",  # extras folder
        "Muay Thai Biomechanics",
        "Whiteboard Coaching Session Episodes",
    ]),
    ("07_Featuring_Don_Heatrick.txt", [
        "Featuring Don Heatrick",
        "Fight Analysis",
    ]),
    ("08_Fighter_Development.txt", [
        "Muay Thai Fight IQ",
        "Age Defying Muay Thai Fighter Series",
        "Injury Prehab_Rehab",
        "The Fighter_s Progression System",
        "Muay Thai Performance Hack Episodes",
    ]),
    ("09_Misc_Interviews_Clips.txt", [
        "Daniel McGowan Interview Yokkao 28",
        "Richard Smith Interview _ Yokkao 23 _ 24",
        "SoBC Podcast Clips",
        "Food _ Nutrition",
    ]),
]


def count_words(text):
    return len(text.split())


def merge_folder(folder_path):
    """Read all .md files from a folder and return combined content with TOC."""
    files = sorted(folder_path.glob("*.md"))
    if not files:
        return "", 0, []
    
    entries = []
    for f in files:
        content = f.read_text(encoding='utf-8', errors='ignore')
        title = f.stem
        # Extract title from first line if it's a header
        lines = content.strip().split('\n')
        if lines and lines[0].startswith('# '):
            title = lines[0][2:].strip()
        entries.append((title, content, f.name))
    
    return entries


def create_merged_file(output_name, folder_names):
    """Create a merged file from multiple folders."""
    all_entries = []
    source_folders = []
    
    for folder_name in folder_names:
        folder_path = TRANSCRIPTS_ROOT / folder_name
        if folder_path.exists():
            entries = merge_folder(folder_path)
            if entries:
                all_entries.extend([(folder_name, *e) for e in entries])
                source_folders.append(folder_name)
    
    if not all_entries:
        return 0, 0
    
    # Build the merged file
    output_path = OUTPUT_DIR / output_name
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        title = output_name.replace('.txt', '').replace('_', ' ')
        title = title.split(' ', 1)[1] if title[0].isdigit() else title  # Remove number prefix
        f.write(f"# {title}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Source folders: {', '.join(source_folders)}\n")
        f.write(f"Total transcripts: {len(all_entries)}\n\n")
        
        # Table of Contents
        f.write("## Table of Contents\n\n")
        for i, (folder, title, content, filename) in enumerate(all_entries, 1):
            # Create anchor-safe ID
            anchor = title.lower().replace(' ', '-').replace("'", '').replace('"', '')
            anchor = ''.join(c for c in anchor if c.isalnum() or c == '-')[:50]
            f.write(f"{i}. [{title[:80]}](#{anchor})\n")
        f.write("\n---\n\n")
        
        # Content
        for folder, title, content, filename in all_entries:
            f.write(f"## {title}\n\n")
            f.write(f"*Source: {folder}*\n\n")
            # Skip the title line if content starts with it
            lines = content.strip().split('\n')
            if lines and lines[0].startswith('# '):
                content = '\n'.join(lines[1:]).strip()
            f.write(content)
            f.write("\n\n---\n\n")
    
    # Calculate stats
    final_content = output_path.read_text(encoding='utf-8')
    word_count = count_words(final_content)
    file_size = output_path.stat().st_size
    
    return word_count, file_size, len(all_entries)


def main():
    print("Merging @heatrick transcripts (Hybrid approach)")
    print(f"Output: {OUTPUT_DIR}\n")
    print("=" * 70)
    
    total_words = 0
    total_files = 0
    results = []
    
    for output_name, folder_names in MERGE_CONFIG:
        words, size, count = create_merged_file(output_name, folder_names)
        if words > 0:
            status = "⚠️ OVER LIMIT" if words > 450000 else "✓"
            results.append((output_name, count, words, size, status))
            total_words += words
            total_files += count
            print(f"{status} {output_name}")
            print(f"   {count} transcripts, {words:,} words, {size//1024} KB")
    
    print("\n" + "=" * 70)
    print(f"\nSUMMARY:")
    print(f"  Created {len(results)} merged files")
    print(f"  Total transcripts: {total_files}")
    print(f"  Total words: {total_words:,}")
    print(f"  Output folder: {OUTPUT_DIR}")
    
    # Check for any files over limit
    over_limit = [r for r in results if r[4] == "⚠️ OVER LIMIT"]
    if over_limit:
        print(f"\n⚠️ WARNING: {len(over_limit)} file(s) exceed 450k word limit!")
        for name, count, words, size, status in over_limit:
            print(f"   - {name}: {words:,} words")


if __name__ == "__main__":
    main()
