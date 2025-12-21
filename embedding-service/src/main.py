"""
Embedding Service - FastAPI server for text embedding.

Provides REST API for Spring Boot to convert text to vectors.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
from sentence_transformers import SentenceTransformer
from contextlib import asynccontextmanager

# Global model instance
model: SentenceTransformer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    global model
    print("Loading ko-sroberta model...")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    print(f"Model loaded on device: {model.device}")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Embedding Service",
    description="Korean text embedding API using ko-sroberta",
    version="1.0.0",
    lifespan=lifespan,
)


class EmbedRequest(BaseModel):
    """Request model for embedding."""

    texts: List[str]


class EmbedResponse(BaseModel):
    """Response model for embedding."""

    embeddings: List[List[float]]
    dimension: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
    )


@app.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """
    Convert texts to embeddings.

    Args:
        request: List of texts to embed

    Returns:
        List of embedding vectors (768-dim each)
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")

    # Generate embeddings
    embeddings = model.encode(
        request.texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return EmbedResponse(
        embeddings=embeddings.tolist(),
        dimension=768,
    )


@app.post("/embed/single")
async def embed_single(text: str):
    """
    Embed a single text (query convenience endpoint).

    Args:
        text: Text to embed

    Returns:
        Single embedding vector
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return {
        "embedding": embedding.tolist(),
        "dimension": 768,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
