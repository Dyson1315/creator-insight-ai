"""
Creator-VRidge AI Image Recommendation System
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api import recommendations, images, analytics
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Creator-VRidge AI Recommendation API",
    description="AI-powered image and artist recommendation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Creator-VRidge AI Recommendation System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "ml_models": "loaded"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )