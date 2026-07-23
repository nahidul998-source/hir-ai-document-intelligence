from enum import Enum

class DocumentType(str, Enum):
    ORDER_SHEET = "order_sheet"
    TECH_PACK = "tech_pack"
    BOM = "bom"
    PURCHASE_ORDER = "purchase_order"
    MEASUREMENT_SHEET = "measurement_sheet"
    GENERIC = "generic"

class DocumentClassifier:
    """
    Classifies documents using AI LLM reasoning (Zero-shot classification).
    """
    def __init__(self, ai_orchestrator=None):
        self.ai = ai_orchestrator

    async def classify(self, filename: str, first_page_text: str = "") -> dict:
        """
        Classify document based on filename and first page text using LLM.
        """
        if not self.ai:
            # Fallback for testing if no orchestrator provided
            return {"document_type": DocumentType.TECH_PACK.value, "confidence": 1.0, "reasoning": "Fallback"}

        prompt = f"""
        Analyze the following text extracted from the first few pages of a document and its filename.
        Determine which of the following document types it is:
        {[dt.value for dt in DocumentType]}
        
        Filename: {filename}
        Text: {first_page_text[:3000]}
        
        Provide your reasoning and a confidence score between 0.0 and 1.0.
        """
        schema = {
            "type": "object",
            "properties": {
                "document_type": {"type": "string", "enum": [dt.value for dt in DocumentType]},
                "reasoning": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["document_type", "reasoning", "confidence"]
        }
        
        try:
            res = await self.ai.generate_json(
                prompt=prompt,
                schema=schema,
                document_type="classification",
                system_prompt="You are an expert Garment Document Classifier."
            )
            return res["data"]
        except Exception as e:
            return {"document_type": DocumentType.GENERIC.value, "confidence": 0.0, "reasoning": f"Error: {e}"}
