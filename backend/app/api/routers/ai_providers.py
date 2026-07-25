from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel
from sqlalchemy import select, update

from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from app.database.session import async_session_maker
from app.infrastructure.database.models import AIProviderConfig, AIProviderRoutingRule
from app.infrastructure.repositories.ai_providers import AIProviderRepository
from app.api.deps import _ai_provider_manager as ai_manager

router = APIRouter(tags=["AI Providers"])

class PriorityUpdateRequest(BaseModel):
    priority: List[str]

class RoutingUpdateRequest(BaseModel):
    document_type: str
    provider_keys: List[str]

@router.get("")
async def list_providers():
    """List all AI providers, their DB config, and runtime metrics."""
    await ai_manager.initialize()
    
    async with async_session_maker() as session:
        repo = AIProviderRepository(session)
        db_configs = await repo.get_all_configs()
        
    result_list = []
    priority_list = []
    for p_cfg in db_configs:
        key = p_cfg.key
        priority_list.append(key)
        metrics = ai_manager.metrics.get(key, {})
        result_list.append({
            "key": key,
            "name": p_cfg.name,
            "enabled": p_cfg.enabled,
            "api_url": p_cfg.api_url,
            "model_name": p_cfg.model_name,
            "priority_index": p_cfg.priority_index,
            "status": metrics.get("status", "Unknown"),
            "latency": metrics.get("latency", 0.0),
            "p95_latency": metrics.get("p95_latency", 0.0),
            "requests": metrics.get("requests", 0),
            "errors": metrics.get("errors", 0),
            "success_rate": metrics.get("success_rate", 100.0),
            "failure_rate": metrics.get("failure_rate", 0.0),
            "retry_count": metrics.get("retry_count", 0),
            "fallback_count": metrics.get("fallback_count", 0),
            "timeout_count": metrics.get("timeout_count", 0),
            "last_successful_request": metrics.get("last_successful_request"),
            "last_error": metrics.get("last_error"),
            "last_health_check": metrics.get("last_health_check"),
            "capabilities": p_cfg.capabilities
        })
        
    return {"providers": result_list, "priority": priority_list}


@router.post("/{key}/test")
async def test_connection(key: str):
    """Test connection to a specific provider."""
    await ai_manager.initialize()
    provider = ai_manager.providers.get(key)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {key} not found")
        
    is_healthy = await provider.is_healthy()
    
    # Update in-memory status
    metrics = ai_manager.metrics[key]
    from datetime import datetime
    metrics["last_health_check"] = datetime.now(timezone.utc).isoformat()
    metrics["status"] = "Healthy" if is_healthy else "Unhealthy"
    
    return {"healthy": is_healthy}


@router.post("/{key}/toggle")
async def toggle_provider(key: str):
    """Toggle a provider's enabled status in database and reload."""
    await ai_manager.initialize()
    
    async with async_session_maker() as session:
        repo = AIProviderRepository(session)
        p_cfg = await repo.get_config_by_key(key)
        if not p_cfg:
            raise HTTPException(status_code=404, detail="Provider not found")
            
        new_status = not p_cfg.enabled
        p_cfg.enabled = new_status
        await session.commit()
        
    await ai_manager.reload_config()
    return {"status": "success", "enabled": new_status}


@router.post("/priority")
async def update_priority(req: PriorityUpdateRequest):
    """Reorder the fallback priority index in DB and reload."""
    await ai_manager.initialize()
    
    async with async_session_maker() as session:
        repo = AIProviderRepository(session)
        for idx, key in enumerate(req.priority):
            await repo.update_priority(key, idx)
        await session.commit()
        
    await ai_manager.reload_config()
    return {"status": "success", "priority": req.priority}


@router.get("/routing")
async def get_routing_rules():
    """Retrieve document routing configurations."""
    async with async_session_maker() as session:
        repo = AIProviderRepository(session)
        rules = await repo.get_all_routing_rules()
        
    return [
        {
            "document_type": r.document_type,
            "provider_keys": r.provider_keys
        }
        for r in rules
    ]


@router.post("/routing")
async def update_routing_rule(req: RoutingUpdateRequest):
    """Create or update a routing rule for a document type."""
    async with async_session_maker() as session:
        repo = AIProviderRepository(session)
        rule = await repo.get_routing_rule_by_doc_type(req.document_type)
        if rule:
            rule.provider_keys = req.provider_keys
        else:
            rule = AIProviderRoutingRule(
                document_type=req.document_type,
                provider_keys=req.provider_keys
            )
            repo.add_routing_rule(rule)
        await session.commit()
        
    return {"status": "success", "document_type": req.document_type, "provider_keys": req.provider_keys}


@router.get("/{key}/models")
async def get_models(key: str):
    """Refresh and return available models from the endpoint."""
    await ai_manager.initialize()
    provider = ai_manager.providers.get(key)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {key} not found")
        
    import httpx
    try:
        timeout_cfg = httpx.Timeout(10.0, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            headers = {}
            if provider.api_key:
                headers["Authorization"] = f"Bearer {provider.api_key}"
            
            response = await client.get(f"{provider.api_url}/models", headers=headers)
            response.raise_for_status()
            models_data = response.json()
            
            # Extract capabilities details if returning OpenAI-compatible JSON list
            # Usually models endpoint returns list, we can update DB if needed.
            return models_data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch models: {str(e)}")
