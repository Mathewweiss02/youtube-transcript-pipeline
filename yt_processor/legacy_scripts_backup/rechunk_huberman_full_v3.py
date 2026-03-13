import pathlib
import re

TRANSCRIPT_DIR = pathlib.Path(r"c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Transcripts/Huberman")
MAX_SIZE = 2.5 * 1024 * 1024  # 2.5 MB per file

def split_into_videos(content):
    """Split content by video markers."""
    pattern = r'(^={80}\n\nVideo \d+:.*?)(?=^={80}|\Z)'
    matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
    
    videos = []
    for match in matches:
        video_content = match.group(1)
        videos.append(video_content)
    
    return videos

def rechunk_file(input_file):
    """Split large transcript file into smaller chunks by video."""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract header (everything before first video)
    header_match = re.match(r'^(.*?)(^={80}\n\nVideo \d+:)', content, re.MULTILINE | re.DOTALL)
    header = header_match.group(1) if header_match else ""
    
    # Get individual videos
    videos = split_into_videos(content)
    print(f"Found {len(videos)} videos in {input_file.name}")
    
    if not videos:
        print(f"  No videos found, skipping")
        return
    
    # Group videos into chunks
    chunks = []
    current_chunk = header
    current_size = len(header.encode('utf-8'))
    
    for i, video in enumerate(videos):
        video_size = len(video.encode('utf-8'))
        
        if current_size + video_size > MAX_SIZE and current_chunk != header:
            chunks.append(current_chunk)
            current_chunk = header
            current_size = len(header.encode('utf-8'))
        
        current_chunk += video
        current_size += video_size
    
    if current_chunk != header:
        chunks.append(current_chunk)
    
    # Write chunks with unique names
    base_name = input_file.stem.replace('HUBERMAN_FULL_', '').replace('_CHUNK_01', '')
    created_files = []
    for i, chunk in enumerate(chunks, 1):
        output_file = TRANSCRIPT_DIR / f"HUBERMAN_FULL_{base_name}_CHUNK_{i:02d}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
        print(f"  → {output_file.name} ({size_mb:.2f} MB)")
        created_files.append(output_file)
    
    return created_files

def main():
    # Find all HUBERMAN_FULL files
    full_files = sorted(TRANSCRIPT_DIR.glob("HUBERMAN_FULL_*_CHUNK_*.md"))
    
    if not full_files:
        print("No HUBERMAN_FULL files found")
        return
    
    print(f"Re-chunking {len(full_files)} Huberman Full files...")
    
    # First, collect all existing files to delete later
    files_to_delete = set(full_files)
    
    # Also check for any missing CHUNK_01 files
    for i in range(1, 7):
        chunk_01 = TRANSCRIPT_DIR / f"HUBERMAN_FULL_0{i}_CHUNK_01.md"
        if not chunk_01.exists():
            # Find other chunks from this group to reconstruct
            other_chunks = sorted(TRANSCRIPT_DIR.glob(f"HUBERMAN_FULL_0{i}_CHUNK_*.md"))
            if other_chunks:
                print(f"Missing CHUNK_01 for group 0{i}, reconstructing from {len(other_chunks)} chunks...")
                # Combine all chunks to recreate original
                combined = ""
                for chunk in other_chunks:
                    with open(chunk, 'r', encoding='utf-8') as f:
                        combined += f.read()
                # Write as temporary file for re-chunking
                temp_file = TRANSCRIPT_DIR / f"HUBERMAN_FULL_0{i}_TEMP.md"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(combined)
                files_to_delete.add(temp_file)
                full_files.append(temp_file)
    
    # Now re-chunk all files
    all_created = []
    for file in sorted(full_files):
        if file.exists():
            created = rechunk_file(file)
            all_created.extend(created)
    
    # Delete old files after successful chunking
    for file in files_to_delete:
        if file.exists():
            file.unlink()
            print(f"Deleted {file.name}")
    
    print(f"\nComplete! Created {len(all_created)} chunk files")

if __name__ == "__main__":
    main()
