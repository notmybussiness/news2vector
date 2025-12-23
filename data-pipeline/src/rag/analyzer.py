"""
LLM-based news analyzer for sentiment, topics, and recommendations.

Uses Google Gemini API for analysis.
"""

import os
import json
from typing import List, Optional
from loguru import logger

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed, using mock analyzer")

from ..api.models import Sentiment, RecommendedStock, PortfolioContext


class NewsAnalyzer:
    """LLM-based news analyzer."""

    def __init__(self):
        """Initialize the analyzer with Gemini API."""
        self.model = None

        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
                logger.info("Gemini model initialized")
            else:
                logger.warning("GEMINI_API_KEY not set, using mock analyzer")

    async def analyze_sentiment(self, text: str) -> Sentiment:
        """
        Analyze sentiment of a single text.

        Args:
            text: News text to analyze

        Returns:
            Sentiment enum (POSITIVE, NEGATIVE, NEUTRAL)
        """
        if not self.model:
            return self._mock_sentiment(text)

        try:
            prompt = f"""다음 뉴스 텍스트의 감성을 분석해주세요.
반드시 POSITIVE, NEGATIVE, NEUTRAL 중 하나만 답변하세요.

텍스트: {text[:500]}

감성:"""

            response = self.model.generate_content(prompt)
            result = response.text.strip().upper()

            if "POSITIVE" in result:
                return Sentiment.POSITIVE
            elif "NEGATIVE" in result:
                return Sentiment.NEGATIVE
            else:
                return Sentiment.NEUTRAL

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._mock_sentiment(text)

    async def analyze_batch(
        self,
        texts: List[str],
        titles: List[str],
        portfolio_context: Optional[PortfolioContext] = None,
    ) -> dict:
        """
        Analyze multiple news articles in batch.

        Args:
            texts: List of news texts
            titles: List of news titles
            portfolio_context: Optional portfolio context

        Returns:
            dict with keyTopics, riskFactors, opportunities, recommendedStocks
        """
        if not self.model:
            return self._mock_batch_analysis(texts, titles, portfolio_context)

        try:
            # Build context string
            context_str = ""
            if portfolio_context and portfolio_context.holdings:
                holdings_str = ", ".join([h.name for h in portfolio_context.holdings])
                context_str = f"\n사용자 보유 종목: {holdings_str}"
                if portfolio_context.sectors:
                    context_str += (
                        f"\n관심 섹터: {', '.join(portfolio_context.sectors)}"
                    )

            # Combine titles and texts for analysis
            news_content = "\n\n".join(
                [
                    f"제목: {title}\n내용: {text[:300]}"
                    for title, text in zip(titles[:5], texts[:5])  # Limit to 5 articles
                ]
            )

            prompt = f"""다음 뉴스들을 분석해서 JSON 형식으로 응답해주세요.
{context_str}

뉴스:
{news_content}

다음 형식으로 JSON만 반환하세요 (다른 텍스트 없이):
{{
    "keyTopics": ["핵심 키워드1", "핵심 키워드2", "핵심 키워드3"],
    "riskFactors": ["리스크 요인1", "리스크 요인2"],
    "opportunities": ["기회 요인1", "기회 요인2"],
    "recommendedStocks": [
        {{"symbol": "종목코드", "name": "종목명", "reason": "추천 이유", "confidence": 0.8}}
    ]
}}"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            result = json.loads(result_text)

            # Convert recommendedStocks to proper format
            recommended = []
            for stock in result.get("recommendedStocks", []):
                recommended.append(
                    RecommendedStock(
                        symbol=stock.get("symbol", ""),
                        name=stock.get("name", ""),
                        reason=stock.get("reason", ""),
                        confidence=float(stock.get("confidence", 0.7)),
                    )
                )

            return {
                "keyTopics": result.get("keyTopics", []),
                "riskFactors": result.get("riskFactors", []),
                "opportunities": result.get("opportunities", []),
                "recommendedStocks": recommended,
            }

        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return self._mock_batch_analysis(texts, titles, portfolio_context)

    def _mock_sentiment(self, text: str) -> Sentiment:
        """Mock sentiment analysis based on keywords."""
        text_lower = text.lower()

        positive_keywords = ["상승", "증가", "성장", "호재", "급등", "돌파", "성공"]
        negative_keywords = ["하락", "감소", "위험", "악재", "급락", "실패", "우려"]

        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)

        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def _mock_batch_analysis(
        self,
        texts: List[str],
        titles: List[str],
        portfolio_context: Optional[PortfolioContext] = None,
    ) -> dict:
        """Mock batch analysis when LLM is unavailable."""
        # Extract keywords from titles
        key_topics = []
        for title in titles[:5]:
            words = title.split()
            key_topics.extend([w for w in words if len(w) > 2][:2])
        key_topics = list(set(key_topics))[:5]

        # Default analysis
        result = {
            "keyTopics": key_topics if key_topics else ["경제", "시장", "투자"],
            "riskFactors": ["시장 변동성 확대", "글로벌 경기 불확실성"],
            "opportunities": ["신규 투자 기회 발굴", "저평가 종목 매수 기회"],
            "recommendedStocks": [],
        }

        # Add recommendations based on portfolio context
        if portfolio_context and portfolio_context.holdings:
            for holding in portfolio_context.holdings[:2]:
                result["recommendedStocks"].append(
                    RecommendedStock(
                        symbol=holding.symbol,
                        name=holding.name,
                        reason=f"포트폴리오 핵심 종목으로 관련 뉴스 다수",
                        confidence=0.75,
                    )
                )

        return result
