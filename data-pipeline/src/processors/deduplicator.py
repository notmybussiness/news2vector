"""Deduplication utilities for news articles."""

from typing import List, Set
import hashlib
from loguru import logger


class Deduplicator:
    """
    Deduplication manager for news articles.

    Supports multiple deduplication strategies:
    - URL-based (exact match)
    - Title-based (exact match)
    - Content hash-based (near-duplicate detection)
    """

    def __init__(self):
        self._seen_urls: Set[str] = set()
        self._seen_titles: Set[str] = set()
        self._seen_hashes: Set[str] = set()

    def is_duplicate(
        self,
        url: str = "",
        title: str = "",
        content: str = "",
    ) -> bool:
        """
        Check if an article is a duplicate.

        Args:
            url: Article URL
            title: Article title
            content: Article content

        Returns:
            True if duplicate, False otherwise
        """
        # URL check (primary)
        if url and url in self._seen_urls:
            return True

        # Title check (secondary)
        normalized_title = self._normalize_text(title)
        if normalized_title and normalized_title in self._seen_titles:
            return True

        # Content hash check (for near-duplicates)
        if content:
            content_hash = self._hash_content(content)
            if content_hash in self._seen_hashes:
                return True
            self._seen_hashes.add(content_hash)

        # Mark as seen
        if url:
            self._seen_urls.add(url)
        if normalized_title:
            self._seen_titles.add(normalized_title)

        return False

    def deduplicate_list(
        self,
        items: List[dict],
        url_key: str = "url",
        title_key: str = "title",
        content_key: str = "content",
    ) -> List[dict]:
        """
        Remove duplicates from a list of items.

        Args:
            items: List of item dicts
            url_key: Key for URL field
            title_key: Key for title field
            content_key: Key for content field

        Returns:
            Deduplicated list
        """
        result = []
        for item in items:
            if not self.is_duplicate(
                url=item.get(url_key, ""),
                title=item.get(title_key, ""),
                content=item.get(content_key, ""),
            ):
                result.append(item)

        removed_count = len(items) - len(result)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate items")

        return result

    def reset(self):
        """Clear all seen items."""
        self._seen_urls.clear()
        self._seen_titles.clear()
        self._seen_hashes.clear()
        logger.debug("Deduplicator cache cleared")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Remove whitespace and convert to lowercase
        return "".join(text.lower().split())

    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate a hash for content comparison."""
        normalized = Deduplicator._normalize_text(content)
        return hashlib.md5(normalized.encode()).hexdigest()
