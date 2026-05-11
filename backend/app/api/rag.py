from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.rag_pipeline import RAGPipeline

router = APIRouter()


class RAGQuery(BaseModel):
    query: str
    filters: dict | None = None
    top_k: int = 5


class RAGResult(BaseModel):
    query: str
    results: list[dict]
    total_found: int


@router.post("/query", response_model=RAGResult)
async def semantic_query(body: RAGQuery, db: AsyncSession = Depends(get_db)) -> RAGResult:
    pipeline = RAGPipeline(db)
    results = await pipeline.query(body.query, filters=body.filters, top_k=body.top_k)
    return RAGResult(query=body.query, results=results, total_found=len(results))
