"""
통합 실험 러너 - 모든 검색 정확도 실험을 순차적으로 실행

Usage:
    cd data-pipeline && source venv/bin/activate && cd ..
    python experiments/exp_runner.py
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src.embeddings import KoSRoBERTaEmbedding
from src.storage import MilvusClient


class ExperimentRunner:
    """실험 실행 및 결과 저장 관리"""

    def __init__(self):
        self.embedder = KoSRoBERTaEmbedding()
        self.storage = MilvusClient()
        self.results_dir = Path(__file__).parent

    def search(self, query: str, top_k: int = 5):
        """쿼리 실행 및 결과 반환"""
        # 임베딩 생성
        embedding = self.embedder.embed(query)[0].tolist()

        # Milvus 검색
        self.storage.connect()
        results = self.storage.search(embedding, top_k=top_k)

        return results

    def save_results(self, exp_name: str, results: dict):
        """결과를 JSON으로 저장"""
        exp_dir = self.results_dir / exp_name
        exp_dir.mkdir(exist_ok=True)

        results["timestamp"] = datetime.now().isoformat()

        with open(exp_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"✓ 결과 저장: {exp_dir}/results.json")

    def run_exp01_stock_search(self):
        """EXP-01: 종목명 검색"""
        print("\n" + "=" * 60)
        print("EXP-01: 종목명 검색")
        print("=" * 60)

        queries = ["삼성전자", "SK하이닉스", "네이버", "카카오", "LG에너지솔루션"]
        results = {"experiment": "exp01_stock_search", "queries": {}}

        for query in queries:
            search_results = self.search(query, top_k=5)

            # 관련성 평가 (제목에 쿼리 단어 포함 여부)
            relevant_count = 0
            query_results = []

            for r in search_results:
                title = r.get("title", "")
                is_relevant = query.lower() in title.lower() or any(
                    kw in title for kw in query.split()
                )
                if is_relevant:
                    relevant_count += 1

                query_results.append(
                    {
                        "title": title[:50],
                        "score": r.get("score", 0),
                        "distance": r.get("distance", 0),
                        "is_relevant": is_relevant,
                    }
                )

            precision = relevant_count / len(search_results) if search_results else 0

            results["queries"][query] = {
                "results": query_results,
                "relevant_count": relevant_count,
                "total": len(search_results),
                "precision": precision,
            }

            print(f"  {query}: {relevant_count}/5 관련 ({precision*100:.0f}%)")

        # 평균 정밀도
        avg_precision = sum(q["precision"] for q in results["queries"].values()) / len(
            queries
        )
        results["avg_precision"] = avg_precision
        print(f"\n  📊 평균 정밀도: {avg_precision*100:.1f}%")

        self.save_results("exp01_stock_search", results)
        return results

    def run_exp02_sector_search(self):
        """EXP-02: 업종/섹터 검색"""
        print("\n" + "=" * 60)
        print("EXP-02: 업종/섹터 검색")
        print("=" * 60)

        sector_keywords = {
            "반도체": ["반도체", "메모리", "HBM", "파운드리", "삼성전자", "SK하이닉스"],
            "2차전지": ["배터리", "2차전지", "전기차", "LG에너지", "삼성SDI"],
            "AI": ["AI", "인공지능", "GPT", "딥러닝", "엔비디아"],
            "금융": ["금융", "은행", "증권", "보험", "금리"],
        }

        results = {"experiment": "exp02_sector_search", "sectors": {}}

        for sector, keywords in sector_keywords.items():
            search_results = self.search(sector, top_k=5)

            relevant_count = 0
            sector_results = []

            for r in search_results:
                title = r.get("title", "")
                text = r.get("original_text", "")
                combined = title + " " + text

                is_relevant = any(kw.lower() in combined.lower() for kw in keywords)
                if is_relevant:
                    relevant_count += 1

                sector_results.append(
                    {
                        "title": title[:50],
                        "score": r.get("score", 0),
                        "is_relevant": is_relevant,
                    }
                )

            precision = relevant_count / len(search_results) if search_results else 0

            results["sectors"][sector] = {
                "keywords": keywords,
                "results": sector_results,
                "relevant_count": relevant_count,
                "precision": precision,
            }

            print(f"  {sector}: {relevant_count}/5 관련 ({precision*100:.0f}%)")

        avg_precision = sum(s["precision"] for s in results["sectors"].values()) / len(
            sector_keywords
        )
        results["avg_precision"] = avg_precision
        print(f"\n  📊 평균 정밀도: {avg_precision*100:.1f}%")

        self.save_results("exp02_sector_search", results)
        return results

    def run_exp03_event_search(self):
        """EXP-03: 이벤트/맥락 검색"""
        print("\n" + "=" * 60)
        print("EXP-03: 이벤트/맥락 검색")
        print("=" * 60)

        event_keywords = {
            "금리 인상": ["금리", "기준금리", "인상", "한국은행", "금융통화위원회"],
            "실적 발표": ["실적", "영업이익", "매출", "분기", "호실적", "어닝"],
            "주가 하락": ["하락", "급락", "폭락", "약세", "베어마켓"],
            "M&A": ["인수", "합병", "M&A", "피인수", "인수합병"],
        }

        results = {"experiment": "exp03_event_search", "events": {}}

        for event, keywords in event_keywords.items():
            search_results = self.search(event, top_k=5)

            relevant_count = 0
            event_results = []

            for r in search_results:
                title = r.get("title", "")
                text = r.get("original_text", "")
                combined = title + " " + text

                is_relevant = any(kw.lower() in combined.lower() for kw in keywords)
                if is_relevant:
                    relevant_count += 1

                event_results.append(
                    {
                        "title": title[:50],
                        "score": r.get("score", 0),
                        "is_relevant": is_relevant,
                    }
                )

            precision = relevant_count / len(search_results) if search_results else 0

            results["events"][event] = {
                "keywords": keywords,
                "results": event_results,
                "relevant_count": relevant_count,
                "precision": precision,
            }

            print(f"  {event}: {relevant_count}/5 관련 ({precision*100:.0f}%)")

        avg_precision = sum(e["precision"] for e in results["events"].values()) / len(
            event_keywords
        )
        results["avg_precision"] = avg_precision
        print(f"\n  📊 평균 정밀도: {avg_precision*100:.1f}%")

        self.save_results("exp03_event_search", results)
        return results

    def run_exp04_topk_variation(self):
        """EXP-04: Top-K 변동"""
        print("\n" + "=" * 60)
        print("EXP-04: Top-K 변동")
        print("=" * 60)

        query = "반도체 주식"
        keywords = ["반도체", "주식", "코스피", "코스닥", "삼성전자", "SK하이닉스"]
        k_values = [3, 5, 10, 20]

        results = {
            "experiment": "exp04_topk_variation",
            "query": query,
            "k_results": {},
        }

        for k in k_values:
            search_results = self.search(query, top_k=k)

            relevant_count = 0
            for r in search_results:
                title = r.get("title", "")
                text = r.get("original_text", "")
                combined = title + " " + text

                if any(kw.lower() in combined.lower() for kw in keywords):
                    relevant_count += 1

            precision = relevant_count / len(search_results) if search_results else 0

            results["k_results"][str(k)] = {
                "total": len(search_results),
                "relevant_count": relevant_count,
                "precision": precision,
                "avg_score": (
                    sum(r.get("score", 0) for r in search_results) / len(search_results)
                    if search_results
                    else 0
                ),
            }

            print(
                f"  K={k}: {relevant_count}/{k} 관련 ({precision*100:.0f}%), 평균 점수: {results['k_results'][str(k)]['avg_score']:.3f}"
            )

        self.save_results("exp04_topk_variation", results)
        return results

    def run_exp05_distance_threshold(self):
        """EXP-05: 거리 임계값 필터링"""
        print("\n" + "=" * 60)
        print("EXP-05: 거리 임계값 필터링")
        print("=" * 60)

        query = "금융 투자"
        keywords = ["금융", "투자", "은행", "증권", "펀드", "자산"]
        thresholds = [0.5, 1.0, 1.5, 2.0]

        # 더 많은 결과 가져오기
        all_results = self.search(query, top_k=50)

        results = {
            "experiment": "exp05_distance_threshold",
            "query": query,
            "thresholds": {},
        }

        for threshold in thresholds:
            filtered = [
                r for r in all_results if r.get("distance", float("inf")) <= threshold
            ]

            relevant_count = 0
            for r in filtered:
                title = r.get("title", "")
                text = r.get("original_text", "")
                combined = title + " " + text

                if any(kw.lower() in combined.lower() for kw in keywords):
                    relevant_count += 1

            precision = relevant_count / len(filtered) if filtered else 0
            recall = relevant_count / len(all_results) if all_results else 0

            results["thresholds"][str(threshold)] = {
                "total_filtered": len(filtered),
                "relevant_count": relevant_count,
                "precision": precision,
                "recall": recall,
            }

            print(
                f"  거리 ≤ {threshold}: {len(filtered)}개 (관련: {relevant_count}, 정밀도: {precision*100:.0f}%)"
            )

        self.save_results("exp05_distance_threshold", results)
        return results

    def run_all(self):
        """모든 실험 실행"""
        print("\n🧪 검색 정확도 실험 시작")
        print("=" * 60)

        self.storage.connect()

        try:
            exp01 = self.run_exp01_stock_search()
            exp02 = self.run_exp02_sector_search()
            exp03 = self.run_exp03_event_search()
            exp04 = self.run_exp04_topk_variation()
            exp05 = self.run_exp05_distance_threshold()

            # 종합 결과
            print("\n" + "=" * 60)
            print("📊 종합 결과")
            print("=" * 60)
            print(f"  EXP-01 종목명 검색: {exp01['avg_precision']*100:.1f}%")
            print(f"  EXP-02 섹터 검색: {exp02['avg_precision']*100:.1f}%")
            print(f"  EXP-03 이벤트 검색: {exp03['avg_precision']*100:.1f}%")
            print(
                f"  EXP-04 Top-K 변동: K=5 정밀도 {exp04['k_results']['5']['precision']*100:.1f}%"
            )
            print(
                f"  EXP-05 거리 임계값: threshold=1.0 정밀도 {exp05['thresholds']['1.0']['precision']*100:.1f}%"
            )

            # 종합 저장
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_entities": self.storage.count(),
                "experiments": {
                    "exp01": exp01["avg_precision"],
                    "exp02": exp02["avg_precision"],
                    "exp03": exp03["avg_precision"],
                    "exp04_k5": exp04["k_results"]["5"]["precision"],
                    "exp05_t1.0": exp05["thresholds"]["1.0"]["precision"],
                },
            }

            with open(self.results_dir / "summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            print(f"\n✓ 종합 결과 저장: experiments/summary.json")

        finally:
            self.storage.disconnect()


if __name__ == "__main__":
    runner = ExperimentRunner()
    runner.run_all()
