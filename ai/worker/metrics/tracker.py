import time
from typing import Dict, Any

class MetricsTracker:
    def __init__(self):
        self.start_time = None
        self.ocr_start = None
        self.ocr_duration = None
        self.llm_start = None
        self.llm_duration = None
        self.tokens_used = 0
        self.provider = "unknown"
        
    def start(self):
        self.start_time = time.time()
        
    def start_ocr(self):
        self.ocr_start = time.time()
        
    def end_ocr(self):
        if self.ocr_start:
            self.ocr_duration = int((time.time() - self.ocr_start) * 1000)
            
    def start_llm(self, provider: str):
        self.provider = provider
        self.llm_start = time.time()
        
    def end_llm(self, tokens: int = 0):
        if self.llm_start:
            self.llm_duration = int((time.time() - self.llm_start) * 1000)
        self.tokens_used = tokens
        
    def get_metrics(self) -> Dict[str, Any]:
        total_time = int((time.time() - self.start_time) * 1000) if self.start_time else 0
        
        cost = (self.tokens_used / 1000) * 0.002
        
        return {
            "total_processing_time_ms": total_time,
            "ocr_time_ms": self.ocr_duration,
            "llm_latency_ms": self.llm_duration,
            "tokens_used": self.tokens_used,
            "provider_name": self.provider,
            "estimated_cost_usd": cost
        }
