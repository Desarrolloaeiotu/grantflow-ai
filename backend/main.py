from contextlib import asynccontextmanager
import json

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

from app.api import chat, contacts, dashboard, funders, monitor, opportunities, organizations, rag, scoring, scrape, scrapers_api, tenders
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


# CORS middleware function
async def cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600",
            },
        )

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# Add middleware
from starlette.middleware.base import BaseHTTPMiddleware
app.add_middleware(BaseHTTPMiddleware, dispatch=cors_middleware)

app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(scoring.router, prefix="/api/v1/opportunities", tags=["scoring"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(funders.router, prefix="/api/v1/funders", tags=["funders"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["contacts"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(tenders.router, prefix="/api/v1/tenders", tags=["tenders"])
app.include_router(scrapers_api.router, prefix="/api/v1", tags=["scrapers"])
app.include_router(monitor.router, tags=["monitor"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(scrape.router, prefix="/api/v1/scrape", tags=["scrape"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


@app.get("/health")
async def health() -> Response:
    content = {"status": "ok", "version": "0.1.0"}
    return Response(
        content=json.dumps(content),
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


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
