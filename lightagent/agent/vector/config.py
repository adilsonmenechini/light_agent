"""Configuration for Vector Memory Search."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EmbeddingProviderType(Enum):
    """Available embedding providers."""

    SIMPLE = "simple"  # Word-based embeddings (no API needed)
    OPENAI = "openai"  # OpenAI embeddings
    OLLAMA = "ollama"  # Ollama local embeddings


@dataclass
class VectorMemoryConfig:
    """Configuration for vector memory search.

    Attributes:
        enabled: Whether vector search is enabled.
        provider_type: Type of embedding provider to use.
        embedding_model: Model name for embeddings (if applicable).
        vector_dimensions: Dimensions of embedding vectors.
        similarity_threshold: Minimum similarity score for results.
        max_results: Maximum results to return.
        hybrid_search: Whether to combine BM25 and semantic search.
        store_path: Path to store vector database.
    """

    enabled: bool = True
    provider_type: EmbeddingProviderType = EmbeddingProviderType.SIMPLE
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimensions: int = 384
    similarity_threshold: float = 0.7
    max_results: int = 5
    hybrid_search: bool = True
    store_path: Optional[str] = None


def default_vector_memory_config() -> VectorMemoryConfig:
    """Get default vector memory configuration."""
    return VectorMemoryConfig()
