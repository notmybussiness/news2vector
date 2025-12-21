"""Korean embedding model using sentence-transformers."""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger


class KoSRoBERTaEmbedding:
    """
    Embedding generator using jhgan/ko-sroberta-multitask model.

    This model is optimized for Korean semantic similarity tasks.
    Output dimension: 768
    """

    MODEL_NAME = "jhgan/ko-sroberta-multitask"
    DIMENSION = 768

    def __init__(self, device: str = None):
        """
        Initialize the embedding model.

        Args:
            device: Device to run on ('cuda', 'mps', 'cpu'). Auto-detected if None.
        """
        self.device = device
        self._model: SentenceTransformer = None
        logger.info(f"KoSRoBERTa embedding model initialized (lazy loading)")

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            logger.info(f"Loading model: {self.MODEL_NAME}")
            self._model = SentenceTransformer(self.MODEL_NAME, device=self.device)
            logger.info(f"Model loaded on device: {self._model.device}")

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            text: Single text or list of texts

        Returns:
            Numpy array of embeddings (shape: [n, 768])
        """
        self._load_model()

        if isinstance(text, str):
            text = [text]

        embeddings = self._model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=len(text) > 10,
            normalize_embeddings=True,  # L2 normalize for cosine similarity
        )

        return embeddings

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """
        Generate embeddings in batches.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        self._load_model()

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = i // batch_size + 1

            logger.debug(f"Embedding batch {batch_num}/{total_batches}")
            embeddings = self._model.encode(
                batch,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            all_embeddings.extend(embeddings.tolist())

        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self.DIMENSION
