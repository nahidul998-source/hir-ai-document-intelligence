import json
import logging
import asyncio
from typing import Dict, Any, Optional
import httpx

from app.domain.interfaces import IAIProvider

logger = logging.getLogger(__name__)

class LocalOpenAIProvider(IAIProvider):
    """
    OpenAI-Compatible AI Provider. Works with Ollama, LM Studio, vLLM, etc.
    """

    def __init__(self, name: str, enabled: bool, api_url: str, api_key: str, model_name: str, 
                 connect_timeout: int = 5, read_timeout: int = 60, retry_timeout: int = 10,
                 capabilities: Optional[Dict[str, Any]] = None):
        self.name = name
        self.enabled = enabled
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.retry_timeout = retry_timeout
        self.capabilities = capabilities or {
            "context_length": 4096,
            "json_mode": True,
            "vision": False,
            "streaming": False
        }

    async def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extracts JSON from markdown code blocks or plain text."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass

        raise ValueError("Failed to parse valid JSON from LLM response.")

    async def generate_json(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled:
            raise RuntimeError(f"Provider {self.name} is disabled.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 1 Retry loop for JSON parsing
        max_attempts = 2
        last_exception = None

        timeout_cfg = httpx.Timeout(
            self.read_timeout,
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=self.read_timeout
        )

        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            for attempt in range(max_attempts):
                try:
                    # Implement cancellation / global request timeout check
                    coro = client.post(
                        f"{self.api_url}/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    # Enforce strict cancellation support via asyncio.wait_for
                    response = await asyncio.wait_for(coro, timeout=float(self.read_timeout))
                    response.raise_for_status()
                    data = response.json()
                    
                    content = data["choices"][0]["message"]["content"]
                    return await self._extract_json(content)
                except (ValueError, KeyError, httpx.HTTPError, asyncio.TimeoutError) as e:
                    last_exception = e
                    logger.warning(f"[{self.name}] Attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        messages.append({"role": "assistant", "content": data["choices"][0]["message"]["content"] if 'data' in locals() and "choices" in data else ""})
                        messages.append({"role": "user", "content": "The previous response was not valid JSON. Please output strictly valid JSON matching the requested schema."})

        raise RuntimeError(f"[{self.name}] Failed to generate valid JSON after {max_attempts} attempts. Last error: {last_exception}")

    async def is_healthy(self) -> bool:
        if not self.enabled:
            return False
            
        try:
            timeout_cfg = httpx.Timeout(5.0, connect=2.0)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                # Check /models endpoint per OpenAI spec
                response = await client.get(f"{self.api_url}/models", headers=headers)
                response.raise_for_status()
                models_data = response.json()
                
                # Try to extract details if they exist in response to update capabilities
                if isinstance(models_data, dict) and "data" in models_data:
                    models_list = models_data["data"]
                    # If our model name matches one in the list, update capabilities if description exists
                    for m in models_list:
                        if m.get("id") == self.model_name:
                            # Context length detection or json capabilities can be customized here
                            pass
                            
                return True
        except Exception as e:
            logger.warning(f"[{self.name}] Health check failed: {e}")
            return False
