"""FastAPI backend for Mind Scout web interface."""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.api import (
    articles,
    fetchers,
    notifications,
    profile,
    recommendations,
    search,
    subscriptions,
)
from backend.scheduler import shutdown_scheduler, start_scheduler
from mindscout.config import get_settings

# Load .env file for ANTHROPIC_API_KEY and other non-prefixed vars
load_dotenv()
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Initialize Phoenix tracing
    from mindscout.observability import init_phoenix

    init_phoenix()

    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="Mind Scout API",
    description="AI-powered research paper recommendation system",
    version="0.6.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(fetchers.router, prefix="/api/fetch", tags=["fetchers"])


@app.get("/")
def root():
    """Root endpoint."""
    return {"name": "Mind Scout API", "version": "0.6.0", "docs": "/docs"}


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
