import time
import logging
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import redis.asyncio as aioredis
import aio_pika
from datetime import datetime

from app.core.config import settings
from app.api.deps import get_db, get_current_user, get_event_publisher
from app.infrastructure.database.models import User, AuditLog, Job
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from app.infrastructure.monitoring.metrics import get_prometheus_metrics
from app.infrastructure.monitoring.alerting import EventDrivenAlertingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring")
ai_provider_manager = AIProviderManager()


async def get_worker_status() -> dict:
    """Checks worker heartbeat keys in Redis."""
    try:
        client = aioredis.from_url(settings.REDIS_URL)
        ai_hb = await client.get("worker:heartbeat:ai_worker")
        erp_hb = await client.get("worker:heartbeat:erp_worker")
        await client.close()
        
        now = datetime.utcnow()
        
        def evaluate(hb_bytes):
            if not hb_bytes:
                return "unhealthy", None
            try:
                hb_str = hb_bytes.decode("utf-8")
                hb_dt = datetime.fromisoformat(hb_str)
                delta = (now - hb_dt).total_seconds()
                # If heartbeat is within last 30s, mark as healthy
                if delta < 30:
                    return "healthy", hb_str
                return "unhealthy", hb_str
            except Exception:
                return "unhealthy", None

        ai_status, ai_time = evaluate(ai_hb)
        erp_status, erp_time = evaluate(erp_hb)
        
        return {
            "ai_worker": {"status": ai_status, "last_heartbeat": ai_time},
            "erp_worker": {"status": erp_status, "last_heartbeat": erp_time}
        }
    except Exception as e:
        logger.warning(f"Error checking worker heartbeats: {e}")
        return {
            "ai_worker": {"status": "unhealthy", "error": str(e)},
            "erp_worker": {"status": "unhealthy", "error": str(e)}
        }


@router.get("/health", tags=["Monitoring"])
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    publisher = Depends(get_event_publisher),
    current_user: User = Depends(get_current_user)
):
    """
    Detailed health check API evaluating Postgres, Redis, RabbitMQ, MinIO,
    AI Providers, and AI/ERP microservice workers.
    """
    alert_service = EventDrivenAlertingService(publisher)
    services = {}
    overall_status = "healthy"
    
    # 1. PostgreSQL Health
    db_start = time.perf_counter()
    try:
        await db.execute(select(1))
        db_latency = (time.perf_counter() - db_start) * 1000
        services["postgresql"] = {"status": "healthy", "latency_ms": round(db_latency, 2)}
    except Exception as e:
        db_latency = (time.perf_counter() - db_start) * 1000
        services["postgresql"] = {"status": "unhealthy", "latency_ms": round(db_latency, 2), "error": str(e)}
        overall_status = "unhealthy"
        await alert_service.trigger_alert("CRITICAL", "postgresql", f"Database connection failed: {e}")

    # 2. Redis Health
    redis_start = time.perf_counter()
    try:
        client = aioredis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        redis_latency = (time.perf_counter() - redis_start) * 1000
        services["redis"] = {"status": "healthy", "latency_ms": round(redis_latency, 2)}
    except Exception as e:
        redis_latency = (time.perf_counter() - redis_start) * 1000
        services["redis"] = {"status": "unhealthy", "latency_ms": round(redis_latency, 2), "error": str(e)}
        overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        await alert_service.trigger_alert("WARNING", "redis", f"Redis ping failed: {e}")

    # 3. RabbitMQ Health
    rabbitmq_start = time.perf_counter()
    try:
        conn = await aio_pika.connect(settings.RABBITMQ_URL)
        await conn.close()
        rabbitmq_latency = (time.perf_counter() - rabbitmq_start) * 1000
        services["rabbitmq"] = {"status": "healthy", "latency_ms": round(rabbitmq_latency, 2)}
    except Exception as e:
        rabbitmq_latency = (time.perf_counter() - rabbitmq_start) * 1000
        services["rabbitmq"] = {"status": "unhealthy", "latency_ms": round(rabbitmq_latency, 2), "error": str(e)}
        overall_status = "unhealthy"
        await alert_service.trigger_alert("CRITICAL", "rabbitmq", f"RabbitMQ connection failed: {e}")

    # 4. MinIO Health
    minio_start = time.perf_counter()
    try:
        from app.api.deps import _storage_adapter
        def _check():
            return _storage_adapter.client.bucket_exists(settings.MINIO_BUCKET_NAME)
        # execute checking in thread pool
        await asyncio.to_thread(_check)
        minio_latency = (time.perf_counter() - minio_start) * 1000
        services["minio"] = {"status": "healthy", "latency_ms": round(minio_latency, 2)}
    except Exception as e:
        minio_latency = (time.perf_counter() - minio_start) * 1000
        services["minio"] = {"status": "unhealthy", "latency_ms": round(minio_latency, 2), "error": str(e)}
        overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        await alert_service.trigger_alert("WARNING", "minio", f"MinIO bucket check failed: {e}")

    # 5. AI Providers Health
    provider_results = {}
    provider_healthy_count = 0
    for key, provider in ai_provider_manager.providers.items():
        try:
            is_provider_healthy = await provider.is_healthy()
            provider_results[key] = {"status": "healthy" if is_provider_healthy else "unhealthy"}
            if is_provider_healthy:
                provider_healthy_count += 1
        except Exception:
            provider_results[key] = {"status": "unhealthy"}
            
    services["ai_providers"] = {
        "status": "healthy" if provider_healthy_count > 0 else "unhealthy",
        "providers": provider_results
    }
    if provider_healthy_count == 0:
        overall_status = "unhealthy"
        await alert_service.trigger_alert("CRITICAL", "ai_providers", "All configured AI Providers are offline.")
    elif provider_healthy_count < len(ai_provider_manager.providers):
        if overall_status == "healthy":
            overall_status = "degraded"

    # 6. AI & ERP Worker Health
    worker_hb = await get_worker_status()
    services["workers"] = worker_hb
    if worker_hb["ai_worker"]["status"] == "unhealthy" or worker_hb["erp_worker"]["status"] == "unhealthy":
        if overall_status == "healthy":
            overall_status = "degraded"
        await alert_service.trigger_alert("WARNING", "workers", "One or more standalone microservice workers are offline.")

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }


