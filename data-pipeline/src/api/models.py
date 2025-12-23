"""
Pydantic models for News RAG API request/response.

Matches the specification in docs/API_NEWS_RAG.md
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================


class Sentiment(str, Enum):
    """Sentiment classification."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


# =============================================================================
# Request Models
# =============================================================================


class Holding(BaseModel):
    """Portfolio holding information."""

    symbol: str = Field(..., description="Stock symbol (e.g., '005930.KS', 'BTC-KRW')")
    name: str = Field(..., description="Stock name (e.g., '삼성전자', '비트코인')")
    weight: float = Field(..., ge=0, le=1, description="Portfolio weight (0-1)")


class PortfolioContext(BaseModel):
    """Portfolio context for personalized search."""

    holdings: Optional[List[Holding]] = Field(
        default=None, description="List of holdings"
    )
    sectors: Optional[List[str]] = Field(default=None, description="Related sectors")
    totalValue: Optional[float] = Field(
        default=None, description="Total portfolio value (KRW)"
    )


class Filters(BaseModel):
    """Search filters."""

    startDate: Optional[str] = Field(
        default=None, description="Start date (YYYY-MM-DD)"
    )
    endDate: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    minRelevance: Optional[float] = Field(
        default=0.7, ge=0, le=1, description="Minimum relevance score"
    )


class NewsSearchRequest(BaseModel):
    """Request body for POST /api/news/search."""

    query: str = Field(..., min_length=1, description="Search keyword")
    portfolioContext: Optional[PortfolioContext] = Field(default=None)
    filters: Optional[Filters] = Field(default=None)
    topK: int = Field(default=5, ge=1, le=20, description="Number of results (max 20)")


# =============================================================================
# Response Models
# =============================================================================


class NewsArticle(BaseModel):
    """Individual news article in response."""

    newsId: int = Field(..., description="Milvus news ID")
    title: str = Field(..., description="News title")
    summary: str = Field(..., description="News summary or chunked text")
    publishedAt: str = Field(..., description="Published date (YYYY-MM-DD HH:mm)")
    url: str = Field(..., description="Original article URL")
    relevanceScore: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    sentiment: Sentiment = Field(..., description="Sentiment classification")


class SentimentDistribution(BaseModel):
    """Sentiment distribution across articles."""

    positive: float = Field(..., ge=0, le=1)
    negative: float = Field(..., ge=0, le=1)
    neutral: float = Field(..., ge=0, le=1)


class RecommendedStock(BaseModel):
    """Recommended stock based on news analysis."""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    reason: str = Field(..., description="Recommendation reason")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")


class Analysis(BaseModel):
    """LLM-based news analysis."""

    overallSentiment: Sentiment = Field(..., description="Overall sentiment")
    sentimentDistribution: SentimentDistribution
    keyTopics: List[str] = Field(
        default_factory=list, description="Key topics extracted"
    )
    riskFactors: List[str] = Field(
        default_factory=list, description="Investment risk factors"
    )
    opportunities: List[str] = Field(
        default_factory=list, description="Investment opportunities"
    )
    recommendedStocks: List[RecommendedStock] = Field(default_factory=list)


class Metadata(BaseModel):
    """Response metadata."""

    totalMatches: int = Field(..., description="Total Milvus matches")
    returnedCount: int = Field(..., description="Returned article count")
    searchTimeMs: int = Field(..., description="Search time in milliseconds")


class NewsSearchResponse(BaseModel):
    """Response body for POST /api/news/search."""

    query: str
    newsArticles: List[NewsArticle]
    analysis: Analysis
    metadata: Metadata


# =============================================================================
# Error Models
# =============================================================================


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="ISO timestamp")
