"""
News RAG Pipeline - orchestrates search, embedding, and analysis.
"""

from typing import List
from loguru import logger

from ..api.models import (
    NewsSearchRequest,
    NewsSearchResponse,
    NewsArticle,
    Analysis,
    SentimentDistribution,
    Metadata,
    Sentiment,
)
from ..storage import MilvusClient
from ..embeddings import KoSRoBERTaEmbedding
from .analyzer import NewsAnalyzer


class NewsRAGPipeline:
    """
    Main RAG pipeline for news search and analysis.

    Orchestrates:
    1. Query embedding generation
    2. Milvus vector search with optional date filtering
    3. LLM-based sentiment and topic analysis
    4. Stock recommendation generation
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.embedder = KoSRoBERTaEmbedding()
        self.storage = MilvusClient()
        self.analyzer = NewsAnalyzer()

        logger.info("NewsRAGPipeline initialized")

    async def search(self, request: NewsSearchRequest) -> NewsSearchResponse:
        """
        Execute the full RAG pipeline.

        Args:
            request: Search request with query, portfolio context, filters

        Returns:
            NewsSearchResponse with articles, analysis, and metadata
        """
        logger.info(f"Starting search for query: '{request.query}'")

        # Step 1: Generate query embedding
        query_embedding = self.embedder.embed(request.query)[0].tolist()

        # Step 2: Search Milvus with optional portfolio boosting
        search_query = self._build_search_query(request)

        # Use hybrid search if portfolio context is provided
        if request.portfolioContext and request.portfolioContext.holdings:
            raw_results = self.storage.hybrid_search(
                query=search_query,
                query_embedding=query_embedding,
                top_k=request.topK,
            )
        else:
            raw_results = self.storage.search(
                query_embedding=query_embedding,
                top_k=request.topK,
            )

        # Step 3: Filter by date if specified
        if request.filters:
            raw_results = self._apply_date_filter(raw_results, request.filters)

        # Step 4: Filter by minimum relevance
        min_relevance = 0.7
        if request.filters and request.filters.minRelevance:
            min_relevance = request.filters.minRelevance

        raw_results = [r for r in raw_results if r.get("score", 0) >= min_relevance]

        # Step 5: Analyze sentiment for each article
        articles: List[NewsArticle] = []
        texts = []
        titles = []

        for result in raw_results:
            text = result.get("original_text", "")
            title = result.get("title", "")

            texts.append(text)
            titles.append(title)

            sentiment = await self.analyzer.analyze_sentiment(text)

            articles.append(
                NewsArticle(
                    newsId=result.get("id", 0),
                    title=title,
                    summary=text[:500] if len(text) > 500 else text,
                    publishedAt=result.get("published_at", ""),
                    url=result.get("url", ""),
                    relevanceScore=round(result.get("score", 0), 4),
                    sentiment=sentiment,
                )
            )

        # Step 6: Calculate sentiment distribution
        sentiment_dist = self._calculate_sentiment_distribution(articles)
        overall_sentiment = self._get_overall_sentiment(sentiment_dist)

        # Step 7: Batch analysis for topics, risks, opportunities, recommendations
        batch_analysis = await self.analyzer.analyze_batch(
            texts=texts,
            titles=titles,
            portfolio_context=request.portfolioContext,
        )

        # Build analysis object
        analysis = Analysis(
            overallSentiment=overall_sentiment,
            sentimentDistribution=sentiment_dist,
            keyTopics=batch_analysis.get("keyTopics", []),
            riskFactors=batch_analysis.get("riskFactors", []),
            opportunities=batch_analysis.get("opportunities", []),
            recommendedStocks=batch_analysis.get("recommendedStocks", []),
        )

        # Build metadata
        metadata = Metadata(
            totalMatches=len(raw_results),
            returnedCount=len(articles),
            searchTimeMs=0,  # Will be set by router
        )

        return NewsSearchResponse(
            query=request.query,
            newsArticles=articles,
            analysis=analysis,
            metadata=metadata,
        )

    def _build_search_query(self, request: NewsSearchRequest) -> str:
        """Build enhanced search query including portfolio context."""
        query_parts = [request.query]

        if request.portfolioContext:
            if request.portfolioContext.holdings:
                for holding in request.portfolioContext.holdings[:3]:
                    query_parts.append(holding.name)

            if request.portfolioContext.sectors:
                query_parts.extend(request.portfolioContext.sectors[:2])

        return " ".join(query_parts)

    def _apply_date_filter(self, results: List[dict], filters) -> List[dict]:
        """Filter results by date range."""
        if not filters.startDate and not filters.endDate:
            return results

        filtered = []
        for result in results:
            pub_date = result.get("published_at", "")[:10]  # Extract YYYY-MM-DD

            if filters.startDate and pub_date < filters.startDate:
                continue
            if filters.endDate and pub_date > filters.endDate:
                continue

            filtered.append(result)

        return filtered

    def _calculate_sentiment_distribution(
        self, articles: List[NewsArticle]
    ) -> SentimentDistribution:
        """Calculate sentiment distribution from articles."""
        if not articles:
            return SentimentDistribution(positive=0.33, negative=0.33, neutral=0.34)

        counts = {Sentiment.POSITIVE: 0, Sentiment.NEGATIVE: 0, Sentiment.NEUTRAL: 0}
        for article in articles:
            counts[article.sentiment] += 1

        total = len(articles)
        return SentimentDistribution(
            positive=round(counts[Sentiment.POSITIVE] / total, 2),
            negative=round(counts[Sentiment.NEGATIVE] / total, 2),
            neutral=round(counts[Sentiment.NEUTRAL] / total, 2),
        )

    def _get_overall_sentiment(self, distribution: SentimentDistribution) -> Sentiment:
        """Determine overall sentiment from distribution."""
        max_val = max(
            distribution.positive, distribution.negative, distribution.neutral
        )

        if max_val == distribution.positive:
            return Sentiment.POSITIVE
        elif max_val == distribution.negative:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL
