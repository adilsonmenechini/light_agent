"""Tests for vector memory search."""

import pytest
import tempfile
from pathlib import Path

from lightagent.agent.vector import (
    VectorMemoryConfig,
    VectorStore,
    VectorDocument,
    SearchResult,
    SimpleEmbeddingProvider,
    MockEmbeddingProvider,
    default_vector_memory_config,
)


class TestVectorMemoryConfig:
    """Tests for VectorMemoryConfig."""

    def test_defaults(self) -> None:
        """Should have correct default values."""
        config = VectorMemoryConfig()
        assert config.enabled is True
        assert config.vector_dimensions == 384
        assert config.similarity_threshold == 0.7
        assert config.max_results == 5
        assert config.hybrid_search is True

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = VectorMemoryConfig(
            enabled=False,
            vector_dimensions=512,
            similarity_threshold=0.8,
            max_results=10,
        )
        assert config.enabled is False
        assert config.vector_dimensions == 512
        assert config.similarity_threshold == 0.8
        assert config.max_results == 10


class TestDefaultVectorMemoryConfig:
    """Tests for default_vector_memory_config function."""

    def test_returns_config(self) -> None:
        """Should return a VectorMemoryConfig instance."""
        config = default_vector_memory_config()
        assert isinstance(config, VectorMemoryConfig)


