import pathlib
import re

TRANSCRIPT_DIR = pathlib.Path(r"c:/Users/aweis/Downloads/YouTube_Tools_Scripts/Transcripts/Huberman")
MAX_SIZE = 2.5 * 1024 * 1024  # 2.5 MB per file

VIDEO_PATTERN = re.compile(r'^=+\n+\s*Video \d+:.*?(?=^=+\n+\s*Video \d+:|\Z)', re.MULTILINE | re.DOTALL)

def split_into_videos(content):
    """Split content by the `=====` separator followed by `Video N:` lines."""
    return VIDEO_PATTERN.findall(content)

def rechunk_file(input_file):
    """Split large transcript file into smaller chunks by video."""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract header (everything before first video block)
    first_video_match = VIDEO_PATTERN.search(content)
    header = content[:first_video_match.start()] if first_video_match else ""
    
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
        
        # If adding this video exceeds limit and we have content, start new chunk
        if current_size + video_size > MAX_SIZE and current_chunk != header:
            chunks.append(current_chunk)
            current_chunk = header
            current_size = len(header.encode('utf-8'))
        
        current_chunk += video
        current_size += video_size
    
    # Add final chunk
    if current_chunk != header:
        chunks.append(current_chunk)
    
    # Write chunks
    base_name = input_file.stem.replace('HUBERMAN_FULL_', '').replace('_CHUNK_01', '')
    for i, chunk in enumerate(chunks, 1):
        output_file = TRANSCRIPT_DIR / f"HUBERMAN_FULL_{base_name}_CHUNK_{i:02d}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
        print(f"  → {output_file.name} ({size_mb:.2f} MB)")

def main():
    # Find all HUBERMAN_FULL files (both old PART and new CHUNK format)
    full_files = sorted(TRANSCRIPT_DIR.glob("HUBERMAN_FULL_*_CHUNK_01.md"))
    
    if not full_files:
        print("No HUBERMAN_FULL_*_CHUNK_01 files found")
        return
    
    print(f"Re-chunking {len(full_files)} Huberman Full files...")
    
    for file in full_files:
        rechunk_file(file)
        # Delete original after successful chunking
        file.unlink()
        print(f"Deleted {file.name}\n")
    
    print("Re-chunking complete!")

if __name__ == "__main__":
    main()
