from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, contacts, dashboard, funders, monitor, opportunities, organizations, rag, scoring, scrape, tenders
from app.core.config import settings
from app.core.database import engine
from app.models import Base

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GrantFlow AI starting", environment=settings.ENVIRONMENT)
    yield
    await engine.dispose()
    logger.info("GrantFlow AI stopped")


app = FastAPI(
    title="GrantFlow AI",
    description="Sistema de inteligencia comercial para prospección de grants — aeioTU",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", settings.NEXT_PUBLIC_API_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(scoring.router, prefix="/api/v1/opportunities", tags=["scoring"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(funders.router, prefix="/api/v1/funders", tags=["funders"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["contacts"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(tenders.router, prefix="/api/v1/tenders", tags=["tenders"])
app.include_router(monitor.router, tags=["monitor"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(scrape.router, prefix="/api/v1/scrape", tags=["scrape"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/debug/opportunities")
async def debug_opportunities() -> dict:
    """DEBUG ONLY - Sin autenticación para desarrollo."""
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import engine
    from app.models.opportunity import Opportunity

    async with AsyncSession(engine) as session:
        result = await session.execute(select(Opportunity).limit(25))
        opps = result.scalars().all()
        return {
            "total": len(opps),
            "items": [
                {
                    "id": str(o.id),
                    "title": o.title,
                    "decision": o.decision,
                    "score": o.score_total,
                }
                for o in opps
            ],
        }
