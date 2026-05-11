"""Servicio de embeddings usando Google Gemini text-embedding-004.

Dimensión de salida: 768. Los embeddings se cachean en la tabla opportunities.embedding.
NO recalcular si ya existe — ver regla en CLAUDE.md.
"""

import structlog
import google.generativeai as genai

from app.core.config import settings

logger = structlog.get_logger()

EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIMENSION = 768


class EmbeddingService:
    def __init__(self) -> None:
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        else:
            logger.warning("GOOGLE_API_KEY not set — embeddings disabled")

    async def embed(self, text: str) -> list[float] | None:
        if not settings.GOOGLE_API_KEY:
            return None

        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text[:8000],  # Límite de tokens del modelo
                task_type="RETRIEVAL_DOCUMENT",
            )
            embedding: list[float] = result["embedding"]
            if len(embedding) != EMBEDDING_DIMENSION:
                logger.warning(
                    "Unexpected embedding dimension",
                    expected=EMBEDDING_DIMENSION,
                    got=len(embedding),
                )
            return embedding
        except Exception as exc:
            logger.error("Embedding failed", error=str(exc))
            return None

    async def embed_query(self, text: str) -> list[float] | None:
        if not settings.GOOGLE_API_KEY:
            return None

        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type="RETRIEVAL_QUERY",
            )
            return result["embedding"]
        except Exception as exc:
            logger.error("Query embedding failed", error=str(exc))
            return None
