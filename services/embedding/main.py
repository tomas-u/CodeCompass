"""Embedding microservice using sentence-transformers."""

import os
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CodeCompass Embedding Service",
    description="Embedding service using sentence-transformers",
    version="0.1.0",
)

# Load model on startup
model_name = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
model: SentenceTransformer | None = None


class EmbedRequest(BaseModel):
    """Request to embed texts."""
    texts: List[str]


class EmbedResponse(BaseModel):
    """Response with embeddings."""
    embeddings: List[List[float]]
    model: str
    dimensions: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model: str
    dimensions: int


@app.on_event("startup")
async def load_model():
    """Load the embedding model on startup."""
    global model
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"Model loaded successfully. Dimensions: {model.get_sentence_embedding_dimension()}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """Generate embeddings for a list of texts."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")

    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per request")

    try:
        embeddings = model.encode(request.texts).tolist()
        return EmbedResponse(
            embeddings=embeddings,
            model=model_name,
            dimensions=model.get_sentence_embedding_dimension(),
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return HealthResponse(
        status="healthy",
        model=model_name,
        dimensions=model.get_sentence_embedding_dimension(),
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "embedding", "version": "0.1.0"}
