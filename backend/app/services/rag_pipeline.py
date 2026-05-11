"""Pipeline RAG: consulta semántica sobre oportunidades usando pgvector."""

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger()


class RAGPipeline:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._embedder = EmbeddingService()

    async def query(
        self,
        query_text: str,
        filters: dict | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        query_embedding = await self._embedder.embed_query(query_text)

        if query_embedding is None:
            # Fallback: búsqueda por keywords si no hay embeddings
            return await self._keyword_search(query_text, top_k)

        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        sql = text("""
            SELECT id, title, description, score_total, decision, url_rfp, source_name,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM opportunities
            WHERE embedding IS NOT NULL
              AND (:decision IS NULL OR decision = :decision)
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        decision_filter = (filters or {}).get("decision")
        result = await self._db.execute(
            sql,
            {"embedding": embedding_str, "decision": decision_filter, "top_k": top_k},
        )
        rows = result.mappings().all()

        return [
            {
                "id": str(row["id"]),
                "title": row["title"],
                "description": (row["description"] or "")[:300],
                "score_total": row["score_total"],
                "decision": row["decision"],
                "url_rfp": row["url_rfp"],
                "source_name": row["source_name"],
                "similarity": round(float(row["similarity"]), 4),
            }
            for row in rows
        ]

    async def _keyword_search(self, query_text: str, top_k: int) -> list[dict]:
        terms = query_text.lower().split()
        q = select(Opportunity).order_by(Opportunity.score_total.desc().nullslast()).limit(top_k)
        rows = (await self._db.execute(q)).scalars().all()
        return [
            {
                "id": str(opp.id),
                "title": opp.title,
                "description": (opp.description or "")[:300],
                "score_total": opp.score_total,
                "decision": opp.decision,
                "url_rfp": opp.url_rfp,
                "source_name": opp.source_name,
                "similarity": None,
            }
            for opp in rows
            if any(t in (opp.title or "").lower() for t in terms)
        ]
