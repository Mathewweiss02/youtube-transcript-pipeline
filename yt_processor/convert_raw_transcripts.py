#!/usr/bin/env python3
"""
Convert raw transcript .txt files to properly formatted Markdown
and chunk them for NotebookLM compliance (<2.5MB per file)
"""

import re
from pathlib import Path

# Configuration
MAX_CHUNK_SIZE = 2.4 * 1024 * 1024  # 2.4MB
BASE_DIR = Path(r"C:\Users\aweis\Downloads\YouTube_Tools_Scripts\Transcripts")

def parse_transcript_file(file_path):
    """
    Parse a raw transcript file into video sections.
    Expected format:
    # Video Title
    
    https://youtube.com/watch?v=xxx
    
    [transcript content]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by video sections (lines starting with # followed by URL)
    sections = []
    current_section = None
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is a title line (starts with #)
        if line.startswith('#') and not line.startswith('##'):
            title = line.lstrip('#').strip()
            
            # Look for URL in next few lines (skip blank lines)
            j = i + 1
            url = None
            while j < len(lines) and j < i + 5:
                next_line = lines[j].strip()
                if next_line.startswith('https://'):
                    url = next_line
                    break
                elif next_line:  # Non-blank line that's not a URL
                    break
                j += 1
            
            if url:
                # Save previous section if exists
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': title,
                    'url': url,
                    'content': []
                }
                i = j + 1
                continue
        
        # Add content to current section
        if current_section:
            current_section['content'].append(lines[i])
        
        i += 1
    
    # Don't forget the last section
    if current_section:
        sections.append(current_section)
    
    return sections

def format_video_section(section):
    """Format a video section as Markdown."""
    lines = [
        f"# {section['title']}\n",
        f"URL: {section['url']}\n",
        "---\n\n"
    ]
    
    # Add transcript content
    content_text = '\n'.join(section['content'])
    
    # Clean up [Music] tags and other artifacts
    content_text = re.sub(r'\[Music\]', '', content_text)
    
    lines.append(content_text)
    return '\n'.join(lines)

def create_chunks(sections, output_dir, base_name):
    """Create NotebookLM-compliant chunks from video sections."""
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_num = 1
    videos_in_chunk = []
    
    for section in sections:
        # Format this section
        formatted = format_video_section(section)
        section_size = len(formatted.encode('utf-8'))
        
        # Check if adding this would exceed chunk size
        if current_size + section_size > MAX_CHUNK_SIZE and current_chunk:
            # Write current chunk
            write_chunk(chunks, chunk_num, videos_in_chunk, current_chunk, output_dir, base_name)
            print(f"  -> Chunk {chunk_num} written ({current_size/1024/1024:.2f} MB, {len(videos_in_chunk)} videos)")
            
            # Reset
            chunk_num += 1
            current_chunk = []
            current_size = 0
            videos_in_chunk = []
        
        # Add to current chunk
        current_chunk.append(formatted)
        current_size += section_size
        videos_in_chunk.append(section['title'])
    
    # Write final chunk
    if current_chunk:
        write_chunk(chunks, chunk_num, videos_in_chunk, current_chunk, output_dir, base_name)
        print(f"  -> Chunk {chunk_num} written ({current_size/1024/1024:.2f} MB, {len(videos_in_chunk)} videos)")
    
    return chunks

def write_chunk(chunks, chunk_num, videos, content_list, output_dir, base_name):
    """Write a chunk to disk."""
    # Create header
    header_lines = [
        f"# {base_name} - Part {chunk_num:02d}\n",
        f"## Table of Contents\n\n"
    ]
    
    for i, title in enumerate(videos, 1):
        header_lines.append(f"{i}. {title}\n")
    
    header_lines.append("\n" + "=" * 80 + "\n\n")
    header = ''.join(header_lines)
    
    # Combine header + content
    full_content = header + "\n\n---\n\n".join(content_list)
    
    # Write file
    output_file = output_dir / f"{base_name}_PART_{chunk_num:02d}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    chunks.append(output_file)

def process_channel(channel_name, input_file):
    """Process a single channel's transcript file."""
    print(f"\n{'=' * 80}")
    print(f"Processing: {channel_name}")
    print(f"{'=' * 80}")
    
    input_path = BASE_DIR / channel_name / input_file
    output_dir = BASE_DIR / channel_name
    
    if not input_path.exists():
        print(f"✗ File not found: {input_path}")
        return []
    
    # Parse sections
    sections = parse_transcript_file(input_path)
    print(f"Found {len(sections)} video sections")
    
    # Create chunks
    base_name = channel_name.upper().replace('_', ' ')
    chunks = create_chunks(sections, output_dir, base_name)
    
    print(f"\n✓ Created {len(chunks)} chunk(s)")
    return chunks

def main():
    print("=" * 80)
    print("TRANSCRIPT CONVERTER & CHUNKER")
    print("=" * 80)
    
    # Define channels to process
    channels = [
        ("Coach_Micah_B", "coachmicahb_part1.txt"),
        ("Combat_Athlete_Physio", "combatathletephysio_part1.txt"),
        ("Daru_Strong", None),  # Multiple files
        ("Warrior_Collective", None),  # Multiple files
    ]
    
    # Process single-file channels
    for channel_name, input_file in channels[:2]:
        if input_file:
            process_channel(channel_name, input_file)
    
    # Process multi-file channels
    print(f"\n{'=' * 80}")
    print("Processing: Daru_Strong (multiple files)")
    print(f"{'=' * 80}")
    
    daru_dir = BASE_DIR / "Daru_Strong"
    daru_files = sorted(daru_dir.glob("daru_part*.txt"))
    print(f"Found {len(daru_files)} files")
    
    all_sections = []
    for daru_file in daru_files:
        print(f"  Reading {daru_file.name}...")
        sections = parse_transcript_file(daru_file)
        all_sections.extend(sections)
    
    print(f"Total sections: {len(all_sections)}")
    output_dir = BASE_DIR / "Daru_Strong"
    chunks = create_chunks(all_sections, output_dir, "DARU STRONG")
    print(f"\n✓ Created {len(chunks)} chunk(s)")
    
    # Process Warrior_Collective
    print(f"\n{'=' * 80}")
    print("Processing: Warrior_Collective (multiple files)")
    print(f"{'=' * 80}")
    
    warrior_dir = BASE_DIR / "Warrior_Collective"
    warrior_files = sorted(warrior_dir.glob("warriorcollective_part*.txt"))
    print(f"Found {len(warrior_files)} files")
    
    all_sections = []
    for warrior_file in warrior_files:
        print(f"  Reading {warrior_file.name}...")
        sections = parse_transcript_file(warrior_file)
        all_sections.extend(sections)
    
    print(f"Total sections: {len(all_sections)}")
    output_dir = BASE_DIR / "Warrior_Collective"
    chunks = create_chunks(all_sections, output_dir, "WARRIOR COLLECTIVE")
    print(f"\n✓ Created {len(chunks)} chunk(s)")
    
    print("\n" + "=" * 80)
    print("ALL CONVERSIONS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
