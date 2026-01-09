"""
FastAPI application entry point.

Training Coach API - Backend for AI-powered fitness coaching.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Data directory: {settings.data_dir}")
    yield
    logger.info("Shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
Training Coach API - Backend for AI-powered fitness coaching.

This API provides endpoints for:
- User profile and goal management
- Training plan generation (8-week high-level plans)
- 21-day training block generation
- Just-in-time workout generation
- Pre-workout feedback and workout adjustment
- Workout logging

All endpoints return JSON responses conforming to defined schemas.
""",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Training Coach"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

