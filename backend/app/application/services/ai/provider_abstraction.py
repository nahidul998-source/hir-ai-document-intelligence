import abc
from typing import List, Dict, Any

class BaseAIProvider(abc.ABC):
    """
    Abstract Base Class for AI Providers (OpenAI, Gemini, HuggingFace, etc.)
    Ensures seamless switching between models for enterprise deployments.
    """
    
    @abc.abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        pass
        
    @abc.abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        pass


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_embedding(self, text: str) -> List[float]:
        # Mock implementation
        return [0.0] * 1536
        
    async def generate_text(self, prompt: str, **kwargs) -> str:
        # Mock implementation
        return "This is a response from OpenAI."


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_embedding(self, text: str) -> List[float]:
        # Mock implementation
        return [0.0] * 768
        
    async def generate_text(self, prompt: str, **kwargs) -> str:
        # Mock implementation
        return "This is a response from Gemini."
