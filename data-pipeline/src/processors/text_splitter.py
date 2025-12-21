"""Text splitting using LangChain's RecursiveCharacterTextSplitter."""

from typing import List
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""

    content: str
    chunk_index: int
    total_chunks: int
    original_title: str
    original_url: str
    published_at: str


class TextSplitter:
    """
    Wrapper for LangChain's RecursiveCharacterTextSplitter.

    Optimized for Korean text with semantic preservation.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None,
    ):
        """
        Initialize the text splitter.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
            separators: Custom separators for splitting (Korean optimized by default)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Korean-optimized separators
        self.separators = separators or [
            "\n\n",  # Paragraph breaks
            "\n",  # Line breaks
            "。",  # Japanese period (sometimes in Korean text)
            ".",  # Period
            "!",  # Exclamation
            "?",  # Question
            "다.",  # Korean sentence ending
            "요.",  # Korean polite ending
            "니다.",  # Korean formal ending
            ",",  # Comma
            " ",  # Space
            "",  # Character
        ]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def split_text(
        self,
        text: str,
        title: str = "",
        url: str = "",
        published_at: str = "",
    ) -> List[TextChunk]:
        """
        Split text into semantic chunks.

        Args:
            text: The full text to split
            title: Original article title
            url: Original article URL
            published_at: Publication date

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        chunks = self._splitter.split_text(text)
        total_chunks = len(chunks)

        result = [
            TextChunk(
                content=chunk,
                chunk_index=i,
                total_chunks=total_chunks,
                original_title=title,
                original_url=url,
                published_at=published_at,
            )
            for i, chunk in enumerate(chunks)
        ]

        logger.debug(f"Split '{title[:30]}...' into {total_chunks} chunks")
        return result

    def split_documents(
        self,
        documents: List[dict],
        text_key: str = "text",
    ) -> List[TextChunk]:
        """
        Split multiple documents into chunks.

        Args:
            documents: List of document dicts with text and metadata
            text_key: Key for the text content in each document

        Returns:
            Combined list of TextChunk objects
        """
        all_chunks = []

        for doc in documents:
            chunks = self.split_text(
                text=doc.get(text_key, ""),
                title=doc.get("title", ""),
                url=doc.get("url", ""),
                published_at=doc.get("published_at", ""),
            )
            all_chunks.extend(chunks)

        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks
