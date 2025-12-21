"""Naver News API collector for fetching Korean economic news."""

import httpx
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings


@dataclass
class NewsItem:
    """Represents a single news article."""

    title: str
    description: str
    url: str
    published_at: str
    source: str

    @property
    def full_text(self) -> str:
        """Combine title and description for embedding."""
        return f"{self.title}\n{self.description}"


class NaverNewsCollector:
    """Collector for Naver News Search API."""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self):
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> dict:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def search(
        self,
        query: str,
        display: int = 100,
        start: int = 1,
        sort: str = "date",  # date: 최신순, sim: 유사도순
    ) -> List[NewsItem]:
        """
        Search news articles via Naver API.

        Args:
            query: Search keyword (ticker name, company name, etc.)
            display: Number of results (max 100)
            start: Start position (1-1000)
            sort: Sort order ('date' or 'sim' for similarity)

        Returns:
            List of NewsItem objects
        """
        client = await self._get_client()
        params = {
            "query": query,
            "display": min(display, 100),
            "start": start,
            "sort": sort,
        }

        logger.info(f"Searching news for: {query}")
        response = await client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()
        items = []

        for item in data.get("items", []):
            # Clean HTML tags from title and description
            title = self._clean_html(item.get("title", ""))
            description = self._clean_html(item.get("description", ""))

            # Parse date
            pub_date = self._parse_date(item.get("pubDate", ""))

            news_item = NewsItem(
                title=title,
                description=description,
                url=item.get("originallink") or item.get("link", ""),
                published_at=pub_date,
                source=self._extract_source(item.get("link", "")),
            )
            items.append(news_item)

        logger.info(f"Found {len(items)} news items for: {query}")
        return items

    async def collect_by_keywords(
        self, keywords: Optional[List[str]] = None
    ) -> List[NewsItem]:
        """
        Collect news for multiple keywords.

        Args:
            keywords: List of search keywords. Uses settings if not provided.

        Returns:
            Combined list of NewsItem objects (deduplicated by URL)
        """
        keywords = keywords or settings.search_keywords
        all_items = []
        seen_urls = set()

        for keyword in keywords:
            items = await self.search(keyword)
            for item in items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_items.append(item)

        logger.info(f"Collected {len(all_items)} unique news items")
        return all_items

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags and entities from text."""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Decode common HTML entities
        text = text.replace("&quot;", '"')
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&nbsp;", " ")
        return text.strip()

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Parse Naver's date format to YYYY-MM-DD HH:mm."""
        try:
            # Naver format: "Sat, 21 Dec 2024 15:30:00 +0900"
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return datetime.now().strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _extract_source(url: str) -> str:
        """Extract source name from URL."""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except Exception:
            return "unknown"
