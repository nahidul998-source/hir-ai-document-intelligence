import time
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Create a custom registry to avoid pollution of the global default registry
registry = CollectorRegistry()

# HTTP Metrics
http_requests_total = Counter(
    "hir_http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status"],
    registry=registry
)

http_request_duration_seconds = Histogram(
    "hir_http_request_duration_seconds",
    "HTTP request execution latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

# Business Logic / Worker Metrics
document_processing_duration_seconds = Histogram(
    "hir_document_processing_duration_seconds",
    "Time taken to process documents by the AI pipeline",
    ["status"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=registry
)

jobs_total = Counter(
    "hir_jobs_total",
    "Total number of system jobs",
    ["status", "job_type"],
    registry=registry
)

ai_provider_requests_total = Counter(
    "hir_ai_provider_requests_total",
    "Total AI generation requests sent to providers",
    ["provider", "status"],
    registry=registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking HTTP request count and latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Ignore metrics endpoints to prevent feedback loops
        if "/metrics" in request.url.path or "/health" in request.url.path:
            return await call_next(request)

        method = request.method
        endpoint = request.url.path
        
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.perf_counter() - start_time
            http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def get_prometheus_metrics() -> tuple[bytes, str]:
    """Generates the latest text representation of Prometheus metrics."""
    return generate_latest(registry), CONTENT_TYPE_LATEST
