from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import contacts, dashboard, opportunities, rag, scoring, scrape
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
    allow_origins=["http://localhost:3000", settings.NEXT_PUBLIC_API_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(scoring.router, prefix="/api/v1/opportunities", tags=["scoring"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["contacts"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(scrape.router, prefix="/api/v1/scrape", tags=["scrape"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
