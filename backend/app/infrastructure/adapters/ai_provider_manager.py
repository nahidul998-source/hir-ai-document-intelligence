import os
import yaml
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.domain.interfaces import IAIProvider
from app.infrastructure.adapters.providers.openai_provider import LocalOpenAIProvider
from app.database.session import async_session_maker
from app.infrastructure.database.models_ai_providers import AIProviderConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)

class AIProviderManager:
    """Manages AI provider lifecycle, configuration database loading, and health checks."""

    def __init__(self, config_path: Optional[str] = None):
        self.providers: Dict[str, LocalOpenAIProvider] = {}
        self.priority: List[str] = []
        
        # Extended Telemetry metrics
        self.metrics: Dict[str, Dict[str, Any]] = {}
        
        # We don't reload synchronously in init anymore since DB calls are async.
        # It will be initialized via lifespan or lazy-loaded.
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the manager by loading config from DB."""
        if not self._initialized:
            await self.reload_config()
            self._initialized = True

    async def reload_config(self) -> None:
        """Loads or reloads the configuration from the database."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(AIProviderConfig).order_by(AIProviderConfig.priority_index.asc())
            )
            db_configs = result.scalars().all()
            
            # If nothing in database, bootstrap from ai.yaml (as fallback)
            if not db_configs:
                logger.warning("No AI Provider configurations found in database. Seeding not complete?")
                # Fallback to loading YAML if database is empty (for bootstrap)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(current_dir, "../../../../configs/ai.yaml")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        yaml_data = yaml.safe_load(f)
                    priority_list = yaml_data.get("priority", [])
                    providers_data = yaml_data.get("providers", {})
                    # Just return simulated configs list
                    db_configs = []
                    for idx, k in enumerate(priority_list):
                        if k in providers_data:
                            p = providers_data[k]
                            db_configs.append(AIProviderConfig(
                                key=k,
                                name=p.get("name", k),
                                enabled=p.get("enabled", True),
                                api_url=p.get("api_url", ""),
                                api_key=p.get("api_key", ""),
                                model_name=p.get("model_name", ""),
                                connect_timeout=p.get("connect_timeout", 5),
                                read_timeout=p.get("timeout", 60),
                                retry_timeout=p.get("retry_timeout", 10),
                                priority_index=idx,
                                capabilities=p.get("capabilities", {})
                            ))

            new_providers = {}
            self.priority = []
            
            for pconfig in db_configs:
                key = pconfig.key
                self.priority.append(key)
                
                api_key = pconfig.api_key
                if key == "github":
                    api_key = os.environ.get("GITHUB_TOKEN") or api_key
                elif key == "gemini":
                    api_key = os.environ.get("GEMINI_API_KEY") or api_key

                api_url = pconfig.api_url
                if key == "gemini" and "openai" not in api_url.lower():
                    api_url = "https://generativelanguage.googleapis.com/v1beta/openai"
                    
                new_providers[key] = LocalOpenAIProvider(
                    name=pconfig.name,
                    enabled=pconfig.enabled,
                    api_url=api_url,
                    api_key=api_key,
                    model_name=pconfig.model_name,
                    connect_timeout=pconfig.connect_timeout,
                    read_timeout=pconfig.read_timeout,
                    retry_timeout=pconfig.retry_timeout,
                    capabilities=pconfig.capabilities
                )
                
                if key not in self.metrics:
                    self.metrics[key] = {
                        "requests": 0,
                        "errors": 0,
                        "latencies": [],  # Store recent latencies to calculate p95, p99
                        "latency": 0.0,   # average latency
                        "p95_latency": 0.0,
                        "success_rate": 100.0,
                        "failure_rate": 0.0,
                        "retry_count": 0,
                        "fallback_count": 0,
                        "timeout_count": 0,
                        "last_successful_request": None,
                        "last_error": None,
                        "last_health_check": None,
                        "status": "Unknown",
                        "uptime_pings": 0,
                        "uptime_successes": 0
                    }

            self.providers = new_providers

    def update_metrics(self, key: str, latency_ms: Optional[float] = None, error: Optional[str] = None, timeout: bool = False, retry: bool = False) -> None:
        """Helper to thread-safely record operational telemetry in memory."""
        if key not in self.metrics:
            return
            
        m = self.metrics[key]
        m["requests"] += 1
        
        if retry:
            m["retry_count"] += 1
            
        if error:
            m["errors"] += 1
            m["last_error"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "message": error
            }
            m["status"] = "Error"
            if timeout:
                m["timeout_count"] += 1
        else:
            m["last_successful_request"] = datetime.utcnow().isoformat()
            m["status"] = "Healthy"
            if latency_ms is not None:
                m["latencies"].append(latency_ms)
                # Keep last 100 latencies for percentile calculations
                if len(m["latencies"]) > 100:
                    m["latencies"].pop(0)
                
                # Calculate average
                m["latency"] = sum(m["latencies"]) / len(m["latencies"])
                
                # Calculate P95
                sorted_lats = sorted(m["latencies"])
                p95_idx = int(len(sorted_lats) * 0.95)
                m["p95_latency"] = sorted_lats[p95_idx] if sorted_lats else latency_ms
                
        # Recalculate success / failure rates
        total_reqs = m["requests"]
        if total_reqs > 0:
            m["failure_rate"] = (m["errors"] / total_reqs) * 100
            m["success_rate"] = 100.0 - m["failure_rate"]

    async def ping_all_providers(self) -> None:
        """Run health check against all active providers and track uptime statistics."""
        for key, provider in self.providers.items():
            if not provider.enabled:
                continue
                
            is_healthy = await provider.is_healthy()
            
            m = self.metrics[key]
            m["last_health_check"] = datetime.utcnow().isoformat()
            m["uptime_pings"] += 1
            if is_healthy:
                m["status"] = "Healthy"
                m["uptime_successes"] += 1
            else:
                m["status"] = "Unhealthy"

    async def get_active_provider(self) -> LocalOpenAIProvider:
        """Compatibility helper to get the first healthy provider."""
        await self.initialize()
        for provider_key in self.priority:
            provider = self.providers.get(provider_key)
            if provider and provider.enabled:
                if await provider.is_healthy():
                    self.metrics[provider_key]["status"] = "Healthy"
                    self.metrics[provider_key]["last_health_check"] = datetime.utcnow().isoformat()
                    return provider
                else:
                    self.metrics[provider_key]["status"] = "Unhealthy"
                    self.metrics[provider_key]["last_health_check"] = datetime.utcnow().isoformat()
                    
        raise RuntimeError("No healthy AI Providers are available. Fallback exhausted.")

    async def generate_json(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Compatibility helper to generate JSON using the orchestrator flow."""
        from app.application.services.ai.orchestrator import AIOrchestrator
        orch = AIOrchestrator(self)
        res = await orch.generate_json(prompt, schema, "generic", system_prompt)
        return res["data"]
