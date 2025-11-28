"""FastAPI backend for Mind Scout web interface."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.api import articles, recommendations, profile, search, subscriptions, notifications, fetchers
from mindscout.config import get_settings

settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Mind Scout API",
    description="AI-powered research paper recommendation system",
    version="0.6.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
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
    return {
        "name": "Mind Scout API",
        "version": "0.6.0",
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
