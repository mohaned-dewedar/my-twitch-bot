"""FastAPI web dashboard main application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path

from db.database import Database
from web.routers import overlay, api
from web.models.leaderboard import ErrorResponse
from config import DATABASE_URL

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the web directory path
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting CherryBott Web Dashboard...")
    try:
        # Initialize database connection
        await Database.init(DATABASE_URL)
        logger.info("Database connection initialized")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down CherryBott Web Dashboard...")


# Create FastAPI app
app = FastAPI(
    title="CherryBott Web Dashboard",
    description="Real-time leaderboard overlay system for Twitch streaming",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(overlay.router, prefix="/overlay", tags=["overlay"])
app.include_router(api.router, prefix="/api", tags=["api"])


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Resource not found",
            detail=f"The requested path '{request.url.path}' was not found"
        ).model_dump(mode='json')
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors with custom response."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred"
        ).model_dump(mode='json')
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CherryBott Web Dashboard",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": "CherryBott Web Dashboard",
        "overlay_url": "/overlay/{channel_name}",
        "api_url": "/api/leaderboard/{channel_name}",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )