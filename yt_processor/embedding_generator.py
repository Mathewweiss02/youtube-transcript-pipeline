"""
Embedding Generator for Wiki Pipeline
Generates embeddings using OpenAI text-embedding-3-small.
"""
import os
from typing import Any, Dict, List

import openai
from tenacity import retry, stop_after_attempt, wait_exponential


class EmbeddingGenerator:
    """Generate embeddings for transcript chunks."""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        self.batch_size = 100
        self.last_usage = {
            "tokens": 0,
            "estimated_cost": 0.0,
            "batch_count": 0,
        }

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    def _generate_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Generate embeddings for a batch of texts."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float",
        )

        return [
            {
                "embedding": item.embedding,
                "index": item.index,
            }
            for item in response.data
        ]

    def process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all chunks in batches and add embeddings.

        Args:
            chunks: List of chunk dicts with 'text' field

        Returns:
            Chunks with added 'embedding' field
        """
        results = []
        total_tokens = 0
        batch_count = 0

        print(f"Processing {len(chunks)} chunks in batches of {self.batch_size}...")

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            texts = [chunk["text"] for chunk in batch]
            batch_count += 1

            print(
                f"  Batch {i // self.batch_size + 1}/"
                f"{(len(chunks) - 1) // self.batch_size + 1}: {len(batch)} chunks"
            )

            try:
                embeddings = self._generate_batch(texts)

                for chunk, emb in zip(batch, embeddings):
                    results.append(
                        {
                            **chunk,
                            "embedding": emb["embedding"],
                        }
                    )

                total_tokens += sum(len(text) // 4 for text in texts)

            except Exception as exc:
                print(f"    Error in batch: {exc}")
                for chunk in batch:
                    results.append(
                        {
                            **chunk,
                            "embedding": None,
                        }
                    )

        cost = (total_tokens / 1_000_000) * 0.02
        self.last_usage = {
            "tokens": total_tokens,
            "estimated_cost": cost,
            "batch_count": batch_count,
        }
        print(f"\nEstimated cost: ${cost:.4f} ({total_tokens:,} tokens)")

        return results

    def get_last_usage(self) -> Dict[str, Any]:
        """Return usage summary from the last embedding run."""
        return dict(self.last_usage)

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        response = self.client.embeddings.create(
            model=self.model,
            input=query,
            encoding_format="float",
        )
        return response.data[0].embedding


if __name__ == "__main__":
    import sys

    from wiki_chunker import chunk_transcript_file

    test_file = r"c:\Users\aweis\Downloads\YouTube_Tools_Scripts\transcripts\Scotty_Optimal\SCOTTY_OPTIMAL_PART_00.md"

    if len(sys.argv) > 1:
        test_file = sys.argv[1]

    print("Chunking transcript...")
    chunks = chunk_transcript_file(test_file, "Scotty_Optimal")
    print(f"Created {len(chunks)} chunks")

    print("\nGenerating embeddings...")
    generator = EmbeddingGenerator()
    chunks_with_embeddings = generator.process_chunks(chunks)

    print(f"\nGenerated {len(chunks_with_embeddings)} embeddings")
    print(f"Sample embedding dimension: {len(chunks_with_embeddings[0]['embedding'])}")
