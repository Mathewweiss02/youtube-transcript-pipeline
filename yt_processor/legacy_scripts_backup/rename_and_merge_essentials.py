#!/usr/bin/env python3
"""
Rename Essentials Transcripts to Titles and Re-merge
"""

import json
import re
from pathlib import Path

# Config
PLAYLIST_FILE = Path('../Howdy/huberman_essentials_playlist.json')
TRANSCRIPT_DIR = Path('../Howdy/Essentials_Transcripts')
MERGED_DIR = Path('../Howdy')
WORD_LIMIT = 400000

def sanitize_filename(title):
    # Keep alphanumeric, spaces, hyphens, underscores
    clean = re.sub(r'[^\w\s-]', '', title)
    # Replace spaces with underscores
    clean = re.sub(r'\s+', '_', clean)
    return clean.strip()

def count_words(text):
    return len(text.split())

def main():
    print("=" * 80)
    print("RENAMING AND MERGING TRANSCRIPTS")
    print("=" * 80)
    
    # Load playlist for mapping
    with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
        
    print(f"Loaded {len(videos)} videos from playlist")
    
    # 1. Rename files
    print("\nRenaming files...")
    renamed_files = []
    
    for video in videos:
        vid_id = video['video_id']
        title = video['title']
        sanitized_title = sanitize_filename(title)
        
        # Check for existing ID-based file
        id_path = TRANSCRIPT_DIR / f"{vid_id}.md"
        title_path = TRANSCRIPT_DIR / f"{sanitized_title}.md"
        
        if id_path.exists():
            print(f"  Renaming: {vid_id} -> {sanitized_title}")
            id_path.rename(title_path)
            renamed_files.append((title, title_path))
        elif title_path.exists():
            # Already renamed
            renamed_files.append((title, title_path))
        else:
            print(f"  Warning: No transcript found for {vid_id}")

    print(f"\nProcessed {len(renamed_files)} files")

    # 2. Merge with word count limit
    print("\nMerging files (Limit: 400k words)...")
    
    current_part = 1
    current_word_count = 0
    current_files = []
    
    def write_merged_file(part_num, files):
        output_path = MERGED_DIR / f"HUBERMAN_ESSENTIALS_CONSOLIDATED_PART_{part_num:02d}.md"
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(f"# Andrew Huberman Essentials - Part {part_num}\n\n")
            f_out.write("## Table of Contents\n\n")
            for i, (t, p) in enumerate(files, 1):
                f_out.write(f"- {i}. {t}\n")
            f_out.write("\n---\n\n")
            
            for t, p in files:
                f_out.write(f"# {t}\n\n")
                with open(p, 'r', encoding='utf-8') as f_in:
                    f_out.write(f_in.read())
                f_out.write("\n\n---\n\n")
        print(f"  Created Part {part_num}: {output_path.name}")

    for title, path in renamed_files:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            words = count_words(content)
            
        if current_word_count + words > WORD_LIMIT:
            write_merged_file(current_part, current_files)
            current_part += 1
            current_word_count = 0
            current_files = []
            
        current_files.append((title, path))
        current_word_count += words
        
    if current_files:
        write_merged_file(current_part, current_files)

    # Cleanup old consolidated file if exists
    old_merged = MERGED_DIR / 'HUBERMAN_ESSENTIALS_CONSOLIDATED.md'
    if old_merged.exists():
        print(f"\nRemoving old merged file: {old_merged.name}")
        old_merged.unlink()

    print("\nDone!")

if __name__ == "__main__":
    main()
