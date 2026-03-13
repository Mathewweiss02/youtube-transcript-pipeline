#!/usr/bin/env python3
"""
Chunk Mark Bell transcripts for NotebookLM compliance (<2.5MB per file)
"""

import re
from pathlib import Path

# Configuration
MAX_CHUNK_SIZE = 2.4 * 1024 * 1024  # 2.4MB
BASE_DIR = Path(r"C:\Users\aweis\Downloads\YouTube_Tools_Scripts\Transcripts")

def parse_mark_bell_transcripts(input_dir):
    """
    Parse Mark Bell transcript files into video sections.
    """
    sections = []
    
    # Get all .md files
    md_files = sorted(input_dir.glob("*.md"))
    
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title and URL from the file
        lines = content.split('\n')
        title = None
        url = None
        transcript_content = []
        
        for i, line in enumerate(lines):
            if line.startswith('# ') and title is None:
                title = line.lstrip('#').strip()
            elif line.startswith('URL: ') and url is None:
                url = line.replace('URL: ', '').strip()
            elif line.strip() == '---':
                # Everything after --- is the transcript
                transcript_content = lines[i+1:]
                break
        
        if title and url:
            sections.append({
                'title': title,
                'url': url,
                'content': '\n'.join(transcript_content)
            })
    
    return sections

def format_video_section(section):
    """Format a video section as Markdown."""
    lines = [
        f"# {section['title']}\n",
        f"URL: {section['url']}\n",
        "---\n\n"
    ]
    
    content_text = section['content']
    
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
        f"# MARK BELL POWER PROJECT - Part {chunk_num:02d}\n",
        f"## Table of Contents\n\n"
    ]
    
    for i, title in enumerate(videos, 1):
        header_lines.append(f"{i}. {title}\n")
    
    header_lines.append("\n" + "=" * 80 + "\n\n")
    header = ''.join(header_lines)
    
    full_content = header + "\n\n---\n\n".join(content_list)
    
    output_file = output_dir / f"MARK_BELL_PART_{chunk_num:02d}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    chunks.append(output_file)

def main():
    print("=" * 80)
    print("CHUNKING MARK BELL TRANSCRIPTS")
    print("=" * 80)
    
    input_dir = BASE_DIR / "Mark_Bell_Raw"
    output_dir = BASE_DIR / "Mark_Bell"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        print(f"✗ Input directory not found: {input_dir}")
        return
    
    # Parse sections
    sections = parse_mark_bell_transcripts(input_dir)
    print(f"\nFound {len(sections)} video sections")
    
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
