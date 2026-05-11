"""Servicio de embeddings usando Google Gemini text-embedding-004.

Dimensión de salida: 768. Los embeddings se cachean en la tabla opportunities.embedding.
NO recalcular si ya existe — ver regla en CLAUDE.md.
"""

import structlog
from google import genai
from google.genai import types

from app.core.config import settings

logger = structlog.get_logger()

EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIMENSION = 768


class EmbeddingService:
    def __init__(self) -> None:
        self._client: genai.Client | None = None
        if settings.GOOGLE_API_KEY:
            self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        else:
            logger.warning("GOOGLE_API_KEY not set — embeddings disabled")

    async def embed(self, text: str) -> list[float] | None:
        if not self._client:
            return None

        try:
            result = await self._client.aio.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text[:8000],
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            embedding: list[float] = result.embeddings[0].values
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
        if not self._client:
            return None

        try:
            result = await self._client.aio.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
            )
            return result.embeddings[0].values
        except Exception as exc:
            logger.error("Query embedding failed", error=str(exc))
            return None
