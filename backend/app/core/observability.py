import logging
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace

logger = logging.getLogger(__name__)

def setup_observability(app: FastAPI):
    """
    Integrates OpenTelemetry for distributed tracing, metrics, and centralized logging.
    """
    # In a real environment, you configure the OTLP exporter here.
    # We are simulating the instrumentation setup.
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry instrumentation successfully attached to FastAPI.")
    except Exception as e:
        logger.warning(f"Could not setup OpenTelemetry: {e}")

def get_tracer(name: str):
    return trace.get_tracer(name)