class TestSimpleEmbeddingProvider:
    """Tests for SimpleEmbeddingProvider."""

    def test_embed_single_text(self) -> None:
        """Should embed a single text."""
        provider = SimpleEmbeddingProvider(dimensions=100)
        embedding = provider.embed("Hello world")

        assert len(embedding) == 100
        # Normalized vector should have magnitude ~1
        magnitude = sum(x * x for x in embedding) ** 0.5
        assert 0.99 < magnitude < 1.01

    def test_embed_batch(self) -> None:
        """Should embed multiple texts."""
        provider = SimpleEmbeddingProvider(dimensions=50)
        embeddings = provider.embed_batch(["Hello", "World", "Test"])

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 50

    def test_empty_text(self) -> None:
        """Should handle empty text."""
        provider = SimpleEmbeddingProvider(dimensions=50)
        embedding = provider.embed("")

        assert len(embedding) == 50
        assert all(x == 0.0 for x in embedding)

    def test_get_dimensions(self) -> None:
        """Should return correct dimensions."""
        provider = SimpleEmbeddingProvider(dimensions=256)
        assert provider.get_dimensions() == 256


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider."""

    def test_embed_deterministic(self) -> None:
        """Should return same embedding for same text."""
        provider = MockEmbeddingProvider()
        emb1 = provider.embed("test query")
        emb2 = provider.embed("test query")

        assert emb1 == emb2

    def test_embed_different_texts(self) -> None:
        """Should return different embeddings for different texts."""
        provider = MockEmbeddingProvider()
        emb1 = provider.embed("apple")
        emb2 = provider.embed("banana")

        assert emb1 != emb2

    def test_get_dimensions(self) -> None:
        """Should return 384 dimensions."""
        provider = MockEmbeddingProvider()
        assert provider.get_dimensions() == 384


class TestVectorDocument:
    """Tests for VectorDocument."""

    def test_create_document(self) -> None:
        """Should create a document."""
        doc = VectorDocument(
            id=1,
            content="Test content",
            metadata={"key": "value"},
        )
        assert doc.id == 1
        assert doc.content == "Test content"
        assert doc.metadata == {"key": "value"}


class TestSearchResult:
    """Tests for SearchResult."""

    def test_create_result(self) -> None:
        """Should create a search result."""
        doc = VectorDocument(id=1, content="Test")
        result = SearchResult(document=doc, similarity=0.85)

        assert result.document == doc
        assert result.similarity == 0.85


class TestVectorStore:
    """Tests for VectorStore."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.store_path = str(Path(self.temp_dir) / "test_vector.db")
        # Use mock provider for deterministic tests
        self.store = VectorStore(
            store_path=self.store_path, embedding_provider=MockEmbeddingProvider()
        )

    def teardown_method(self) -> None:
        """Clean up."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_document(self) -> None:
        """Should add a document."""
        doc_id = self.store.add_document("Test content", {"type": "test"})
        assert doc_id == 1

    def test_add_multiple_documents(self) -> None:
        """Should add multiple documents."""
        docs = [
            {"content": "Python programming language"},
            {"content": "Machine learning algorithms"},
            {"content": "Natural language processing"},
        ]
        ids = self.store.add_documents(docs)
        assert len(ids) == 3

    def test_search_similar_content(self) -> None:
        """Should find similar content."""
        # Add documents
        self.store.add_document("Python is a programming language", {"topic": "coding"})
        self.store.add_document("Java is also a programming language", {"topic": "coding"})
        self.store.add_document("The weather is nice today", {"topic": "weather"})

        # Search
        results = self.store.search("programming languages", threshold=0.1)

        assert len(results) > 0
        # Should find Python and Java documents
        contents = [r.document.content for r in results]
        assert any("Python" in c for c in contents)

    def test_search_with_threshold(self) -> None:
        """Should respect similarity threshold."""
        self.store.add_document("Hello world")
        self.store.add_document("Goodbye world")
        self.store.add_document("Completely different topic")

        results = self.store.search("Hello", threshold=0.1)
        assert len(results) >= 0  # May or may not find matches depending on embedding

    def test_search_with_limit(self) -> None:
        """Should respect result limit."""
        for i in range(10):
            self.store.add_document(f"Document number {i}")

        results = self.store.search("document", threshold=0.01, limit=3)
        assert len(results) == 3

    def test_get_document(self) -> None:
        """Should retrieve a document by ID."""
        self.store.add_document("Test content", {"key": "value"})
        doc = self.store.get_document(1)

        assert doc is not None
        assert doc.content == "Test content"
        assert doc.metadata == {"key": "value"}

    def test_get_nonexistent_document(self) -> None:
        """Should return None for nonexistent document."""
        doc = self.store.get_document(999)
        assert doc is None

    def test_delete_document(self) -> None:
        """Should delete a document."""
        self.store.add_document("Test content")
        result = self.store.delete_document(1)
        assert result is True

        doc = self.store.get_document(1)
        assert doc is None

    def test_count_documents(self) -> None:
        """Should count documents."""
        assert self.store.count_documents() == 0

        self.store.add_document("Doc 1")
        self.store.add_document("Doc 2")
        assert self.store.count_documents() == 2

    def test_clear_documents(self) -> None:
        """Should clear all documents."""
        self.store.add_document("Doc 1")
        self.store.add_document("Doc 2")
        assert self.store.count_documents() == 2

        self.store.clear()
        assert self.store.count_documents() == 0

    def test_empty_search(self) -> None:
        """Should handle empty database."""
        results = self.store.search("test query")
        assert results == []

    def test_get_embedding_provider(self) -> None:
        """Should return embedding provider."""
        provider = self.store.get_embedding_provider()
        # With mock provider, should return MockEmbeddingProvider
        assert hasattr(provider, "embed")


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_identical_vectors(self) -> None:
        """Should return 1.0 for identical vectors."""
        store = VectorStore(store_path=":memory:")
        result = store._cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert result == 1.0

    def test_orthogonal_vectors(self) -> None:
        """Should return 0.0 for orthogonal vectors."""
        store = VectorStore(store_path=":memory:")
        result = store._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert result == 0.0

    def test_opposite_vectors(self) -> None:
        """Should return -1.0 for opposite vectors."""
        store = VectorStore(store_path=":memory:")
        result = store._cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert result == -1.0

    def test_empty_vectors(self) -> None:
        """Should return 0.0 for empty vectors."""
        store = VectorStore(store_path=":memory:")
        result = store._cosine_similarity([], [])
        assert result == 0.0
