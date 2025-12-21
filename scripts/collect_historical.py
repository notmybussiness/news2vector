"""
과거 뉴스 대량 수집 스크립트

네이버 API는 날짜 필터가 없어서, 페이지네이션으로 최대한 수집합니다.
- 최대 start=1000까지 가능 (API 제한)
- 키워드당 1000개 → 11개 키워드 × 1000 = 최대 11000개 (중복 제거 후 더 적음)

Usage:
    cd data-pipeline && source venv/bin/activate && cd ..
    python scripts/collect_historical.py
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src.collectors import NaverNewsCollector
from src.embeddings import KoSRoBERTaEmbedding
from src.storage import MilvusClient
from src.processors import TextSplitter, Deduplicator


async def collect_historical(max_pages_per_keyword: int = 10):
    """
    과거 뉴스 대량 수집

    Args:
        max_pages_per_keyword: 키워드당 페이지 수 (1페이지 = 100개, max 10)
    """
    print("\n" + "=" * 60)
    print(f"과거 뉴스 대량 수집 (키워드당 {max_pages_per_keyword}페이지)")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 60)

    # 키워드 목록
    keywords = [
        "경제",
        "증시",
        "주식시장",
        "코스피",
        "코스닥",
        "삼성전자",
        "SK하이닉스",
        "금융",
        "투자",
        "환율",
        "금리",
    ]

    collector = NaverNewsCollector()
    embedder = KoSRoBERTaEmbedding()
    storage = MilvusClient()
    splitter = TextSplitter()
    deduplicator = Deduplicator()

    all_items = []
    seen_urls = set()

    try:
        # 1. 뉴스 수집
        print("\n📰 Step 1: 뉴스 수집 중...")
        for keyword in keywords:
            print(f"  수집 중: {keyword}", end="", flush=True)
            keyword_count = 0

            for page in range(max_pages_per_keyword):
                start = page * 100 + 1
                if start > 1000:  # API 제한
                    break

                items = await collector.search(
                    keyword, display=100, start=start, sort="date"
                )

                for item in items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        all_items.append(item)
                        keyword_count += 1

                print(".", end="", flush=True)

            print(f" +{keyword_count}개 (총 {len(all_items)}개)")

        print(f"\n  ✓ 총 수집: {len(all_items)}개")

        # 2. Milvus 연결 및 중복 체크
        print("\n🔍 Step 2: 중복 체크...")
        storage.connect()
        storage.create_collection()

        existing_count = storage.count()
        print(f"  기존 데이터: {existing_count}개")

        # URL 기반 중복 제거 (기존 DB와 비교)
        new_items = []
        for item in all_items:
            if not storage.check_url_exists(item.url):
                new_items.append(item)

        print(f"  신규 데이터: {len(new_items)}개")

        if not new_items:
            print("\n  ℹ️ 신규 데이터 없음. 종료.")
            return {"collected": len(all_items), "new": 0}

        # 3. 임베딩 생성
        print("\n🧠 Step 3: 임베딩 생성...")
        texts = [item.full_text for item in new_items]
        embeddings = embedder.embed_batch(texts)
        print(f"  ✓ {len(embeddings)}개 임베딩 생성")

        # 4. Milvus 저장
        print("\n💾 Step 4: Milvus 저장...")
        # 임베딩이 numpy array인 경우 tolist(), 이미 list면 그대로
        embedding_list = [e.tolist() if hasattr(e, "tolist") else e for e in embeddings]
        ids = storage.insert(
            embeddings=embedding_list,
            texts=texts,
            titles=[item.title for item in new_items],
            published_dates=[item.published_at for item in new_items],
            urls=[item.url for item in new_items],
        )

        final_count = storage.count()
        print(f"  ✓ {len(ids)}개 저장 완료")
        print(f"  총 데이터: {final_count}개")

        result = {
            "collected": len(all_items),
            "new": len(new_items),
            "stored": len(ids),
            "total": final_count,
        }

    finally:
        await collector.close()
        storage.disconnect()

    print("\n" + "=" * 60)
    print(f"완료 시간: {datetime.now()}")
    print("=" * 60)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="과거 뉴스 대량 수집")
    parser.add_argument(
        "--pages", type=int, default=5, help="키워드당 페이지 수 (1-10)"
    )
    args = parser.parse_args()

    pages = min(max(args.pages, 1), 10)  # 1-10 범위
    result = asyncio.run(collect_historical(max_pages_per_keyword=pages))

    print(f"\n📊 결과: {result}")
