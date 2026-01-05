"""
FastAPI main application for Vegetation Change Intelligence Platform.

Run with:
    uvicorn app.api.main:app --reload

Or:
    python -m app.api.main
"""

from contextlib import asynccontextmanager
from typing import Optional
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import __version__
from app.api.models.responses import HealthResponse, ErrorResponse
from app.api.routes.analysis import router as analysis_router
from app.api.routes.metadata import router as metadata_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track EE initialization status
_ee_initialized: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    Initializes Earth Engine on startup.
    """
    global _ee_initialized

    # Startup
    logger.info("Initializing Earth Engine...")
    try:
        from engine.ee_init import initialize_ee, is_ee_initialized

        if not is_ee_initialized():
            initialize_ee()

        _ee_initialized = is_ee_initialized()
        if _ee_initialized:
            logger.info("Earth Engine initialized successfully")
        else:
            logger.warning("Earth Engine initialization may have failed")

    except Exception as e:
        logger.error(f"Failed to initialize Earth Engine: {e}")
        _ee_initialized = False

    yield

    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="Vegetation Change Intelligence Platform API",
    description="""
    REST API for satellite-based vegetation change detection.

    ## Features
    - Multi-decadal vegetation change analysis (1985-present)
    - Multiple spectral indices (NDVI, NBR, NDWI, EVI, NDMI)
    - Multi-sensor fusion (Landsat 5/7/8, Sentinel-2)
    - Async job processing with progress tracking
    - Preview tile URL generation

    ## Quick Start
    1. Create an analysis job with `POST /analysis`
    2. Monitor progress with `GET /analysis/{job_id}`
    3. Retrieve results when completed

    ## Authentication
    This API requires Earth Engine credentials configured on the server.
    """,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="ValidationError",
            message=str(exc),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.exception("Unexpected error")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalError",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__},
        ).model_dump(),
    )


# Include routers
app.include_router(analysis_router)
app.include_router(metadata_router)


# Root endpoints
@app.get(
    "/",
    summary="API Root",
    description="Basic API information and links.",
)
async def root():
    """API root endpoint."""
    return {
        "name": "Vegetation Change Intelligence Platform API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health and Earth Engine status.",
)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if _ee_initialized else "degraded",
        version=__version__,
        earth_engine=_ee_initialized,
    )


# Run directly with python -m app.api.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
