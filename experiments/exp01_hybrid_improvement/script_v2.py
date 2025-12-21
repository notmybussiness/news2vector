"""
EXP-01 개선 실험 v2: 쿼리 확장 + 필터 우선 검색

가설: 종목명에 관련 키워드를 추가하면 벡터 검색 정확도가 향상된다
방법:
  1. 쿼리 확장: "삼성전자" → "삼성전자 주가 반도체 실적"
  2. 필터 우선: 제목에 종목명 있는 것 먼저, 나머지는 의미 검색
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "data-pipeline"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from src.embeddings import KoSRoBERTaEmbedding
from src.storage import MilvusClient


# 종목-관련 키워드 사전
STOCK_KEYWORDS = {
    "삼성전자": ["삼성전자", "반도체", "갤럭시", "메모리"],
    "SK하이닉스": ["SK하이닉스", "HBM", "반도체", "메모리"],
    "네이버": ["네이버", "검색", "라인", "웹툰"],
    "카카오": ["카카오", "카톡", "카카오페이", "카카오뱅크"],
    "LG에너지솔루션": ["LG에너지솔루션", "배터리", "2차전지", "전기차"],
}


def expanded_search(embedder, storage, query, top_k=5):
    """쿼리 확장 검색: 종목명 + 관련 키워드"""
    keywords = STOCK_KEYWORDS.get(query, [query])
    expanded_query = " ".join(keywords[:3])  # 상위 3개 키워드

    embedding = embedder.embed(expanded_query)[0].tolist()
    results = storage.search(embedding, top_k=top_k)

    return results, expanded_query


def filter_first_search(embedder, storage, query, top_k=5):
    """필터 우선 검색: 제목에 종목명 있는 것 먼저"""
    embedding = embedder.embed(query)[0].tolist()

    # 많이 가져와서 필터링
    candidates = storage.search(embedding, top_k=50)

    # 1단계: 제목에 종목명 있는 것
    exact_matches = [
        r for r in candidates if query.lower() in r.get("title", "").lower()
    ]

    # 2단계: 나머지 의미 검색 결과
    remaining = [r for r in candidates if r not in exact_matches]

    # 합치기
    final = exact_matches[:top_k]
    if len(final) < top_k:
        final.extend(remaining[: top_k - len(final)])

    return final


def run_comparison():
    print("\n" + "=" * 60)
    print("EXP-01 개선 v2: 쿼리 확장 + 필터 우선")
    print("=" * 60)

    embedder = KoSRoBERTaEmbedding()
    storage = MilvusClient()
    storage.connect()

    queries = list(STOCK_KEYWORDS.keys())

    results = {
        "experiment": "exp01_improved_v2",
        "timestamp": datetime.now().isoformat(),
        "methods": {},
    }

    for query in queries:
        embedding = embedder.embed(query)[0].tolist()

        # 방법 A: 기존 벡터 검색
        vector_results = storage.search(embedding, top_k=5)
        vector_relevant = sum(
            1 for r in vector_results if query.lower() in r.get("title", "").lower()
        )

        # 방법 B: 쿼리 확장
        expanded_results, expanded_query = expanded_search(embedder, storage, query)
        expanded_relevant = sum(
            1 for r in expanded_results if query.lower() in r.get("title", "").lower()
        )

        # 방법 C: 필터 우선
        filter_results = filter_first_search(embedder, storage, query)
        filter_relevant = sum(
            1 for r in filter_results if query.lower() in r.get("title", "").lower()
        )

        results["methods"][query] = {
            "vector_only": {
                "relevant": vector_relevant,
                "precision": vector_relevant / 5,
            },
            "query_expansion": {
                "relevant": expanded_relevant,
                "precision": expanded_relevant / 5,
                "query": expanded_query,
            },
            "filter_first": {
                "relevant": filter_relevant,
                "precision": filter_relevant / 5,
            },
        }

        print(f"\n{query}:")
        print(f"  벡터 검색: {vector_relevant}/5 ({vector_relevant*20}%)")
        print(
            f"  쿼리 확장: {expanded_relevant}/5 ({expanded_relevant*20}%) - '{expanded_query}'"
        )
        print(
            f"  필터 우선: {filter_relevant}/5 ({filter_relevant*20}%) {'✅ 최고' if filter_relevant >= max(vector_relevant, expanded_relevant) and filter_relevant > 0 else ''}"
        )

    # 평균 계산
    avg_vector = sum(
        r["vector_only"]["precision"] for r in results["methods"].values()
    ) / len(queries)
    avg_expanded = sum(
        r["query_expansion"]["precision"] for r in results["methods"].values()
    ) / len(queries)
    avg_filter = sum(
        r["filter_first"]["precision"] for r in results["methods"].values()
    ) / len(queries)

    results["summary"] = {
        "avg_vector": avg_vector,
        "avg_query_expansion": avg_expanded,
        "avg_filter_first": avg_filter,
        "best_method": (
            "filter_first"
            if avg_filter >= max(avg_vector, avg_expanded)
            else ("query_expansion" if avg_expanded > avg_vector else "vector_only")
        ),
    }

    print("\n" + "=" * 60)
    print("📊 종합 결과")
    print("=" * 60)
    print(f"  벡터 검색: {avg_vector*100:.1f}%")
    print(f"  쿼리 확장: {avg_expanded*100:.1f}%")
    print(
        f"  필터 우선: {avg_filter*100:.1f}% {'← 최고!' if avg_filter >= max(avg_vector, avg_expanded) else ''}"
    )
    print(f"\n  개선도 (필터 우선 vs 벡터): {(avg_filter - avg_vector)*100:+.1f}%p")

    # 저장
    output_dir = Path(__file__).parent
    with open(output_dir / "results_v2.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 결과 저장: {output_dir}/results_v2.json")

    storage.disconnect()
    return results


if __name__ == "__main__":
    run_comparison()
