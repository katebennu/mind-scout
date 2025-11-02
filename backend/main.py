"""FastAPI backend for Mind Scout web interface."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import articles, recommendations, profile, search

app = FastAPI(
    title="Mind Scout API",
    description="AI-powered research paper recommendation system",
    version="0.6.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


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
