#!/usr/bin/env python3
"""
Jay Campbell Chunker
Merges 265 redownloaded transcripts into NotebookLM-compliant consolidated parts.
"""

import re
from pathlib import Path

INPUT_DIR = Path("../../transcripts/Jay_Campbell_Redownload")
OUTPUT_DIR = Path("../../transcripts/Jay_Campbell")
BASE_NAME = "Jay_Campbell"
MAX_CHUNK_SIZE = 2.4 * 1024 * 1024

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("🎙️ JAY CAMPBELL CHUNKER")
print("=" * 70)
print(f"Input: {INPUT_DIR}")
print(f"Output: {OUTPUT_DIR}")
print(f"Max chunk: {MAX_CHUNK_SIZE/1024/1024:.2f} MB")
print()

def parse_transcripts():
    """Parse individual transcript files."""
    sections = []
    md_files = sorted(INPUT_DIR.glob("*.md"))
    
    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        title = None
        url = None
        video_id = None
        transcript_lines = []
        in_transcript = False
        
        for line in lines:
            if line.startswith('# ') and title is None:
                title = line.lstrip('#').strip()
            elif line.startswith('URL: ') and url is None:
                url = line.replace('URL: ', '').strip()
            elif line.startswith('Video ID: ') and video_id is None:
                video_id = line.replace('Video ID: ', '').strip()
            elif line.strip() == '---':
                in_transcript = True
                continue
            elif in_transcript:
                transcript_lines.append(line)
        
        if title and url:
            sections.append({
                'title': title,
                'url': url,
                'video_id': video_id or '',
                'content': '\n'.join(transcript_lines).strip()
            })
    
    return sections

def format_section(section):
    """Format a video section."""
    lines = [f"# {section['title']}\n"]
    lines.append(f"URL: {section['url']}\n")
    if section['video_id']:
        lines.append(f"Video ID: {section['video_id']}\n")
    lines.append("---\n\n")
    
    content = section['content']
    content = re.sub(r'\[Music\]', '', content)
    content = re.sub(r'\s+', ' ', content)
    lines.append(content)
    lines.append("\n\n")
    
    return ''.join(lines)

def create_chunks(sections):
    """Create NotebookLM-compliant chunks."""
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_num = 1
    videos_in_chunk = []
    
    for section in sections:
        formatted = format_section(section)
        formatted_size = len(formatted.encode('utf-8'))
        
        if current_size + formatted_size > MAX_CHUNK_SIZE and current_chunk:
            # Write current chunk
            chunk_content = ''.join(current_chunk)
            toc = "## Table of Contents\n" + ''.join([f"- {v}\n" for v in videos_in_chunk]) + "\n---\n\n"
            
            chunk_path = OUTPUT_DIR / f"{BASE_NAME}_CONSOLIDATED_PART_{chunk_num:02d}.md"
            chunk_path.write_text(toc + chunk_content, encoding='utf-8')
            
            size_mb = len((toc + chunk_content).encode('utf-8')) / 1024 / 1024
            print(f"  -> Part {chunk_num}: {size_mb:.2f} MB, {len(videos_in_chunk)} videos")
            
            chunks.append(chunk_path)
            current_chunk = []
            current_size = 0
            videos_in_chunk = []
            chunk_num += 1
        
        current_chunk.append(formatted)
        current_size += formatted_size
        videos_in_chunk.append(section['title'])
    
    # Write final chunk
    if current_chunk:
        chunk_content = ''.join(current_chunk)
        toc = "## Table of Contents\n" + ''.join([f"- {v}\n" for v in videos_in_chunk]) + "\n---\n\n"
        
        chunk_path = OUTPUT_DIR / f"{BASE_NAME}_CONSOLIDATED_PART_{chunk_num:02d}.md"
        chunk_path.write_text(toc + chunk_content, encoding='utf-8')
        
        size_mb = len((toc + chunk_content).encode('utf-8')) / 1024 / 1024
        print(f"  -> Part {chunk_num}: {size_mb:.2f} MB, {len(videos_in_chunk)} videos")
        chunks.append(chunk_path)
    
    return chunks

# Run
sections = parse_transcripts()
print(f"Found {len(sections)} video transcripts")

if sections:
    chunks = create_chunks(sections)
    
    print("\n" + "=" * 70)
    print("✅ CHUNKING COMPLETE!")
    print("=" * 70)
    print(f"Created {len(chunks)} consolidated part(s):")
    for chunk in chunks:
        size = chunk.stat().st_size / 1024 / 1024
        print(f"  - {chunk.name}: {size:.2f} MB")
    print("\n💡 Next: Delete old Jay_Campbell/ folder and update sidecar")
else:
    print("❌ No transcripts found!")
