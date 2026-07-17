import logging
import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_telemetry(app: FastAPI) -> None:
    """Sets up OpenTelemetry tracing for the FastAPI application."""
    try:
        # Define service details
        resource = Resource.create({
            "service.name": "hir-backend-service",
            "service.environment": settings.APP_ENV,
        })
        
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Detect OTLP Endpoint
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", None)

        if otlp_endpoint:
            logger.info(f"OpenTelemetry: Configuring OTLP exporter to {otlp_endpoint}")
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        else:
            # Fall back to console span exporter in development or debug modes
            logger.info("OpenTelemetry: OTLP endpoint not configured. Configuring ConsoleSpanExporter.")
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))

        # Instrument FastAPI app
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        logger.info("OpenTelemetry: FastAPI application successfully instrumented.")

    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry tracing: {e}. Running without tracing.")
