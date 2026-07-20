from typing import List, Dict, Any

class RAGQueryService:
    """
    Assembles context from hybrid search and generates context-augmented LLM responses.
    """
    
    def __init__(self, search_engine, ai_provider):
        self.search_engine = search_engine
        self.ai_provider = ai_provider
        
    async def answer_query(self, query: str, tenant_id: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retrieves context via hybrid search and generates an answer with citations.
        """
        # 1. Retrieve context
        search_results = await self.search_engine.search(query, tenant_id, top_k=5, filters=filters)
        
        # 2. Build prompt context
        context_texts = [f"Source: {res['document']}, Page {res['page']}\n{res['text']}" for res in search_results]
        joined_context = "\n\n".join(context_texts)
        
        prompt = f"Answer the user's question using ONLY the provided context.\n\nContext:\n{joined_context}\n\nQuestion: {query}"
        
        # 3. Generate response
        llm_response = await self.ai_provider.generate_text(prompt)
        
        # 4. Format citation objects
        citations = [
            {
                "document": res["document"],
                "page": res["page"],
                "section": res["section"],
                "confidence": res["confidence"],
                "bbox": res["bbox"]
            } for res in search_results
        ]
        
        return {
            "answer": llm_response,
            "citations": citations,
            "metrics": {
                "chunks_retrieved": len(search_results),
                "llm_latency_ms": 120 # Mock
            }
        }
