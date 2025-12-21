"""
Embedding Test Script

Tests the ko-sroberta embedding model locally.
"""

from sentence_transformers import SentenceTransformer
import numpy as np


def main():
    print("=" * 60)
    print("Embedding Model Test")
    print("=" * 60)

    # Load model
    print("\nLoading model: jhgan/ko-sroberta-multitask")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    print(f"✓ Model loaded on device: {model.device}")

    # Test texts
    texts = [
        "삼성전자 반도체 실적이 크게 개선되었습니다.",
        "SK하이닉스 HBM 수주가 증가했습니다.",
        "네이버 AI 서비스 확대로 주가가 상승했습니다.",
        "오늘 날씨가 매우 좋습니다.",  # Unrelated text for comparison
    ]

    # Generate embeddings
    print("\nGenerating embeddings...")
    embeddings = model.encode(texts, normalize_embeddings=True)

    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"  Dimension: {embeddings.shape[1]}")

    # Calculate similarities
    print("\n" + "=" * 60)
    print("Similarity Matrix")
    print("=" * 60)

    similarities = np.inner(embeddings, embeddings)

    # Print header
    print("\n" + " " * 30, end="")
    for i in range(len(texts)):
        print(f"  [{i}]  ", end="")
    print()

    # Print matrix
    for i, text in enumerate(texts):
        print(f"[{i}] {text[:25]:25s}", end="")
        for j in range(len(texts)):
            sim = similarities[i][j]
            print(f" {sim:.3f} ", end="")
        print()

    # Test query
    print("\n" + "=" * 60)
    print("Query Test")
    print("=" * 60)

    query = "반도체 주식 동향"
    query_embedding = model.encode(query, normalize_embeddings=True)

    print(f"\nQuery: '{query}'")
    print("\nResults (by similarity):")

    scores = np.inner(query_embedding, embeddings)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    for rank, (idx, score) in enumerate(ranked, 1):
        print(f"  {rank}. [{score:.4f}] {texts[idx]}")

    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    main()
