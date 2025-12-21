"""Processors package"""

from .text_splitter import TextSplitter, TextChunk
from .deduplicator import Deduplicator

__all__ = ["TextSplitter", "TextChunk", "Deduplicator"]
