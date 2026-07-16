import os
import yaml
from typing import Dict, Any, List, Optional
from app.domain.interfaces import IAIProvider


class MockAIProvider(IAIProvider):
    """Placeholder AI provider for Phase 1 compilation and test verification."""

    def __init__(self, name: str, enabled: bool, api_url: str, api_key: str, model_name: str, healthy: bool = True):
        self.name = name
        self.enabled = enabled
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self._healthy = healthy

    async def generate_json(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled or not self._healthy:
            raise RuntimeError(f"Provider {self.name} is not available.")
        # Return a simple mock matching a standard format for testing/Phase 1 verification
        return {"provider": self.name, "status": "extracted_mock_data"}

    async def is_healthy(self) -> bool:
        return self.enabled and self._healthy


class AIProviderManager:
    """Manages AI provider priority routing and automatic fallback based on config/ai.yaml."""

    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            # Fallback path finding relative to runtime root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "../../../../configs/ai.yaml")

        self.config_path = os.path.abspath(config_path)
        self.providers: Dict[str, IAIProvider] = {}
        self.priority: List[str] = []
        self._load_config()

    def _load_config(self) -> None:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"AI config file not found at {self.config_path}")

        with open(self.config_path, "r") as f:
            config_data = yaml.safe_load(f)

        providers_config = config_data.get("providers", {})
        self.priority = config_data.get("priority", [])

        for key, pconfig in providers_config.items():
            # Inject actual keys from environments if available/not configured in YAML
            api_key = pconfig.get("api_key") or ""
            if key == "github":
                api_key = os.environ.get("GITHUB_TOKEN") or api_key
            elif key == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY") or api_key

            self.providers[key] = MockAIProvider(
                name=pconfig.get("name", key),
                enabled=pconfig.get("enabled", True),
                api_url=pconfig.get("api_url", ""),
                api_key=api_key,
                model_name=pconfig.get("model_name", "")
            )

    def set_provider_health(self, key: str, healthy: bool) -> None:
        """Helper to simulate provider failures in testing."""
        if key in self.providers and isinstance(self.providers[key], MockAIProvider):
            self.providers[key]._healthy = healthy

    async def get_active_provider(self) -> IAIProvider:
        """Returns the highest priority healthy provider. Fallback routing logic."""
        for provider_key in self.priority:
            provider = self.providers.get(provider_key)
            if provider and await provider.is_healthy():
                return provider
        raise RuntimeError("No healthy AI Providers are available. Fallback exhausted.")

    async def generate_json(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Tries to execute generation with the active provider, falling back to next available on failure."""
        for provider_key in self.priority:
            provider = self.providers.get(provider_key)
            if not provider:
                continue

            try:
                if await provider.is_healthy():
                    return await provider.generate_json(prompt, schema, system_prompt)
            except Exception as e:
                # Log provider failure and fallback to next
                print(f"Provider {provider_key} failed: {e}. Attempting fallback...")
                continue

        raise RuntimeError("AI Generation failed. All configured fallback providers failed or are offline.")
