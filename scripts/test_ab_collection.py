"""
A/B Test Script for News Collection

A) 경제 뉴스 한정 (100개) - "경제" 키워드 검색
B) 대량 뉴스 수집 (2000개) - 페이지네이션으로 여러 페이지

비교: 검색 정확도, 수집 시간
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src.collectors import NaverNewsCollector
from src.config import settings


async def test_a_economy_focused():
    """Test A: 경제 뉴스 한정"""
    print("\n" + "=" * 60)
    print("TEST A: 경제 뉴스 한정 검색")
    print("=" * 60)

    collector = NaverNewsCollector()

    # 경제 관련 키워드로 검색
    economy_keywords = ["경제 뉴스", "주식시장", "코스피 경제", "환율", "금리"]

    start_time = time.time()
    all_items = []
    seen_urls = set()

    try:
        for keyword in economy_keywords:
            items = await collector.search(keyword, display=100, sort="date")
            for item in items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_items.append(item)
            print(f"  '{keyword}': {len(items)}개 (누적: {len(all_items)})")
    finally:
        await collector.close()

    elapsed = time.time() - start_time

    print(f"\n📊 결과:")
    print(f"  총 수집: {len(all_items)}개")
    print(f"  소요 시간: {elapsed:.2f}초")
    print(f"  초당 수집: {len(all_items)/elapsed:.1f}개/초")

    # 샘플 출력
    print(f"\n📰 샘플 (처음 5개):")
    for i, item in enumerate(all_items[:5], 1):
        print(f"  {i}. {item.title[:50]}...")

    return all_items


async def test_b_mass_collection():
    """Test B: 대량 뉴스 수집 (페이지네이션)"""
    print("\n" + "=" * 60)
    print("TEST B: 대량 뉴스 수집 (목표: 2000개)")
    print("=" * 60)

    collector = NaverNewsCollector()

    # 다양한 키워드로 더 많이 수집
    keywords = [
        "증시",
        "주식",
        "코스피",
        "코스닥",
        "삼성전자",
        "SK하이닉스",
        "금융",
        "은행",
        "투자",
        "펀드",
    ]

    start_time = time.time()
    all_items = []
    seen_urls = set()

    try:
        for keyword in keywords:
            # 각 키워드당 200개 (100개씩 2페이지)
            for start in [1, 101]:
                items = await collector.search(
                    keyword, display=100, start=start, sort="date"
                )
                for item in items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        all_items.append(item)

                if len(all_items) >= 2000:
                    break

            print(f"  '{keyword}': 누적 {len(all_items)}개")

            if len(all_items) >= 2000:
                break
    finally:
        await collector.close()

    elapsed = time.time() - start_time

    print(f"\n📊 결과:")
    print(f"  총 수집: {len(all_items)}개")
    print(f"  소요 시간: {elapsed:.2f}초")
    print(f"  초당 수집: {len(all_items)/elapsed:.1f}개/초")

    # 샘플 출력
    print(f"\n📰 샘플 (처음 5개):")
    for i, item in enumerate(all_items[:5], 1):
        print(f"  {i}. {item.title[:50]}...")

    return all_items


async def main():
    print("🧪 A/B 테스트 시작")

    # Test A
    items_a = await test_a_economy_focused()

    # Test B
    items_b = await test_b_mass_collection()

    # 비교 결과
    print("\n" + "=" * 60)
    print("📊 A/B 테스트 비교 결과")
    print("=" * 60)
    print(f"  Test A (경제 한정): {len(items_a)}개")
    print(f"  Test B (대량 수집): {len(items_b)}개")

    # 경제 관련 키워드 포함 비율 계산
    economy_keywords = [
        "경제",
        "주식",
        "코스피",
        "코스닥",
        "증시",
        "금융",
        "투자",
        "은행",
        "금리",
        "환율",
    ]

    def count_economy_related(items):
        count = 0
        for item in items:
            title = item.title.lower()
            if any(kw in title for kw in economy_keywords):
                count += 1
        return count

    eco_a = count_economy_related(items_a)
    eco_b = count_economy_related(items_b)

    print(f"\n📈 경제 관련 뉴스 비율:")
    print(
        f"  Test A: {eco_a}/{len(items_a)} ({eco_a/len(items_a)*100:.1f}%)"
        if items_a
        else "  Test A: 0"
    )
    print(
        f"  Test B: {eco_b}/{len(items_b)} ({eco_b/len(items_b)*100:.1f}%)"
        if items_b
        else "  Test B: 0"
    )


if __name__ == "__main__":
    asyncio.run(main())
