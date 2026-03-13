#!/usr/bin/env python3
"""
Re-chunk Professor_Jiang transcript (5MB file) into NotebookLM-compliant chunks
"""

import re
from pathlib import Path

# Configuration
MAX_CHUNK_SIZE = 2.4 * 1024 * 1024  # 2.4MB
BASE_DIR = Path(r"C:\Users\aweis\Downloads\YouTube_Tools_Scripts\Transcripts")

def parse_jiang_transcript(file_path):
    """
    Parse Professor Jiang transcript file into video sections.
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
            
            # Look for URL in next few lines
            j = i + 1
            url = None
            while j < len(lines) and j < i + 5:
                next_line = lines[j].strip()
                if next_line.startswith('https://'):
                    url = next_line
                    break
                elif next_line:
                    break
                j += 1
            
            if url:
                # Save previous section
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
        
        # Add content
        if current_section:
            current_section['content'].append(lines[i])
        
        i += 1
    
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
    
    content_text = '\n'.join(section['content'])
    
    # Clean up artifacts
    content_text = re.sub(r'\[Music\]', '', content_text)
    
    lines.append(content_text)
    return '\n'.join(lines)

def create_chunks(sections, output_dir):
    """Create NotebookLM-compliant chunks."""
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_num = 1
    videos_in_chunk = []
    
    for section in sections:
        formatted = format_video_section(section)
        section_size = len(formatted.encode('utf-8'))
        
        if current_size + section_size > MAX_CHUNK_SIZE and current_chunk:
            write_chunk(chunks, chunk_num, videos_in_chunk, current_chunk, output_dir)
            print(f"  -> Chunk {chunk_num} written ({current_size/1024/1024:.2f} MB, {len(videos_in_chunk)} videos)")
            
            chunk_num += 1
            current_chunk = []
            current_size = 0
            videos_in_chunk = []
        
        current_chunk.append(formatted)
        current_size += section_size
        videos_in_chunk.append(section['title'])
    
    if current_chunk:
        write_chunk(chunks, chunk_num, videos_in_chunk, current_chunk, output_dir)
        print(f"  -> Chunk {chunk_num} written ({current_size/1024/1024:.2f} MB, {len(videos_in_chunk)} videos)")
    
    return chunks

def write_chunk(chunks, chunk_num, videos, content_list, output_dir):
    """Write a chunk to disk."""
    header_lines = [
        f"# PROFESSOR JIANG - Part {chunk_num:02d}\n",
        f"## Table of Contents\n\n"
    ]
    
    for i, title in enumerate(videos, 1):
        header_lines.append(f"{i}. {title}\n")
    
    header_lines.append("\n" + "=" * 80 + "\n\n")
    header = ''.join(header_lines)
    
    full_content = header + "\n\n---\n\n".join(content_list)
    
    output_file = output_dir / f"PROFESSOR_JIANG_PART_{chunk_num:02d}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    chunks.append(output_file)

def main():
    print("=" * 80)
    print("RE-CHUNKING PROFESSOR JIANG TRANSCRIPT")
    print("=" * 80)
    
    input_file = BASE_DIR / "Professor_Jiang" / "MERGED_ALL_Prof_JIANG_TRANSCRIPTS.md"
    output_dir = BASE_DIR / "Professor_Jiang"
    
    if not input_file.exists():
        print(f"✗ File not found: {input_file}")
        return
    
    print(f"\nInput file: {input_file.name}")
    print(f"File size: {input_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Parse sections
    sections = parse_jiang_transcript(input_file)
    print(f"Found {len(sections)} video sections")
    
    # Create chunks
    chunks = create_chunks(sections, output_dir)
    
    print(f"\n✓ Created {len(chunks)} chunk(s)")
    print(f"Output directory: {output_dir}")
    
    # Verify sizes
    print("\nChunk sizes:")
    for chunk in chunks:
        size_mb = chunk.stat().st_size / 1024 / 1024
        status = "✅" if size_mb < 2.5 else "❌"
        print(f"  {status} {chunk.name}: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
