import pathlib
import re

TRANSCRIPT_DIR = pathlib.Path(r"c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Transcripts/Huberman")
MAX_SIZE = 2.5 * 1024 * 1024  # 2.5 MB per file

def count_words(text):
    return len(text.split())

def get_video_sections(content):
    """Extract individual video sections from merged transcript."""
    sections = []
    pattern = r'^## (.*?)(?=^## |\Z)'
    matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
    
    for match in matches:
        title = match.group(1).strip()
        body = content[match.start():match.end()]
        sections.append({
            'title': title,
            'content': body,
            'size': len(body.encode('utf-8'))
        })
    
    return sections

def rechunk_file(input_file):
    """Split large transcript file into smaller chunks."""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract header
    header_match = re.match(r'^(# .*?\n\n)', content, re.DOTALL)
    header = header_match.group(1) if header_match else ""
    
    # Get video sections
    sections = get_video_sections(content)
    print(f"Found {len(sections)} video sections in {input_file.name}")
    
    # Group sections into chunks
    chunks = []
    current_chunk = [header]
    current_size = len(header.encode('utf-8'))
    
    for section in sections:
        section_size = section['size']
        
        if current_size + section_size > MAX_SIZE and current_chunk != [header]:
            chunks.append(''.join(current_chunk))
            current_chunk = [header]
            current_size = len(header.encode('utf-8'))
        
        current_chunk.append(section['content'])
        current_size += section_size
    
    if current_chunk != [header]:
        chunks.append(''.join(current_chunk))
    
    # Write chunks
    base_name = input_file.stem.replace('HUBERMAN_FULL_PART_', '')
    for i, chunk in enumerate(chunks, 1):
        output_file = TRANSCRIPT_DIR / f"HUBERMAN_FULL_{base_name}_CHUNK_{i:02d}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
        print(f"  → {output_file.name} ({size_mb:.2f} MB)")

def main():
    # Find all HUBERMAN_FULL_PART files
    full_files = sorted(TRANSCRIPT_DIR.glob("HUBERMAN_FULL_PART_*.md"))
    
    if not full_files:
        print("No HUBERMAN_FULL_PART files found")
        return
    
    print(f"Re-chunking {len(full_files)} Huberman Full files...")
    
    for file in full_files:
        rechunk_file(file)
        # Delete original after successful chunking
        file.unlink()
        print(f"Deleted {file.name}")
    
    print("\nRe-chunking complete!")

if __name__ == "__main__":
    main()
