from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.deps import _event_publisher
from app.api.routers import auth, projects, documents

# Configure structured logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
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


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Simple endpoint to verify server is active."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "env": settings.APP_ENV
    }
