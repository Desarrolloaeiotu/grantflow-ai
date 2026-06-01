"""API endpoints para monitoreo de scrapers.

Endpoints:
  GET  /api/v1/monitor/health                    # Estado actual de todos los scrapers
  GET  /api/v1/monitor/validate/{source_name}   # Validar selectores de una fuente
  POST /api/v1/monitor/run                       # Ejecutar monitor completo (n8n trigger)
  GET  /api/v1/monitor/log                       # Histórico de monitoreos
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc

from app.core.database import AsyncSessionLocal
from app.models.opportunity import Opportunity
from app.scrapers.scraper_monitor import (
    run_all_monitors,
    validate_selectors,
    alert_to_slack,
    persist_monitor_log,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])


@router.get("/health")
async def monitor_health() -> dict[str, Any]:
    """Retorna estado de salud de todos los scrapers basado en últimos monitoreos."""
    async with AsyncSessionLocal() as db:
        # TODO: Consultar tabla scraper_monitor_log y retornar status
        # Por ahora retorna validación en vivo
        pass

    results = await run_all_monitors()
    summary = {
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "overall_status": "healthy",
        "sources": {},
    }

    for result in results:
        source = result["source"]
        status = result["status"]
        summary["sources"][source] = {
            "status": status,
            "url": result.get("url"),
            "checked_at": result.get("checked_at"),
        }

        if status == "failed":
            summary["overall_status"] = "critical"
        elif status == "degraded" and summary["overall_status"] != "critical":
            summary["overall_status"] = "warning"

    return summary


@router.get("/validate/{source_name}")
async def validate_source(source_name: str) -> dict[str, Any]:
    """Valida selectores de una fuente específica."""
    result = await validate_selectors(source_name)

    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result.get("error", "Validation failed"))

    return result


@router.post("/run")
async def run_monitor() -> dict[str, Any]:
    """Ejecuta monitoreo completo de todas las fuentes.

    Triggered por n8n daily-monitor-html workflow 30min antes de cada scraper.
    Retorna resultados y envía alertas a Slack si hay problemas.
    """
    log = logger.bind(action="run_monitor")
    log.info("Monitor run started")

    results = await run_all_monitors()
    alerts_sent = 0
    failed_sources = []

    async with AsyncSessionLocal() as db:
        for result in results:
            # Persistir en BD
            await persist_monitor_log(result, db)

            # Alerta a Slack si status != healthy
            if result["status"] != "healthy":
                sent = await alert_to_slack(result)
                if sent:
                    alerts_sent += 1
                failed_sources.append(result["source"])

    summary = {
        "run_at": datetime.utcnow().isoformat() + "Z",
        "total_checked": len(results),
        "failed": len(failed_sources),
        "failed_sources": failed_sources,
        "alerts_sent": alerts_sent,
        "status": "critical" if failed_sources else "ok",
    }

    log.info("Monitor run completed", **summary)
    return summary


@router.get("/log")
async def monitor_log(
    source_name: str | None = Query(None),
    status: str | None = Query(None),
    days: int = Query(7, ge=1, le=30),
) -> list[dict[str, Any]]:
    """Retorna histórico de monitoreos.

    Parámetros:
      ?source_name=bid           # Filtrar por fuente
      ?status=failed             # Filtrar por estado
      ?days=7                    # Últimos N días (default 7)

    Ejemplo:
      GET /api/v1/monitor/log?source_name=bid&status=failed&days=14
    """
    # TODO: Implementar cuando tabla scraper_monitor_log esté disponible
    return []
