from contextlib import asynccontextmanager
import logging
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.deps import _event_publisher
from app.api.routers import auth, projects, documents, monitoring, learning, admin, analytics
from app.infrastructure.monitoring.telemetry import setup_telemetry
from app.infrastructure.monitoring.metrics import PrometheusMiddleware

# Configure structured JSON logging for the application
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # Inject standard telemetry/alert context properties if present
        if hasattr(record, "service"):
            log_data["service"] = record.service
        if hasattr(record, "level") and isinstance(record.level, str):
            log_data["alert_level"] = record.level
        if hasattr(record, "details"):
            log_data["details"] = record.details
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

log_handler = logging.StreamHandler()
log_handler.setFormatter(JSONFormatter())

# Override root logging settings
logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing RabbitMQ Event Publisher...")
    try:
        await _event_publisher.connect()
    except Exception as e:
        logger.warning(f"Could not connect to RabbitMQ broker on startup: {e}. Services running in degraded mode.")

    yield

    # Shutdown actions
    logger.info("Closing RabbitMQ Event Publisher connection...")
    await _event_publisher.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Document Intelligence Platform Backend",
    version="0.1.0",
    lifespan=lifespan
)

# Initialize OpenTelemetry telemetry setup
setup_telemetry(app)

# Inject Prometheus metrics collector middleware
app.add_middleware(PrometheusMiddleware)

# Setup CORS middleware for web frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hook up API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(monitoring.router, prefix=f"{settings.API_V1_STR}", tags=["Monitoring"])
app.include_router(learning.router, prefix=f"{settings.API_V1_STR}", tags=["Continuous Learning Engine"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}", tags=["Enterprise Administration"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}", tags=["Analytics & BI Engine"])


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Simple endpoint to verify server is active."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "env": settings.APP_ENV
    }

