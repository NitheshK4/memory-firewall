"""Unit tests for LocalSemanticEmbeddingStore and build_vector_store settings factory."""

from apps.api.app.config import Settings
from apps.api.app.db.vector import (
    VectorDocument,
    LocalSemanticEmbeddingStore,
    InMemoryVectorStore,
    OpenAIEmbeddingStore,
    build_vector_store,
)


def test_local_semantic_embedding_store_basic() -> None:
    """Test standard indexing, deletion, and semantic matching of LocalSemanticEmbeddingStore."""
    store = LocalSemanticEmbeddingStore(model_name="all-MiniLM-L6-v2")

    doc1 = VectorDocument(doc_id="doc1", text="I love drinking cold beer and other beverages on a hot day.")
    doc2 = VectorDocument(doc_id="doc2", text="The weather forecast predicts heavy rain tomorrow morning.")
    doc3 = VectorDocument(doc_id="doc3", text="Authentication requires a valid username and password.")

    store.add(doc1)
    store.add(doc2)
    store.add(doc3)

    # 1. Direct search by matching semantic keywords (e.g. synonym "drinks" or "alcohol" to "beer"/"beverages")
    results = store.similarity_search("alcohol and drinks", top_k=2)
    assert len(results) > 0
    assert results[0][0].doc_id == "doc1"
    # Similarity score should be reasonably high (> 0.25)
    assert results[0][1] > 0.25

    # 2. Match security credentials
    sec_results = store.similarity_search("login credentials secret", top_k=2)
    assert len(sec_results) > 0
    assert sec_results[0][0].doc_id == "doc3"

    # 3. Deletion test
    store.delete("doc3")
    deleted_results = store.similarity_search("login credentials secret", top_k=2)
    assert not any(doc.doc_id == "doc3" for doc, _ in deleted_results)


def test_build_vector_store_settings_routing() -> None:
    """Test that build_vector_store routes correctly according to Settings."""
    # Scenario A: OpenAI configured and active
    settings_openai = Settings(
        use_openai=True,
        openai_api_key="sk-mock-key-12345",
        use_local_semantic=False,
    )
    store_a = build_vector_store(settings_openai)
    assert isinstance(store_a, OpenAIEmbeddingStore)

    # Scenario B: OpenAI inactive, Local Semantic active (should load LocalSemanticEmbeddingStore)
    settings_local = Settings(
        use_openai=False,
        use_local_semantic=True,
        local_embedding_model="all-MiniLM-L6-v2",
    )
    store_b = build_vector_store(settings_local)
    assert isinstance(store_b, LocalSemanticEmbeddingStore)

    # Scenario C: Both inactive or disabled -> fallback to InMemoryVectorStore
    settings_fallback = Settings(
        use_openai=False,
        use_local_semantic=False,
    )
    store_c = build_vector_store(settings_fallback)
    assert isinstance(store_c, InMemoryVectorStore)
