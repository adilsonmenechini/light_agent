"""Vector Memory Search for semantic similarity matching.

Provides semantic search capabilities using embeddings for long-term memory.
"""

from .config import VectorMemoryConfig, default_vector_memory_config
from .store import VectorStore, VectorDocument, SearchResult
from .embeddings import EmbeddingProvider, SimpleEmbeddingProvider, MockEmbeddingProvider

__all__ = [
    "VectorMemoryConfig",
    "default_vector_memory_config",
    "VectorStore",
    "VectorDocument",
    "SearchResult",
    "EmbeddingProvider",
    "SimpleEmbeddingProvider",
    "MockEmbeddingProvider",
]
