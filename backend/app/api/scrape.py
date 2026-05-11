"""Endpoints para disparar scrapers desde n8n u otros sistemas externos."""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings
from app.scrapers.runner import SCRAPERS, run_scraper

logger = structlog.get_logger()
router = APIRouter()


def _check_api_key(x_api_key: str | None) -> None:
    """Verifica X-API-Key contra GRANTFLOW_API_KEY si está configurada.

    Si la variable no está en .env, el endpoint queda abierto (dev).
    """
    expected = settings.GRANTFLOW_API_KEY
    if not expected:
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/run")
async def run_all_scrapers(
    source: str | None = Query(None, description="Nombre del scraper. Vacío = todos"),
    score: bool = Query(False, description="Scorear con LLM al persistir"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Ejecuta scrapers y persiste oportunidades nuevas.

    Llamado por n8n diariamente. Devuelve stats agregados para que el workflow
    pueda decidir si notificar éxito/error.
    """
    _check_api_key(x_api_key)

    if source and source not in SCRAPERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scraper '{source}'. Valid: {list(SCRAPERS.keys())}",
        )

    started_at = datetime.now(timezone.utc)
    targets = [source] if source else list(SCRAPERS.keys())
    per_source: dict[str, int] = {}
    total = 0
    errors: list[str] = []

    for name in targets:
        try:
            count = await run_scraper(name, do_score=score)
            per_source[name] = count
            total += count
        except Exception as exc:
            msg = str(exc)[:200]
            logger.error("Scraper crashed", scraper=name, error=msg)
            per_source[name] = 0
            errors.append(f"{name}: {msg}")

    completed_at = datetime.now(timezone.utc)
    duration_sec = (completed_at - started_at).total_seconds()

    logger.info(
        "Scrape run complete",
        total_persisted=total,
        sources=per_source,
        duration_sec=duration_sec,
        errors=len(errors),
    )

    return {
        "total_persisted": total,
        "per_source": per_source,
        "errors": errors,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_sec": duration_sec,
    }


@router.get("/sources")
async def list_sources(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Lista los scrapers disponibles para invocar."""
    _check_api_key(x_api_key)
    return {"sources": list(SCRAPERS.keys())}
