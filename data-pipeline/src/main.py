"""
News2Vector Data Pipeline - Main Entry Point

This module orchestrates the complete data pipeline:
1. Collect news from Naver API
2. Split text into chunks
3. Generate embeddings
4. Store in Milvus

Usage:
    python -m src.main                    # Run once
    python -m src.main --keywords "삼성전자,SK하이닉스"  # Custom keywords
"""

import asyncio
import argparse
from typing import List, Optional
from loguru import logger
import sys

from .config import settings
from .collectors import NaverNewsCollector, NewsItem
from .processors import TextSplitter, Deduplicator
from .embeddings import KoSRoBERTaEmbedding
from .storage import MilvusClient


class DataPipeline:
    """
    Main data pipeline orchestrator.

    Coordinates news collection, processing, embedding, and storage.
    """

    def __init__(self, keywords: Optional[List[str]] = None):
        """
        Initialize the pipeline.

        Args:
            keywords: Search keywords (uses settings if not provided)
        """
        self.keywords = keywords or settings.search_keywords

        # Initialize components
        self.collector = NaverNewsCollector()
        self.splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
        self.deduplicator = Deduplicator()
        self.embedder = KoSRoBERTaEmbedding()
        self.storage = MilvusClient()

        logger.info(f"Pipeline initialized with keywords: {self.keywords}")

    async def run(self) -> dict:
        """
        Execute the complete pipeline.

        Returns:
            Statistics about the pipeline run
        """
        stats = {
            "news_collected": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "records_inserted": 0,
            "duplicates_skipped": 0,
        }

        try:
            # Step 1: Collect news
            logger.info("Step 1: Collecting news from Naver API")
            news_items = await self.collector.collect_by_keywords(self.keywords)
            stats["news_collected"] = len(news_items)

            if not news_items:
                logger.warning("No news items collected")
                return stats

            # Step 2: Filter duplicates using Milvus
            logger.info("Step 2: Filtering duplicates")
            new_items = []
            for item in news_items:
                if not self.storage.check_url_exists(item.url):
                    new_items.append(item)
                else:
                    stats["duplicates_skipped"] += 1

            if not new_items:
                logger.info("All items are duplicates, nothing to insert")
                return stats

            # Step 3: Split text into chunks
            logger.info("Step 3: Splitting text into chunks")
            all_chunks = []
            for item in new_items:
                chunks = self.splitter.split_text(
                    text=item.full_text,
                    title=item.title,
                    url=item.url,
                    published_at=item.published_at,
                )
                all_chunks.extend(chunks)
            stats["chunks_created"] = len(all_chunks)

            # Step 4: Generate embeddings
            logger.info("Step 4: Generating embeddings")
            texts = [chunk.content for chunk in all_chunks]
            embeddings = self.embedder.embed_batch(texts, batch_size=32)
            stats["embeddings_generated"] = len(embeddings)

            # Step 5: Store in Milvus
            logger.info("Step 5: Storing in Milvus")
            ids = self.storage.insert(
                embeddings=embeddings,
                texts=texts,
                titles=[chunk.original_title for chunk in all_chunks],
                published_dates=[chunk.published_at for chunk in all_chunks],
                urls=[chunk.original_url for chunk in all_chunks],
            )
            stats["records_inserted"] = len(ids)

            logger.info(f"Pipeline completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

        finally:
            await self.collector.close()
            self.storage.disconnect()

    async def search(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Search for similar news.

        Args:
            query: Search query (ticker name, company name, etc.)
            top_k: Number of results

        Returns:
            List of similar news items
        """
        # Generate embedding for query
        query_embedding = self.embedder.embed(query)[0].tolist()

        # Search in Milvus
        results = self.storage.search(query_embedding, top_k=top_k)

        return results


def setup_logging():
    """Configure loguru logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )
    logger.add(
        "logs/pipeline_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="News2Vector Data Pipeline")
    parser.add_argument(
        "--keywords",
        type=str,
        help="Comma-separated list of search keywords",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search query (instead of running pipeline)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of search results",
    )
    args = parser.parse_args()

    setup_logging()

    # Parse keywords
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",")]

    pipeline = DataPipeline(keywords=keywords)

    if args.search:
        # Search mode
        logger.info(f"Searching for: {args.search}")
        results = await pipeline.search(args.search, top_k=args.top_k)

        print("\n" + "=" * 60)
        print(f"Search Results for: {args.search}")
        print("=" * 60)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Date: {result['published_at']}")
            print(f"   URL: {result['url']}")
            print(f"   Text: {result['original_text'][:100]}...")
    else:
        # Pipeline mode
        stats = await pipeline.run()

        print("\n" + "=" * 60)
        print("Pipeline Results")
        print("=" * 60)
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
