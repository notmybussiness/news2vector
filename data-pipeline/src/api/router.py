"""
FastAPI router for News RAG API.

Implements POST /api/news/search endpoint.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from loguru import logger
import time

from .models import (
    NewsSearchRequest,
    NewsSearchResponse,
    ErrorResponse,
)
from ..rag.pipeline import NewsRAGPipeline


router = APIRouter(prefix="/api/news", tags=["news"])

# Initialize pipeline (singleton)
_pipeline: NewsRAGPipeline = None


def get_pipeline() -> NewsRAGPipeline:
    """Get or create the RAG pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = NewsRAGPipeline()
    return _pipeline


@router.post(
    "/search",
    response_model=NewsSearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    summary="Search news with portfolio context",
    description="Search for portfolio-related news with sentiment analysis and stock recommendations.",
)
async def search_news(request: NewsSearchRequest) -> NewsSearchResponse:
    """
    Search for news articles based on query and portfolio context.

    Returns analyzed news with sentiment, key topics, risks, opportunities,
    and recommended stocks.
    """
    start_time = time.time()

    try:
        logger.info(
            f"Received search request: query='{request.query}', topK={request.topK}"
        )

        pipeline = get_pipeline()
        response = await pipeline.search(request)

        elapsed_ms = int((time.time() - start_time) * 1000)
        response.metadata.searchTimeMs = elapsed_ms

        logger.info(
            f"Search completed in {elapsed_ms}ms, returned {response.metadata.returnedCount} articles"
        )

        return response

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_REQUEST",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
