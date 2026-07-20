import pytest

def test_chunking_engine():
    from app.application.services.rag.chunking_engine import ChunkingEngine
    engine = ChunkingEngine(max_tokens=50, overlap=10)
    text = "Line 1\n\nLine 2\n\nLine 3"
    chunks = engine.chunk_document(text, {"doc_id": "test"})
    assert len(chunks) > 0
    assert chunks[0]["metadata"]["doc_id"] == "test"

@pytest.mark.asyncio
async def test_hybrid_search():
    from app.application.services.rag.hybrid_search import HybridSearchEngine
    engine = HybridSearchEngine()
    results = await engine.search("test query", "tenant_1")
    assert len(results) > 0
    assert results[0]["chunk_id"] == "chunk-123"
