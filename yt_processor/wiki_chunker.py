"""
Wiki Transcript Chunker
Chunks transcripts for vector search with optimal settings.
"""
import tiktoken
from typing import Any, Dict, List


class TranscriptChunker:
    """Chunk transcripts using token-aware overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def chunk_transcript(
        self,
        transcript_text: str,
        video_metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Chunk transcript into retrievable segments.

        Args:
            transcript_text: Full cleaned transcript
            video_metadata: {video_id, title, url, channel, duration}

        Returns:
            List of chunk dicts with text, metadata, timestamps
        """
        tokens = self.encoding.encode(transcript_text)
        total_tokens = len(tokens)

        chunks = []
        start_idx = 0
        chunk_index = 0

        while start_idx < total_tokens:
            end_idx = min(start_idx + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.encoding.decode(chunk_tokens)

            position_ratio = start_idx / total_tokens if total_tokens > 0 else 0
            estimated_seconds = int(position_ratio * video_metadata.get("duration", 0))

            chunk = {
                "id": f"{video_metadata['video_id']}_chunk_{chunk_index}",
                "text": chunk_text,
                "metadata": {
                    "video_id": video_metadata["video_id"],
                    "title": video_metadata["title"],
                    "url": video_metadata["url"],
                    "channel": video_metadata["channel"],
                    "chunk_index": chunk_index,
                    "start_timestamp": estimated_seconds,
                    "duration": int(video_metadata.get("duration", 0)),
                    "total_chunks": None,
                },
            }
            chunks.append(chunk)

            start_idx += self.chunk_size - self.chunk_overlap
            chunk_index += 1

            if end_idx == total_tokens:
                break

        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = len(chunks)

        return chunks


def parse_markdown_transcript(file_path: str) -> tuple:
    """
    Parse a markdown transcript file.

    Returns:
        (metadata, transcript_text)
    """
    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    lines = content.split("\n")

    title = ""
    url = ""
    transcript_lines = []
    in_transcript = False

    for index, line in enumerate(lines):
        if index == 0 and line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("URL: "):
            url = line[5:].strip()
        elif line.startswith("---") and not in_transcript:
            in_transcript = True
        elif in_transcript:
            transcript_lines.append(line)

    transcript_text = "\n".join(transcript_lines).strip()

    video_id = ""
    if "youtube.com/watch?v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]

    metadata = {
        "title": title,
        "url": url,
        "video_id": video_id,
        "duration": 0,
    }

    return metadata, transcript_text


def chunk_transcript_file(file_path: str, channel: str) -> List[Dict[str, Any]]:
    """
    Process a single transcript file into chunks.

    Args:
        file_path: Path to markdown transcript
        channel: Channel name

    Returns:
        List of chunk dictionaries
    """
    metadata, transcript_text = parse_markdown_transcript(file_path)
    estimated_duration = len(transcript_text) / 20

    video_metadata = {
        "video_id": metadata["video_id"],
        "title": metadata["title"],
        "url": metadata["url"],
        "channel": channel,
        "duration": estimated_duration,
    }

    chunker = TranscriptChunker()
    return chunker.chunk_transcript(transcript_text, video_metadata)


if __name__ == "__main__":
    import sys

    test_file = r"c:\Users\aweis\Downloads\YouTube_Tools_Scripts\transcripts\Scotty_Optimal\SCOTTY_OPTIMAL_PART_00.md"

    if len(sys.argv) > 1:
        test_file = sys.argv[1]

    chunks = chunk_transcript_file(test_file, "Scotty_Optimal")
    print(f"Created {len(chunks)} chunks")

    for index, chunk in enumerate(chunks[:3], start=1):
        print(f"\nChunk {index}:")
        print(f"  ID: {chunk['id']}")
        print(f"  Timestamp: {chunk['metadata']['start_timestamp']}s")
        print(f"  Preview: {chunk['text'][:100]}...")
