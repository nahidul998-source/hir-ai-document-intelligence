from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["Health & Readiness"])

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic liveness probe for Kubernetes.
    """
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Deep readiness probe checking database, Redis, and message queues.
    """
    # Placeholder: execute actual ping commands against dependencies
    dependencies = {
        "database": "ok",
        "redis": "ok",
        "rabbitmq": "ok"
    }
    
    is_ready = all(status == "ok" for status in dependencies.values())
    if not is_ready:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=dependencies)
        
    return {"status": "ready", "dependencies": dependencies}
