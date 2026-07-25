import logging
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from app.database.session import async_session_maker
from app.infrastructure.database.models import AIProviderRoutingRule
from sqlalchemy import select

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """
    Orchestrates LLM generation: selects providers based on document type, 
    capabilities, health, manages retries, and records execution metrics.
    """

    def __init__(self, manager: AIProviderManager):
        self.manager = manager

    async def get_route_for_document(self, document_type: str) -> List[str]:
        """Query database for custom routing rules, falling back to manager priority list."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(AIProviderRoutingRule).where(AIProviderRoutingRule.document_type == document_type)
                )
                rule = result.scalar_one_or_none()
                if rule and rule.provider_keys:
                    return rule.provider_keys
                
                # Fallback to generic route
                result = await session.execute(
                    select(AIProviderRoutingRule).where(AIProviderRoutingRule.document_type == "generic")
                )
                generic_rule = result.scalar_one_or_none()
                if generic_rule and generic_rule.provider_keys:
                    return generic_rule.provider_keys
        except Exception:
            pass

        # Default fallback to global manager priority list
        return self.manager.priority

    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        document_type: str,
        system_prompt: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        forced_provider_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes JSON extraction. Resolves best candidate provider using capabilities 
        and routing rules, retries, and performs fallbacks.
        """
        # Ensure manager has loaded configurations
        await self.manager.initialize()

        request_id = str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        required_caps = required_capabilities or ["json_mode"]

        # Step 1: Resolve provider priority route for this document type
        if forced_provider_key:
            provider_route = [forced_provider_key]
        else:
            provider_route = await self.get_route_for_document(document_type)

        # Step 2: Iterate through fallback sequence
        fallback_count = 0
        last_exception = None

        for provider_key in provider_route:
            provider = self.manager.providers.get(provider_key)
            if not provider or not provider.enabled:
                continue

            # Capability verification (context window, json mode etc.)
            if not forced_provider_key:
                capabilities_match = True
                for cap in required_caps:
                    if not provider.capabilities.get(cap, False):
                        capabilities_match = False
                        break

                if not capabilities_match:
                    logger.info(f"[Orchestrator] Skipping provider '{provider_key}': capabilities mismatch.")
                    continue

            # Verify health status
            metrics = self.manager.metrics.get(provider_key, {})
            if metrics.get("status") == "Unhealthy" or not await provider.is_healthy():
                logger.info(f"[Orchestrator] Skipping provider '{provider_key}': Unhealthy state.")
                continue

            # Try generating
            retry_count = 0
            start_time = datetime.now(timezone.utc).replace(tzinfo=None)
            
            logger.info(
                f"[Orchestrator] Request {request_id} (Trace: {trace_id}) routing to '{provider_key}' "
                f"for document type '{document_type}'."
            )

            try:
                # Actual LLM Call
                result = await provider.generate_json(prompt, schema, system_prompt)
                
                # Success metrics logging
                latency_ms = (datetime.now(timezone.utc).replace(tzinfo=None) - start_time).total_seconds() * 1000
                self.manager.update_metrics(
                    key=provider_key,
                    latency_ms=latency_ms
                )
                
                logger.info(
                    f"[Orchestrator] SUCCESS | Request: {request_id} | Trace: {trace_id} | "
                    f"Provider: {provider_key} | Latency: {latency_ms:.2f}ms | Fallbacks: {fallback_count}"
                )
                return {
                    "data": result,
                    "provider": provider_key,
                    "model": provider.model_name,
                    "latency_ms": latency_ms,
                    "fallback_count": fallback_count,
                    "trace_id": trace_id
                }

            except Exception as e:
                latency_ms = (datetime.now(timezone.utc).replace(tzinfo=None) - start_time).total_seconds() * 1000
                is_timeout = isinstance(e, asyncio.TimeoutError)
                
                logger.warning(
                    f"[Orchestrator] FAILURE | Request: {request_id} | Trace: {trace_id} | "
                    f"Provider: {provider_key} | Error: {str(e)} | Latency: {latency_ms:.2f}ms"
                )
                
                # Log telemetry metrics
                self.manager.update_metrics(
                    key=provider_key,
                    latency_ms=latency_ms,
                    error=str(e),
                    timeout=is_timeout
                )
                
                # Increment fallback tracker
                fallback_count += 1
                last_exception = e
                # Record fallback count in metrics
                if provider_key in self.manager.metrics:
                    self.manager.metrics[provider_key]["fallback_count"] = self.manager.metrics[provider_key].get("fallback_count", 0) + 1
                
                continue

        raise RuntimeError(
            f"AI Generation failed. All configured fallback providers failed or were ineligible "
            f"for document type '{document_type}' (Trace: {trace_id}). Last error: {str(last_exception)}"
        )
