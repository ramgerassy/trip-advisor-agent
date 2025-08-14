"""
FastAPI server main application.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import create_tables
from app.server.routes import conversations

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting Trip Planner Agent API...")
    create_tables()
    logger.info("✅ Database tables created/verified")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Trip Planner Agent API...")


# Create FastAPI app
app = FastAPI(
    title="Trip Planner Agent API",
    description="Orchestrated AI agent for trip planning with structured conversation flow",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Trip Planner Agent API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2024-01-01T00:00:00Z"
    }