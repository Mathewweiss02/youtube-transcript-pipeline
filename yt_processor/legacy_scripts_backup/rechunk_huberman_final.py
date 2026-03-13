import pathlib
import re

TRANSCRIPT_DIR = pathlib.Path(r"c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Transcripts/Huberman")
MAX_SIZE = 2.5 * 1024 * 1024  # 2.5 MB per file

def reconstruct_original(group_num):
    """Reconstruct original file from all chunks."""
    chunks = sorted(TRANSCRIPT_DIR.glob(f"HUBERMAN_FULL_0{group_num}_CHUNK_*.md"))
    
    if not chunks:
        return None
    
    print(f"Reconstructing group 0{group_num} from {len(chunks)} chunks...")
    combined = ""
    
    for chunk in chunks:
        with open(chunk, 'r', encoding='utf-8') as f:
            combined += f.read()
    
    return combined

def split_into_videos(content):
    """Split content by video markers."""
    pattern = r'(^={80}\n\nVideo \d+:.*?)(?=^={80}|\Z)'
    matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
    
    videos = []
    for match in matches:
        video_content = match.group(1)
        videos.append(video_content)
    
    return videos

def rechunk_group(group_num, content):
    """Split content into chunks by video."""
    # Extract header
    header_match = re.match(r'^(.*?)(^={80}\n\nVideo \d+:)', content, re.MULTILINE | re.DOTALL)
    header = header_match.group(1) if header_match else ""
    
    # Get individual videos
    videos = split_into_videos(content)
    print(f"  Found {len(videos)} videos")
    
    if not videos:
        return []
    
    # Group videos into chunks
    chunks = []
    current_chunk = header
    current_size = len(header.encode('utf-8'))
    
    for video in videos:
        video_size = len(video.encode('utf-8'))
        
        if current_size + video_size > MAX_SIZE and current_chunk != header:
            chunks.append(current_chunk)
            current_chunk = header
            current_size = len(header.encode('utf-8'))
        
        current_chunk += video
        current_size += video_size
    
    if current_chunk != header:
        chunks.append(current_chunk)
    
    # Write chunks
    created_files = []
    for i, chunk in enumerate(chunks, 1):
        output_file = TRANSCRIPT_DIR / f"HUBERMAN_FULL_0{group_num}_CHUNK_{i:02d}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
        print(f"    → {output_file.name} ({size_mb:.2f} MB)")
        created_files.append(output_file)
    
    return created_files

def main():
    print("Re-chunking Huberman Full files...\n")
    
    all_created = []
    
    # Process each group
    for i in range(1, 7):
        # Reconstruct original
        content = reconstruct_original(i)
        
        if content is None:
            print(f"Group 0{i}: No chunks found\n")
            continue
        
        # Re-chunk
        created = rechunk_group(i, content)
        all_created.extend(created)
        
        # Delete old chunks
        old_chunks = TRANSCRIPT_DIR.glob(f"HUBERMAN_FULL_0{i}_CHUNK_*.md")
        for chunk in old_chunks:
            if chunk not in created:
                chunk.unlink()
        
        print()
    
    print(f"Complete! Created {len(all_created)} chunk files")

if __name__ == "__main__":
    main()
