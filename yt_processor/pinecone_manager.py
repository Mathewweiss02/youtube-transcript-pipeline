"""
Pinecone Integration for Wiki Pipeline
Manages vector database operations.
"""
import os
from typing import Any, Dict, List, Optional

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    from pinecone import Pinecone, ServerlessSpec


class PineconeManager:
    """Manage Pinecone vector database operations."""

    def __init__(self, api_key: str = None, index_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("Pinecone API key required")

        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME") or "youtube-wiki"

    def create_index(self, dimension: int = 1536):
        """Create index if it doesn't exist."""
        existing_indexes = self.pc.list_indexes().names()

        if self.index_name not in existing_indexes:
            print(f"Creating index '{self.index_name}'...")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1",
                ),
            )
            print(f"Index '{self.index_name}' created")
        else:
            print(f"Index '{self.index_name}' already exists")

    def delete_index(self):
        """Delete the index (use with caution)."""
        self.pc.delete_index(self.index_name)
        print(f"Index '{self.index_name}' deleted")

    def get_index_stats(self):
        """Get index statistics."""
        index = self.pc.index(self.index_name)
        return index.describe_index_stats()

    def upsert_chunks(
        self,
        channel: str,
        chunks_with_embeddings: List[Dict[str, Any]],
        batch_size: int = 100,
    ):
        """
        Upsert chunks to Pinecone namespace.

        Args:
            channel: Channel name (used as namespace)
            chunks_with_embeddings: Chunks with 'embedding' field
            batch_size: Number of records per batch
        """
        index = self.pc.index(self.index_name)
        namespace = index.namespace(channel)

        records = []
        for chunk in chunks_with_embeddings:
            if not chunk.get("embedding"):
                print(f"  Skipping chunk {chunk['id']} - no embedding")
                continue

            records.append(
                {
                    "id": chunk["id"],
                    "values": chunk["embedding"],
                    "metadata": {
                        "video_id": chunk["metadata"]["video_id"],
                        "title": chunk["metadata"]["title"],
                        "url": chunk["metadata"]["url"],
                        "channel": chunk["metadata"]["channel"],
                        "chunk_index": chunk["metadata"]["chunk_index"],
                        "total_chunks": chunk["metadata"]["total_chunks"],
                        "start_timestamp": chunk["metadata"]["start_timestamp"],
                        "duration": chunk["metadata"].get("duration", 0),
                        "topics": chunk.get("topics", []),
                        "guest": chunk.get("guest", ""),
                        "text": chunk["text"],
                        "text_preview": chunk["text"][:300],
                    },
                }
            )

        total = len(records)
        print(f"Upserting {total} records to namespace '{channel}'...")

        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            namespace.upsert(vectors=batch)
            print(
                f"  Batch {i // batch_size + 1}/"
                f"{(total - 1) // batch_size + 1}: {len(batch)} records"
            )

        print(f"Upserted {total} records")

    def query(
        self,
        channel: str,
        vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Query the vector database.

        Args:
            channel: Namespace to query
            vector: Query embedding
            top_k: Number of results
            filter_dict: Optional metadata filter

        Returns:
            List of match dictionaries
        """
        index = self.pc.index(self.index_name)
        namespace = index.namespace(channel)

        results = namespace.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )

        return results.matches or []

    def delete_namespace(self, channel: str):
        """Delete all vectors in a namespace."""
        index = self.pc.index(self.index_name)
        index.delete(delete_all=True, namespace=channel)
        print(f"Deleted all vectors in namespace '{channel}'")


if __name__ == "__main__":
    manager = PineconeManager()

    print("Creating index...")
    manager.create_index()

    print("\nIndex stats:")
    print(manager.get_index_stats())
