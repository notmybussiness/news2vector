"""
EXP-01 개선 실험: 하이브리드 검색 vs 기존 벡터 검색 비교

가설: 하이브리드 검색(벡터 + 키워드 부스팅)이 종목명 검색 정밀도를 향상시킨다.
통제 변인: 쿼리 목록, Top-K(5), 데이터셋(778개)
가변 요인: 검색 방식 (vector_only vs hybrid)
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


def run_comparison():
    print("\n" + "=" * 60)
    print("EXP-01 개선: 하이브리드 검색 vs 벡터 검색")
    print("=" * 60)

    embedder = KoSRoBERTaEmbedding()
    storage = MilvusClient()
    storage.connect()

    queries = ["삼성전자", "SK하이닉스", "네이버", "카카오", "LG에너지솔루션"]

    results = {
        "experiment": "exp01_hybrid_comparison",
        "timestamp": datetime.now().isoformat(),
        "comparison": {},
    }

    for query in queries:
        embedding = embedder.embed(query)[0].tolist()

        # 방법 A: 기존 벡터 검색
        vector_results = storage.search(embedding, top_k=5)
        vector_relevant = sum(
            1 for r in vector_results if query.lower() in r.get("title", "").lower()
        )
        vector_precision = vector_relevant / 5

        # 방법 B: 하이브리드 검색
        hybrid_results = storage.hybrid_search(
            query, embedding, top_k=5, boost_factor=1.5
        )
        hybrid_relevant = sum(
            1 for r in hybrid_results if query.lower() in r.get("title", "").lower()
        )
        hybrid_precision = hybrid_relevant / 5

        improvement = (hybrid_precision - vector_precision) * 100

        results["comparison"][query] = {
            "vector_only": {
                "relevant": vector_relevant,
                "precision": vector_precision,
                "top_titles": [r.get("title", "")[:40] for r in vector_results[:3]],
            },
            "hybrid": {
                "relevant": hybrid_relevant,
                "precision": hybrid_precision,
                "top_titles": [r.get("title", "")[:40] for r in hybrid_results[:3]],
                "match_types": [r.get("match_type", "") for r in hybrid_results],
            },
            "improvement": improvement,
        }

        status = "✅" if improvement > 0 else "➖" if improvement == 0 else "❌"
        print(f"\n{query}:")
        print(f"  벡터 검색: {vector_relevant}/5 ({vector_precision*100:.0f}%)")
        print(
            f"  하이브리드: {hybrid_relevant}/5 ({hybrid_precision*100:.0f}%) {status} {improvement:+.0f}%p"
        )

    # 평균 계산
    avg_vector = sum(
        r["vector_only"]["precision"] for r in results["comparison"].values()
    ) / len(queries)
    avg_hybrid = sum(
        r["hybrid"]["precision"] for r in results["comparison"].values()
    ) / len(queries)
    avg_improvement = (avg_hybrid - avg_vector) * 100

    results["summary"] = {
        "avg_vector_precision": avg_vector,
        "avg_hybrid_precision": avg_hybrid,
        "avg_improvement_pp": avg_improvement,
    }

    print("\n" + "=" * 60)
    print("📊 종합 결과")
    print("=" * 60)
    print(f"  벡터 검색 평균: {avg_vector*100:.1f}%")
    print(f"  하이브리드 평균: {avg_hybrid*100:.1f}%")
    print(f"  개선도: {avg_improvement:+.1f}%p")

    # 결과 저장
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 결과 저장: {output_dir}/results.json")

    storage.disconnect()
    return results


if __name__ == "__main__":
    run_comparison()
