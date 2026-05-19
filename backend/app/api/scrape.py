"""Endpoints para disparar scrapers desde n8n u otros sistemas externos."""

from datetime import datetime, timezone
from typing import Any

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


@router.get("/diagnose")
async def diagnose_scraper(
    source: str = Query("nacional_colombia", description="Scraper a diagnosticar"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict[str, Any]:
    """Diagnostica un scraper: ejecuta sin persistir, devuelve debug info.

    Útil para verificar si el scraper está encontrando oportunidades
    sin necesidad de afectar la base de datos.

    Uso: GET /api/v1/scrape/diagnose?source=nacional_colombia
    """
    _check_api_key(x_api_key)

    if source not in SCRAPERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scraper '{source}'. Valid: {list(SCRAPERS.keys())}",
        )

    started_at = datetime.now(timezone.utc)
    scraper_cls = SCRAPERS[source]
    scraper = scraper_cls()

    try:
        raw_items = await scraper.fetch_raw()
        logger.info(
            "Diagnose: fetch_raw complete",
            scraper=source,
            raw_items=len(raw_items),
        )

        # Normalizar cada item para ver cuáles pasan el filtro
        normalized = []
        rejected = []

        for i, raw in enumerate(raw_items):
            normalized_opp = scraper.normalize(raw)
            if normalized_opp:
                normalized.append({
                    "title": normalized_opp.title,
                    "funder": normalized_opp.funder_name,
                    "url": normalized_opp.url_rfp,
                    "deadline": str(normalized_opp.deadline) if normalized_opp.deadline else None,
                })
            else:
                rejected.append({
                    "title": raw.get("title", "N/A")[:80],
                    "reason": "Failed normalization filter",
                })

        completed_at = datetime.now(timezone.utc)
        duration_sec = (completed_at - started_at).total_seconds()

        return {
            "scraper": source,
            "status": "success",
            "raw_fetched": len(raw_items),
            "normalized_valid": len(normalized),
            "rejected": len(rejected),
            "normalized_sample": normalized[:5],  # Primeros 5 válidos
            "rejected_sample": rejected[:5],  # Primeros 5 rechazados
            "duration_sec": duration_sec,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "note": "No data persisted to database. This is diagnostic only.",
        }

    except Exception as exc:
        logger.error("Diagnose failed", scraper=source, error=str(exc))
        return {
            "scraper": source,
            "status": "error",
            "error": str(exc)[:500],
            "duration_sec": (datetime.now(timezone.utc) - started_at).total_seconds(),
        }


@router.post("/rescore")
async def run_rescorer(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Ejecuta el motor de scoring LLM en oportunidades sin score.

    Llamado por n8n después de que scrapers persistan datos nuevos.
    Devuelve stats para alertas en Slack.
    """
    _check_api_key(x_api_key)

    from app.scrapers.rescore import rescore_batch

    started_at = datetime.now(timezone.utc)

    try:
        result = await rescore_batch()
        completed_at = datetime.now(timezone.utc)
        duration_sec = (completed_at - started_at).total_seconds()

        logger.info(
            "Rescore run complete",
            total=result["total"],
            succeeded=result["succeeded"],
            failed=result["failed"],
            duration_sec=duration_sec,
        )

        return {
            "status": "success",
            "total": result["total"],
            "succeeded": result["succeeded"],
            "failed": result["failed"],
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_sec": duration_sec,
        }

    except Exception as exc:
        logger.error("Rescore failed", error=str(exc))
        return {
            "status": "error",
            "error": str(exc)[:500],
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
