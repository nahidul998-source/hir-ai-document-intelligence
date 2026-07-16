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
    Classifies documents based on metadata and preliminary layout text.
    """
    def __init__(self):
        self.keywords = {
            DocumentType.TECH_PACK: ["tech pack", "technical package", "style details", "construction", "techpack"],
            DocumentType.ORDER_SHEET: ["order sheet", "sales order", "ship date", "order qty"],
            DocumentType.BOM: ["bill of materials", "bom", "trim", "fabric consumption", "placement"],
            DocumentType.MEASUREMENT_SHEET: ["measurement", "spec", "size chart", "graded spec", "tol", "tolerance"],
            DocumentType.PURCHASE_ORDER: ["purchase order", "vendor", "po number", "po#"]
        }

    def classify(self, filename: str, first_page_text: str = "") -> DocumentType:
        """
        Classify document based on filename and first page text.
        """
        text_to_search = f"{filename} {first_page_text}".lower()
        
        scores = {doc_type: 0 for doc_type in DocumentType}
        
        for doc_type, keywords in self.keywords.items():
            for kw in keywords:
                if kw in text_to_search:
                    scores[doc_type] += 1
        
        max_score = max(scores.values())
        if max_score == 0:
            return DocumentType.GENERIC
            
        best_match = [dt for dt, score in scores.items() if score == max_score][0]
        return best_match
