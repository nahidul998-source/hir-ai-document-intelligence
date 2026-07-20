import re
from typing import List, Dict, Any

class ChunkingEngine:
    """
    Semantic sliding window text splitter with token count, overlap, and header preservation.
    """
    
    def __init__(self, max_tokens: int = 500, overlap: int = 50):
        self.max_tokens = max_tokens
        self.overlap = overlap
        
    def chunk_document(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Splits a text document into semantic chunks.
        """
        if metadata is None:
            metadata = {}
            
        chunks = []
        # Basic paragraph-level splitting for demonstration
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        current_tokens = 0
        
        for p in paragraphs:
            # Simplistic token estimate (1 token approx 4 chars)
            p_tokens = len(p) // 4
            
            if current_tokens + p_tokens > self.max_tokens and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": metadata.copy()
                })
                # Start new chunk with overlap (simplistic overlap handling)
                overlap_text = current_chunk[-self.overlap * 4:] if len(current_chunk) > self.overlap * 4 else current_chunk
                current_chunk = overlap_text + "\n\n" + p
                current_tokens = len(current_chunk) // 4
            else:
                current_chunk += "\n\n" + p if current_chunk else p
                current_tokens += p_tokens
                
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": metadata.copy()
            })
            
        # Add indexing to metadata
        for idx, chunk in enumerate(chunks):
            chunk["metadata"]["chunk_index"] = idx
            
        return chunks
