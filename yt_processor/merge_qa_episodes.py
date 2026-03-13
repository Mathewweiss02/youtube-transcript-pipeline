#!/usr/bin/env python3
"""
Merge Hyperarch Fascia Q&A episodes into consolidated files.
Follows YouTube pipeline rules: ≤2.5MB per file, natural episode boundaries.
"""

import os
import glob
import re

SOURCE_DIR = r"c:\Users\aweis\Downloads\YouTube_Tools_Scripts\transcripts\Hyperarch_Fascia_QA_Sources"
MAX_SIZE_BYTES = 2.5 * 1024 * 1024  # 2.5 MB limit

def extract_episode_number(filename):
    """Extract episode number from filename like QA_EP_45_*.md"""
    match = re.search(r'QA_EP_(\d+)_', filename)
    return int(match.group(1)) if match else 999

def get_all_episode_files():
    """Get all QA episode files sorted by episode number"""
    pattern = os.path.join(SOURCE_DIR, "QA_EP_*.md")
    files = glob.glob(pattern)
    return sorted(files, key=lambda x: extract_episode_number(os.path.basename(x)))

def read_episode_content(filepath):
    """Read episode content, removing the top-level header for merging"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract episode number and title from first line
    lines = content.split('\n')
    first_line = lines[0] if lines else ""
    
    # Keep the header but format it as a section header
    # Remove the # and keep as ## for section
    if first_line.startswith('# '):
        header = '## ' + first_line[2:]
    else:
        header = first_line
    
    # Reconstruct with modified header
    new_content = header + '\n' + '\n'.join(lines[1:])
    return new_content

def merge_episodes():
    """Merge all episodes into consolidated files"""
    episode_files = get_all_episode_files()
    
    if not episode_files:
        print("No episode files found!")
        return
    
    print(f"Found {len(episode_files)} episode files")
    
    # Calculate total size
    total_size = sum(os.path.getsize(f) for f in episode_files)
    print(f"Total size: {total_size / 1024:.1f} KB")
    
    # Since total is ~500KB, we can fit all in one file
    # But let's split into 2 parts for better navigation (~250KB each)
    mid_point = len(episode_files) // 2
    
    batches = [
        ("PART_01", episode_files[:mid_point]),
        ("PART_02", episode_files[mid_point:])
    ]
    
    for part_name, batch_files in batches:
        if not batch_files:
            continue
            
        output_file = os.path.join(SOURCE_DIR, f"HYPERARCH_QA_MERGED_{part_name}.md")
        
        # Build merged content
        merged_lines = []
        
        # Add master header
        episode_range = f"Episodes {extract_episode_number(os.path.basename(batch_files[0]))}-{extract_episode_number(os.path.basename(batch_files[-1]))}"
        merged_lines.append(f"# Hyperarch Fascia Q&A {episode_range}")
        merged_lines.append("")
        merged_lines.append(f"**Source:** NotebookLM - Hyperarch Fascia Q&A: Big Toe, Music, and Training")
        merged_lines.append(f"**URL:** https://notebooklm.google.com/notebook/4963d1f4-6003-4172-9772-1b4e1542b7fd")
        merged_lines.append("")
        merged_lines.append("---")
        merged_lines.append("")
        
        # Table of Contents
        merged_lines.append("## Table of Contents")
        merged_lines.append("")
        for i, filepath in enumerate(batch_files, 1):
            basename = os.path.basename(filepath)
            ep_num = extract_episode_number(basename)
            # Get title from file
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                title = first_line.replace('# QA Ep ', '').replace('# QA EP ', '') if first_line.startswith('#') else basename
            merged_lines.append(f"{i}. [Episode {ep_num}](#episode-{ep_num})")
        merged_lines.append("")
        merged_lines.append("---")
        merged_lines.append("")
        
        # Add each episode
        for filepath in batch_files:
            basename = os.path.basename(filepath)
            ep_num = extract_episode_number(basename)
            
            # Add episode anchor
            merged_lines.append(f"<a name='episode-{ep_num}'></a>")
            merged_lines.append("")
            
            # Read and add episode content
            content = read_episode_content(filepath)
            merged_lines.append(content)
            
            # Add separator between episodes
            merged_lines.append("")
            merged_lines.append("---")
            merged_lines.append("")
        
        # Write merged file
        merged_content = '\n'.join(merged_lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        
        file_size = os.path.getsize(output_file)
        print(f"✓ Created {part_name}: {os.path.basename(output_file)} ({file_size / 1024:.1f} KB)")
        
        if file_size > MAX_SIZE_BYTES:
            print(f"  ⚠️ WARNING: File exceeds 2.5MB limit!")
    
    print(f"\n✅ Merging complete!")

if __name__ == "__main__":
    merge_episodes()
