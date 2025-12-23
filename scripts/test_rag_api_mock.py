"""
Test script to run News RAG API with mock data.

Usage:
    cd /Users/gyu/Desktop/프로젝트/news2vector/data-pipeline
    source venv/bin/activate
    python ../scripts/test_rag_api_mock.py
"""

import asyncio
import json
from datetime import datetime

# Add parent to path
import sys

sys.path.insert(0, ".")

from src.api.models import (
    NewsSearchRequest,
    PortfolioContext,
    Holding,
    Filters,
    Sentiment,
)
from src.rag.analyzer import NewsAnalyzer


# Mock data for Milvus results
MOCK_NEWS_DATA = [
    {
        "id": 12345,
        "title": "삼성전자, 차세대 3nm 공정 양산 시작",
        "original_text": "삼성전자가 3나노미터 공정을 활용한 차세대 반도체 양산을 시작했다. 업계 전문가들은 이번 3nm 공정이 기존 5nm 대비 성능은 23% 향상되고 전력 소비는 45% 감소할 것으로 전망하고 있다.",
        "published_at": "2025-12-20 10:30",
        "url": "https://news.naver.com/example1",
        "score": 0.92,
    },
    {
        "id": 12346,
        "title": "반도체 수출 3개월 연속 증가, AI 칩 수요 급증",
        "original_text": "한국 반도체 수출이 3개월 연속 증가하며 회복세를 보이고 있다. 특히 AI 서버용 고성능 칩 수요가 급증하면서 삼성전자와 SK하이닉스의 수주량이 전년 대비 40% 증가했다.",
        "published_at": "2025-12-19 14:20",
        "url": "https://news.naver.com/example2",
        "score": 0.85,
    },
    {
        "id": 12347,
        "title": "미중 반도체 갈등 심화, 한국 기업 리스크 증가",
        "original_text": "미국과 중국의 반도체 패권 경쟁이 격화되면서 한국 반도체 기업들이 양국 사이에서 선택의 기로에 놓였다. 전문가들은 지정학적 리스크가 단기 실적에 악영향을 미칠 수 있다고 경고했다.",
        "published_at": "2025-12-18 09:15",
        "url": "https://news.naver.com/example3",
        "score": 0.78,
    },
]


async def test_mock_analysis():
    """Test the analyzer with mock data."""
    print("=" * 60)
    print("Testing News RAG API with Mock Data")
    print("=" * 60)

    # Create mock request
    request = NewsSearchRequest(
        query="삼성전자 반도체 최신 동향",
        portfolioContext=PortfolioContext(
            holdings=[
                Holding(symbol="005930.KS", name="삼성전자", weight=0.3),
                Holding(symbol="000660.KS", name="SK하이닉스", weight=0.2),
            ],
            sectors=["반도체", "IT"],
            totalValue=10000000,
        ),
        filters=Filters(
            startDate="2025-12-01",
            endDate="2025-12-22",
            minRelevance=0.7,
        ),
        topK=5,
    )

    print(f"\n📥 Request:")
    print(f"  Query: {request.query}")
    print(f"  TopK: {request.topK}")
    print(f"  Holdings: {[h.name for h in request.portfolioContext.holdings]}")

    # Initialize analyzer
    analyzer = NewsAnalyzer()

    # Analyze sentiment for each article
    print("\n🔍 Analyzing sentiment...")
    articles = []
    for news in MOCK_NEWS_DATA:
        sentiment = await analyzer.analyze_sentiment(news["original_text"])
        articles.append(
            {
                **news,
                "sentiment": sentiment.value,
            }
        )
        print(f"  - {news['title'][:30]}... → {sentiment.value}")

    # Batch analysis
    print("\n📊 Batch Analysis...")
    texts = [n["original_text"] for n in MOCK_NEWS_DATA]
    titles = [n["title"] for n in MOCK_NEWS_DATA]

    batch_result = await analyzer.analyze_batch(
        texts=texts,
        titles=titles,
        portfolio_context=request.portfolioContext,
    )

    # Build response
    response = {
        "query": request.query,
        "newsArticles": [
            {
                "newsId": a["id"],
                "title": a["title"],
                "summary": a["original_text"][:200] + "...",
                "publishedAt": a["published_at"],
                "url": a["url"],
                "relevanceScore": a["score"],
                "sentiment": a["sentiment"],
            }
            for a in articles
        ],
        "analysis": {
            "overallSentiment": "POSITIVE",
            "sentimentDistribution": {
                "positive": 0.67,
                "negative": 0.20,
                "neutral": 0.13,
            },
            "keyTopics": batch_result.get("keyTopics", []),
            "riskFactors": batch_result.get("riskFactors", []),
            "opportunities": batch_result.get("opportunities", []),
            "recommendedStocks": [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "reason": s.reason,
                    "confidence": s.confidence,
                }
                for s in batch_result.get("recommendedStocks", [])
            ],
        },
        "metadata": {
            "totalMatches": len(MOCK_NEWS_DATA),
            "returnedCount": len(articles),
            "searchTimeMs": 120,
        },
    }

    print("\n" + "=" * 60)
    print("📤 Response:")
    print("=" * 60)
    print(json.dumps(response, ensure_ascii=False, indent=2))

    return response


if __name__ == "__main__":
    asyncio.run(test_mock_analysis())
