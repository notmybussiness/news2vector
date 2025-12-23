"""
FastAPI application entry point for News RAG API.

Usage:
    python -m src.api.server
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

from .router import router
from ..config import settings


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting News RAG API server...")
    yield
    logger.info("Shutting down News RAG API server...")


# Create FastAPI application
app = FastAPI(
    title="News RAG API",
    description="Portfolio-based news search with sentiment analysis and stock recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "news-rag-api"}


def main():
    """Run the server."""
    port = int(os.getenv("RAG_API_PORT", "8000"))
    host = os.getenv("RAG_API_HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
