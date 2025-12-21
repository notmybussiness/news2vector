"""
Naver API Test Script

Tests the Naver News API connection with current credentials.
"""

import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src.collectors import NaverNewsCollector


async def main():
    print("=" * 60)
    print("Naver News API Test")
    print("=" * 60)

    collector = NaverNewsCollector()

    try:
        # Test single query
        query = "증시"
        print(f"\n🔍 Testing query: '{query}'")

        items = await collector.search(query, display=10)

        print(f"✅ Found {len(items)} news items\n")

        for i, item in enumerate(items[:5], 1):
            print(f"{i}. {item.title[:50]}...")
            print(f"   📅 {item.published_at}")
            print(f"   🔗 {item.url[:60]}...")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await collector.close()

    print("✅ API Test Completed!")


if __name__ == "__main__":
    asyncio.run(main())