@router.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
async def metrics():
    """Exposes Prometheus-ready raw text metrics."""
    metrics_data, content_type = get_prometheus_metrics()
    return PlainTextResponse(metrics_data, media_type=content_type)


@router.get("/audit-logs", tags=["Monitoring"])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves paginated structured audit logs for dashboard view."""
    query = select(AuditLog)
    if action:
        query = query.where(func.lower(AuditLog.action) == action.lower())
    
    # Sort by created_at desc
    query = query.order_by(desc(AuditLog.created_at))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0
    
    # Get results
    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()
    
    return {
        "total": total,
        "logs": [
            {
                "id": str(log.id),
                "created_at": log.created_at.isoformat(),
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "details": log.details,
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    }


@router.get("/jobs", tags=["Monitoring"])
async def get_jobs_statistics(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves job processing counts grouped by status and a list of recent jobs."""
    # Count by status
    count_query = select(Job.status, func.count(Job.id)).group_by(Job.status)
    count_res = await db.execute(count_query)
    status_counts = {row[0]: row[1] for row in count_res.all()}
    
    # Fill in defaults if not present
    for status_key in ("queued", "processing", "completed", "failed"):
        if status_key not in status_counts:
            status_counts[status_key] = 0
            
    # Recent jobs
    recent_query = select(Job).order_by(desc(Job.created_at)).limit(limit)
    recent_res = await db.execute(recent_query)
    recent_jobs = recent_res.scalars().all()
    
    return {
        "summary": status_counts,
        "recent_jobs": [
            {
                "id": str(job.id),
                "document_id": str(job.document_id),
                "job_type": job.job_type,
                "status": job.status,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in recent_jobs
        ]
    }


@router.get("/queues", tags=["Monitoring"])
async def get_queues_monitoring(
    current_user: User = Depends(get_current_user)
):
    """Checks lengths and active consumers directly from RabbitMQ using passive queue declarations."""
    try:
        conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await conn.channel()
        
        target_queues = [
            "hir.ai_worker.processing",
            "hir.ai_worker.dlq",
            "hir.erp_worker.processing",
            "hir.erp_worker.dlq"
        ]
        
        queue_stats = {}
        for qname in target_queues:
            try:
                # Declare passively to extract existing metadata without altering queue state
                q = await channel.declare_queue(qname, passive=True)
                queue_stats[qname] = {
                    "message_count": q.declaration_result.message_count,
                    "consumer_count": q.declaration_result.consumer_count,
                    "status": "active" if q.declaration_result.consumer_count > 0 or not qname.endswith("processing") else "idle"
                }
            except Exception as e:
                # Queue does not exist yet (not declared by workers yet)
                queue_stats[qname] = {
                    "message_count": 0,
                    "consumer_count": 0,
                    "status": "not_declared",
                    "error": str(e)
                }
                # Reopen channel if passive declaration closed it on error
                if channel.is_closed:
                    channel = await conn.channel()
                    
        await conn.close()
        return queue_stats
    except Exception as e:
        logger.warning(f"Error checking RabbitMQ queues: {e}")
        return {
            "error": str(e),
            "status": "unavailable"
        }
