"""Vector store for semantic memory search."""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import VectorMemoryConfig, default_vector_memory_config
from .embeddings import EmbeddingProvider, SimpleEmbeddingProvider


@dataclass
class VectorDocument:
    """A document stored in the vector database."""

    id: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Result from a vector similarity search."""

    document: VectorDocument
    similarity: float


class VectorStore:
    """Vector database for semantic similarity search.

    Stores documents with their embeddings and supports similarity search.
    """

    def __init__(
        self,
        config: Optional[VectorMemoryConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        store_path: Optional[str] = None,
    ):
        """Initialize vector store.

        Args:
            config: Vector memory configuration.
            embedding_provider: Provider for generating embeddings.
            store_path: Path to store the database.
        """
        self.config = config or default_vector_memory_config()
        self._embedding_provider = embedding_provider or SimpleEmbeddingProvider(
            self.config.vector_dimensions
        )
        self._store_path = store_path or self.config.store_path

        if self._store_path:
            path = Path(self._store_path)
        else:
            # Default to data/vector_store/
            path = Path("data/vector_store/vector.db")

        path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embedding BLOB,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create index on content for fallback text search
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content ON documents(content)
            """)
            conn.commit()

    def _embeddings_to_blob(self, embeddings: List[float]) -> bytes:
        """Convert embeddings to blob for storage.

        Args:
            embeddings: List of floats.

        Returns:
            Binary blob.
        """
        import struct

        return struct.pack(f"{len(embeddings)}f", *embeddings)

    def _blob_to_embeddings(self, blob: bytes) -> List[float]:
        """Convert blob back to embeddings.

        Args:
            blob: Binary blob.

        Returns:
            List of floats.
        """
        import struct

        num_floats = len(blob) // 4
        return list(struct.unpack(f"{num_floats}f", blob))

    def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True,
    ) -> int:
        """Add a document to the store.

        Args:
            content: Document content.
            metadata: Optional metadata.
            generate_embedding: Whether to generate embedding.

        Returns:
            Document ID.
        """
        embedding = None
        if generate_embedding:
            embedding = self._embedding_provider.embed(content)

        embedding_blob = None
        if embedding:
            embedding_blob = self._embeddings_to_blob(embedding)

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO documents (content, metadata, embedding)
                VALUES (?, ?, ?)
                """,
                (content, json.dumps(metadata or {}), embedding_blob),
            )
            conn.commit()
            return cursor.lastrowid

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        content_key: str = "content",
        metadata_key: Optional[str] = None,
    ) -> List[int]:
        """Add multiple documents.

        Args:
            documents: List of document dicts with content.
            content_key: Key for content in dicts.
            metadata_key: Optional key for metadata.

        Returns:
            List of document IDs.
        """
        ids = []
        for doc in documents:
            content = doc.get(content_key, "")
            metadata = doc.get(metadata_key) if metadata_key else None
            doc_id = self.add_document(content, metadata)
            ids.append(doc_id)
        return ids

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """Search for similar documents.

        Args:
            query: Search query.
            limit: Maximum results.
            threshold: Minimum similarity threshold.

        Returns:
            List of search results.
        """
        limit = limit or self.config.max_results
        threshold = threshold or self.config.similarity_threshold

        # Generate query embedding
        query_embedding = self._embedding_provider.embed(query)

        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, content, metadata, embedding, created_at FROM documents"
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        results = []
        for row in rows:
            embedding_blob = row["embedding"]
            if embedding_blob:
                doc_embedding = self._blob_to_embeddings(embedding_blob)
                similarity = self._cosine_similarity(query_embedding, doc_embedding)

                if similarity >= threshold:
                    doc = VectorDocument(
                        id=row["id"],
                        content=row["content"],
                        metadata=json.loads(row["metadata"] or "{}"),
                        embedding=list(doc_embedding),
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                    results.append(SearchResult(document=doc, similarity=similarity))

        # Sort by similarity and limit
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:limit]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Similarity score between -1 and 1.
        """
        if not a or not b:
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(y * y for y in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def get_document(self, doc_id: int) -> Optional[VectorDocument]:
        """Get a document by ID.

        Args:
            doc_id: Document ID.

        Returns:
            Document or None.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, content, metadata, embedding, created_at FROM documents WHERE id = ?",
                (doc_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        embedding_blob = row["embedding"]
        embedding = None
        if embedding_blob:
            embedding = self._blob_to_embeddings(embedding_blob)

        return VectorDocument(
            id=row["id"],
            content=row["content"],
            metadata=json.loads(row["metadata"] or "{}"),
            embedding=embedding,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document.

        Args:
            doc_id: Document ID.

        Returns:
            True if deleted.
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count_documents(self) -> int:
        """Get document count.

        Returns:
            Number of documents.
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            return cursor.fetchone()[0]

    def clear(self) -> None:
        """Clear all documents."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM documents")
            conn.commit()

    def get_embedding_provider(self) -> EmbeddingProvider:
        """Get the embedding provider.

        Returns:
            Embedding provider.
        """
        return self._embedding_provider
