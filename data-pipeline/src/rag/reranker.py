"""Cross-encoder based reranker for improving search precision."""

from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from sentence_transformers import CrossEncoder

    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not installed, reranking disabled")


class CrossEncoderReranker:
    """
    Reranker using Cross-Encoder model.

    Cross-encoders compute query-document relevance directly,
    providing more accurate ranking than bi-encoder similarity.
    """

    # Korean-optimized reranker model
    DEFAULT_MODEL = "Dongjin-kr/ko-reranker"

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the reranker.

        Args:
            model_name: HuggingFace model name (default: ms-marco-MiniLM-L-6-v2)
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model: Optional[CrossEncoder] = None
        self._enabled = CROSS_ENCODER_AVAILABLE

        if not self._enabled:
            logger.warning("CrossEncoderReranker disabled: missing dependencies")

    @property
    def model(self) -> Optional[CrossEncoder]:
        """Lazy load the model."""
        if not self._enabled:
            return None

        if self._model is None:
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
            logger.info("Cross-encoder model loaded")

        return self._model

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        text_field: str = "original_text",
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using cross-encoder.

        Args:
            query: Search query
            results: List of search results with text field
            top_k: Number of results to return (default: all)
            text_field: Field name containing the text to compare

        Returns:
            Reranked results with added 'rerank_score' field
        """
        if not results:
            return results

        if not self._enabled or self.model is None:
            logger.debug("Reranking skipped: model not available")
            return results[:top_k] if top_k else results

        try:
            # Create query-document pairs
            pairs = []
            for result in results:
                text = result.get(text_field, "")
                # Include title for better context
                title = result.get("title", "")
                combined = f"{title}. {text}" if title else text
                pairs.append((query, combined))

            # Get cross-encoder scores
            scores = self.model.predict(pairs)

            # Add scores to results (keep original score for filtering)
            for result, score in zip(results, scores):
                result["rerank_score"] = float(score)
                # Keep original score - don't overwrite with rerank score
                # Cross-encoder scores can be negative, which breaks min_relevance filter

            # Sort by rerank score (descending)
            reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

            logger.debug(
                f"Reranked {len(results)} results, top score: {reranked[0]['rerank_score']:.4f}"
            )

            return reranked[:top_k] if top_k else reranked

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:top_k] if top_k else results

    def is_enabled(self) -> bool:
        """Check if reranker is available."""
        return self._enabled

    def get_model_info(self) -> dict:
        """Get information about the model."""
        return {
            "model_name": self.model_name,
            "enabled": self._enabled,
            "loaded": self._model is not None,
        }
