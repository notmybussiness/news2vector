"""
EXP-06: Preprocessing + Re-ranking Improvement Test

Test Contents:
1. NewsPreprocessor unit test
2. CrossEncoderReranker unit test
3. Accuracy comparison (Before vs After)
"""

import sys
import os

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "data-pipeline"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def test_preprocessor():
    """전처리기 단위 테스트"""
    print("\n" + "=" * 60)
    print("TEST 1: NewsPreprocessor 단위 테스트")
    print("=" * 60)

    from src.processors import NewsPreprocessor

    preprocessor = NewsPreprocessor()

    # 테스트 케이스
    test_cases = [
        {
            "name": "기자 이메일 제거",
            "input": "삼성전자가 신제품을 발표했다. 홍길동 기자 hong@example.com",
            "should_remove": "기자 이메일",
        },
        {
            "name": "뉴스 태그 제거",
            "input": "[서울경제뉴스] 주가가 상승했다.",
            "should_remove": "뉴스 태그",
        },
        {
            "name": "저작권 문구 제거",
            "input": "기사 내용입니다. 무단 전재 및 재배포 금지",
            "should_remove": "저작권 문구",
        },
        {
            "name": "관련기사 제거",
            "input": "본문입니다. ▶ 관련기사: SK하이닉스 실적 발표",
            "should_remove": "관련기사",
        },
        {
            "name": "HTML 엔티티 디코딩",
            "input": "삼성전자 &quot;실적 호조&quot; &amp; 주가 상승",
            "expected_contains": '"실적 호조" & 주가 상승',
        },
    ]

    passed = 0
    for case in test_cases:
        result = preprocessor.preprocess(case["input"])
        analysis = preprocessor.analyze(case["input"])

        if "should_remove" in case:
            success = case["should_remove"] in analysis["removed_patterns"]
        else:
            success = case["expected_contains"] in result

        status = "✅" if success else "❌"
        print(f"  {status} {case['name']}")
        if success:
            passed += 1
        else:
            print(f"     입력: {case['input'][:50]}")
            print(f"     결과: {result[:50]}")
            print(f"     제거됨: {analysis['removed_patterns']}")

    print(f"\n  결과: {passed}/{len(test_cases)} 통과")
    return passed == len(test_cases)


def test_reranker():
    """Re-ranker 단위 테스트"""
    print("\n" + "=" * 60)
    print("TEST 2: CrossEncoderReranker 단위 테스트")
    print("=" * 60)

    from src.rag import CrossEncoderReranker

    reranker = CrossEncoderReranker()

    # 모델 로드 확인
    if not reranker.is_enabled():
        print("  ⚠️ Re-ranker 비활성화 (sentence-transformers 미설치)")
        return False

    print(f"  ✅ 모델 로드: {reranker.model_name}")

    # 테스트 데이터
    query = "삼성전자 주가"
    mock_results = [
        {"title": "카카오 실적 발표", "original_text": "카카오가 분기 실적을 발표했다.", "score": 0.9},
        {"title": "삼성전자 주가 상승", "original_text": "삼성전자 주가가 5% 상승했다.", "score": 0.5},
        {"title": "네이버 신규 서비스", "original_text": "네이버가 새 서비스를 출시했다.", "score": 0.8},
        {"title": "삼성전자 반도체", "original_text": "삼성전자가 HBM 생산량을 늘렸다.", "score": 0.3},
    ]

    # Rerank
    print(f"\n  쿼리: '{query}'")
    print(f"  입력 순서 (벡터 점수순):")
    for i, r in enumerate(mock_results):
        print(f"    {i+1}. [{r['score']:.2f}] {r['title']}")

    reranked = reranker.rerank(query, mock_results, top_k=4)

    print(f"\n  Rerank 결과 (cross-encoder 점수순):")
    for i, r in enumerate(reranked):
        print(f"    {i+1}. [{r.get('rerank_score', 0):.4f}] {r['title']}")

    # 검증: 삼성전자 관련 기사가 상위로 올라와야 함
    top_2_titles = [r["title"] for r in reranked[:2]]
    has_samsung = any("삼성전자" in t for t in top_2_titles)

    if has_samsung:
        print("\n  ✅ 관련 기사가 상위로 재정렬됨")
        return True
    else:
        print("\n  ❌ 재정렬 실패")
        return False


def test_integration():
    """통합 테스트: Milvus 검색 + Re-ranking 비교"""
    print("\n" + "=" * 60)
    print("TEST 3: 통합 정확도 비교 (Before vs After)")
    print("=" * 60)

    try:
        from src.embeddings import KoSRoBERTaEmbedding
        from src.storage import MilvusClient
        from src.rag import CrossEncoderReranker
    except ImportError as e:
        print(f"  ❌ Import 실패: {e}")
        return False

    embedder = KoSRoBERTaEmbedding()
    storage = MilvusClient()
    reranker = CrossEncoderReranker()

    try:
        storage.connect()
    except Exception as e:
        print(f"  ⚠️ Milvus 연결 실패: {e}")
        print("  → Docker에서 Milvus가 실행 중인지 확인하세요")
        return False

    queries = ["삼성전자", "SK하이닉스", "네이버", "카카오", "LG에너지솔루션"]

    results_before = []
    results_after = []

    for query in queries:
        # 임베딩 생성
        embedding = embedder.embed(query)[0].tolist()

        # Before: 순수 벡터 검색
        vector_results = storage.search(embedding, top_k=20)
        before_relevant = sum(
            1 for r in vector_results[:5] if query.lower() in r.get("title", "").lower()
        )
        results_before.append(before_relevant)

        # After: 벡터 검색 + Re-ranking
        if reranker.is_enabled():
            reranked = reranker.rerank(query, vector_results, top_k=5)
            after_relevant = sum(
                1 for r in reranked if query.lower() in r.get("title", "").lower()
            )
        else:
            after_relevant = before_relevant
        results_after.append(after_relevant)

        print(f"  {query}: Before={before_relevant}/5, After={after_relevant}/5")

    avg_before = sum(results_before) / len(queries) / 5 * 100
    avg_after = sum(results_after) / len(queries) / 5 * 100
    improvement = avg_after - avg_before

    print(f"\n  📊 평균 정확도:")
    print(f"     Before (벡터 only): {avg_before:.1f}%")
    print(f"     After (+Re-ranking): {avg_after:.1f}%")
    print(f"     개선도: {improvement:+.1f}%p")

    storage.disconnect()

    return improvement >= 0


def main():
    print("\n🧪 RAG 개선 테스트 시작")
    print("=" * 60)

    results = {
        "전처리기": test_preprocessor(),
        "Re-ranker": test_reranker(),
        "통합 테스트": test_integration(),
    }

    print("\n" + "=" * 60)
    print("📊 최종 결과")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print(f"\n{'🎉 모든 테스트 통과!' if all_passed else '⚠️ 일부 테스트 실패'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
