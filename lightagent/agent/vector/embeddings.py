"""Embedding providers for vector memory search."""

from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings.

        Returns:
            Number of dimensions.
        """
        pass


class SimpleEmbeddingProvider(EmbeddingProvider):
    """Simple word-based embedding provider.

    Uses a simple bag-of-words approach with TF-IDF-like weighting.
    No external API required.
    """

    def __init__(self, dimensions: int = 384):
        """Initialize simple embedding provider.

        Args:
            dimensions: Number of embedding dimensions.
        """
        self._dimensions = dimensions
        self._vocabulary: dict[str, int] = {}
        self._idf_weights: dict[int, float] = {}
        self._document_count = 0
        self._seen_words: set[str] = set()

    def _word_to_index(self, word: str) -> int:
        """Convert word to consistent index using hash.

        Args:
            word: Word to index.

        Returns:
            Index in vector space.
        """
        # Use hash for consistent indexing
        hash_val = hash(word)
        return abs(hash_val) % self._dimensions

    def embed(self, text: str) -> List[float]:
        """Generate embedding using simple word hashing.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        words = text.lower().split()
        if not words:
            return [0.0] * self._dimensions

        # Create vector using hash-based indexing
        vector = [0.0] * self._dimensions
        word_counts: dict[int, int] = {}
        unique_words = set(words)

        for word in words:
            idx = self._word_to_index(word)
            word_counts[idx] = word_counts.get(idx, 0) + 1

        # Apply TF weighting
        for idx, count in word_counts.items():
            tf = count / len(words)  # Term frequency
            vector[idx] = tf

        # Normalize
        magnitude = sum(v * v for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        # Update document stats
        self._document_count += 1
        for word in unique_words:
            if word not in self._seen_words:
                self._seen_words.add(word)

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        return [self.embed(text) for text in texts]

    def get_dimensions(self) -> int:
        """Get embedding dimensions.

        Returns:
            Number of dimensions.
        """
        return self._dimensions


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing.

    Returns deterministic fake embeddings based on text hash.
    """

    def embed(self, text: str) -> List[float]:
        """Generate mock embedding.

        Args:
            text: Text to embed.

        Returns:
            Mock embedding vector.
        """
        # Create deterministic fake embedding based on text
        hash_value = hash(text.lower())
        vector = [(hash_value >> (i * 8)) & 0xFF for i in range(32)]
        # Normalize
        magnitude = sum(v * v for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        return [float(v) for v in vector] + [0.0] * (384 - 32)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of mock embedding vectors.
        """
        return [self.embed(text) for text in texts]

    def get_dimensions(self) -> int:
        """Get embedding dimensions.

        Returns:
            Number of dimensions.
        """
        return 384
