"""
Accuracy comparison: Vector-only vs Re-ranking

Run inside Docker container:
    docker exec news2vector-rag-api python -m src.experiments.accuracy_test
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.embeddings import KoSRoBERTaEmbedding
from src.storage import MilvusClient

# Lazy import to avoid circular dependency
def get_reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder('Dongjin-kr/ko-reranker')


def run_experiment():
    print("\n" + "=" * 60)
    print("RAG Accuracy Experiment: Vector vs Re-ranking")
    print("=" * 60)

    # Initialize
    embedder = KoSRoBERTaEmbedding()
    storage = MilvusClient()
    storage.connect()

    print("\nLoading cross-encoder model...")
    reranker = get_reranker()
    print("Model loaded.\n")

    # Test queries (stock names)
    queries = ["삼성전자", "SK하이닉스", "네이버", "카카오", "LG에너지솔루션"]

    results_vector = []
    results_rerank = []

    for query in queries:
        # Generate embedding
        embedding = embedder.embed(query)[0].tolist()

        # Vector search (fetch more for reranking)
        raw_results = storage.search(embedding, top_k=20)

        # Method A: Vector only (top 5)
        vector_top5 = raw_results[:5]
        vector_relevant = sum(
            1 for r in vector_top5
            if query.lower() in r.get("title", "").lower()
        )
        results_vector.append(vector_relevant)

        # Method B: Rerank then top 5
        pairs = [
            (query, f"{r.get('title', '')}. {r.get('original_text', '')[:200]}")
            for r in raw_results
        ]
        scores = reranker.predict(pairs)

        # Add scores and sort
        for r, score in zip(raw_results, scores):
            r['rerank_score'] = float(score)

        reranked = sorted(raw_results, key=lambda x: x['rerank_score'], reverse=True)
        rerank_top5 = reranked[:5]
        rerank_relevant = sum(
            1 for r in rerank_top5
            if query.lower() in r.get("title", "").lower()
        )
        results_rerank.append(rerank_relevant)

        # Print per-query results
        print(f"{query}:")
        print(f"  Vector:  {vector_relevant}/5 ({vector_relevant*20}%)")
        print(f"  Rerank:  {rerank_relevant}/5 ({rerank_relevant*20}%)")

        # Show top results
        print(f"  [Vector top 3]")
        for i, r in enumerate(vector_top5[:3], 1):
            title = r.get('title', '')[:40]
            match = "O" if query.lower() in r.get('title', '').lower() else "X"
            print(f"    {i}. [{match}] {title}")

        print(f"  [Rerank top 3]")
        for i, r in enumerate(rerank_top5[:3], 1):
            title = r.get('title', '')[:40]
            match = "O" if query.lower() in r.get('title', '').lower() else "X"
            print(f"    {i}. [{match}] {title}")
        print()

    # Calculate averages
    avg_vector = sum(results_vector) / len(queries) / 5 * 100
    avg_rerank = sum(results_rerank) / len(queries) / 5 * 100
    improvement = avg_rerank - avg_vector

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Vector-only accuracy:  {avg_vector:.1f}%")
    print(f"Re-ranking accuracy:   {avg_rerank:.1f}%")
    print(f"Improvement:           {improvement:+.1f}%p")
    print("=" * 60)

    storage.disconnect()

    return {
        "vector": avg_vector,
        "rerank": avg_rerank,
        "improvement": improvement
    }


if __name__ == "__main__":
    run_experiment()
