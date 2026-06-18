"""API endpoints para monitoreo de scrapers y endpoints de API.

Endpoints de monitoreo HTML:
  GET  /api/v1/monitor/health                    # Estado actual de todos los scrapers
  GET  /api/v1/monitor/validate/{source_name}   # Validar selectores de una fuente
  POST /api/v1/monitor/run                       # Ejecutar monitor completo (n8n trigger)
  GET  /api/v1/monitor/log                       # Histórico de monitoreos

Endpoints de monitoreo de APIs:
  GET  /api/v1/monitor/endpoints/health          # Estado actual de todos los endpoints
  GET  /api/v1/monitor/endpoints/validate/{endpoint_name}  # Validar endpoint específico
  POST /api/v1/monitor/endpoints/run             # Ejecutar monitor completo (n8n trigger)
  GET  /api/v1/monitor/endpoints/log             # Histórico de monitoreos
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
from app.scrapers.utils.endpoint_monitor import (
    run_all_endpoint_monitors,
    validate_endpoint,
    alert_to_slack as endpoint_alert_to_slack,
    persist_endpoint_log,
)
from app.scrapers.metrics_monitor import (
    get_weekly_summary,
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


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE MONITOREO DE APIS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/endpoints/health")
async def endpoints_health() -> dict[str, Any]:
    """Retorna estado de salud de todos los endpoints de API basado en últimos monitoreos."""
    results = await run_all_endpoint_monitors()
    summary = {
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "overall_status": "healthy",
        "endpoints": {},
    }

    for result in results:
        endpoint = result["endpoint_name"]
        status = result["status"]
        summary["endpoints"][endpoint] = {
            "status": status,
            "url": result.get("url"),
            "http_status_code": result.get("http_status_code"),
            "latency_ms": result.get("latency_ms"),
            "checked_at": result.get("checked_at"),
        }

        if status == "failed":
            summary["overall_status"] = "critical"
        elif status == "degraded" and summary["overall_status"] != "critical":
            summary["overall_status"] = "warning"

    return summary


@router.get("/endpoints/validate/{endpoint_name}")
async def validate_endpoint_endpoint(endpoint_name: str) -> dict[str, Any]:
    """Valida un endpoint específico."""
    result = await validate_endpoint(endpoint_name)

    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result.get("error", "Validation failed"))

    return result


@router.post("/endpoints/run")
async def run_endpoints_monitor() -> dict[str, Any]:
    """Ejecuta monitoreo completo de todos los endpoints de API.

    Triggered por n8n hourly-endpoint-monitor workflow cada hora.
    Retorna resultados y envía alertas a Slack si hay problemas.
    """
    log = logger.bind(action="run_endpoints_monitor")
    log.info("Endpoint monitor run started")

    results = await run_all_endpoint_monitors()
    alerts_sent = 0
    failed_endpoints = []

    async with AsyncSessionLocal() as db:
        for result in results:
            # Persistir en BD
            await persist_endpoint_log(result, db)

            # Alerta a Slack si status != healthy
            if result["status"] != "healthy":
                sent = await endpoint_alert_to_slack(result)
                if sent:
                    alerts_sent += 1
                failed_endpoints.append(result["endpoint_name"])

    summary = {
        "run_at": datetime.utcnow().isoformat() + "Z",
        "total_checked": len(results),
        "failed": len(failed_endpoints),
        "failed_endpoints": failed_endpoints,
        "alerts_sent": alerts_sent,
        "status": "critical" if failed_endpoints else "ok",
    }

    log.info("Endpoint monitor run completed", **summary)
    return summary


@router.get("/endpoints/log")
async def endpoints_monitor_log(
    endpoint_name: str | None = Query(None),
    status: str | None = Query(None),
    days: int = Query(7, ge=1, le=30),
) -> list[dict[str, Any]]:
    """Retorna histórico de monitoreos de endpoints.

    Parámetros:
      ?endpoint_name=grantsgov_api  # Filtrar por endpoint
      ?status=failed                # Filtrar por estado
      ?days=7                       # Últimos N días (default 7)

    Ejemplo:
      GET /api/v1/monitor/endpoints/log?endpoint_name=grantsgov_api&status=failed&days=14
    """
    # TODO: Implementar cuando tabla endpoint_monitor_log esté disponible
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE MONITOREO DE MÉTRICAS DE SCRAPERS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/metrics/summary")
async def metrics_summary() -> dict[str, Any]:
    """Retorna resumen semanal de tasas de éxito de todos los scrapers.

    Usado por:
      - n8n weekly-metrics-summary workflow (lunes 8am)
      - Dashboard Metabase
      - Análisis de tendencias
    """
    summary = await get_weekly_summary()
    return summary


@router.get("/metrics/history/{scraper_name}")
async def metrics_history(
    scraper_name: str,
    days: int = Query(30, ge=1, le=90),
) -> dict[str, Any]:
    """Retorna histórico de métricas para un scraper específico.

    Parámetros:
      ?days=30  # Últimos N días (default 30)

    Ejemplo:
      GET /api/v1/monitor/metrics/history/grantsgov?days=30
    """
    from datetime import date, timedelta

    try:
        async with AsyncSessionLocal() as db:
            cutoff_date = date.today() - timedelta(days=days)

            from sqlalchemy import text

            result = await db.execute(
                text("""
                    SELECT
                      run_date,
                      total_normalized,
                      total_persisted,
                      total_skipped,
                      errors_count,
                      run_duration_sec
                    FROM scraper_metrics
                    WHERE scraper_name = :scraper_name
                      AND run_date >= :cutoff_date
                    ORDER BY run_date DESC
                """),
                {"scraper_name": scraper_name, "cutoff_date": cutoff_date},
            )

            history = []
            for row in result:
                run_date, normalized, persisted, skipped, errors, duration = row
                history.append(
                    {
                        "run_date": run_date.isoformat(),
                        "total_normalized": normalized,
                        "total_persisted": persisted,
                        "total_skipped": skipped,
                        "errors_count": errors,
                        "run_duration_sec": round(duration, 2),
                    }
                )

            return {
                "scraper_name": scraper_name,
                "days": days,
                "total_runs": len(history),
                "history": history,
            }

    except Exception as exc:
        logger.error("Failed to fetch metrics history", scraper=scraper_name, error=str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(exc)}")


@router.get("/metrics/drop-alerts")
async def metrics_drop_alerts() -> dict[str, Any]:
    """Retorna lista de scrapers que hoy tuvieron caída significativa en detección.

    Útil para dashboards en tiempo real — qué scrapers necesitan atención ahora.
    """
    from datetime import date, timedelta

    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text

            # Query: comparar hoy vs promedio últimos 7 días
            result = await db.execute(
                text("""
                    SELECT
                      scraper_name,
                      (SELECT total_normalized FROM scraper_metrics
                       WHERE scraper_name = sm.scraper_name
                       AND run_date = CURRENT_DATE
                       ORDER BY created_at DESC LIMIT 1) as today_normalized,
                      AVG(total_normalized) as avg_7d
                    FROM scraper_metrics sm
                    WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY scraper_name
                    HAVING (SELECT total_normalized FROM scraper_metrics
                           WHERE scraper_name = sm.scraper_name
                           AND run_date = CURRENT_DATE
                           ORDER BY created_at DESC LIMIT 1) IS NOT NULL
                """)
            )

            alerts = []
            for row in result:
                scraper_name, today, avg_7d = row

                if today is None or avg_7d is None:
                    continue

                # Detectar caída: today < avg*0.5
                if today == 0 or today < avg_7d * 0.5:
                    drop_percent = (1.0 - today / avg_7d) * 100 if avg_7d > 0 else 100.0
                    alerts.append(
                        {
                            "scraper_name": scraper_name,
                            "today": today,
                            "avg_7d": int(avg_7d),
                            "drop_percent": round(drop_percent, 1),
                            "severity": "critical" if today == 0 else "warning",
                        }
                    )

            return {
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "total_alerts": len(alerts),
                "alerts": sorted(alerts, key=lambda x: x["drop_percent"], reverse=True),
            }

    except Exception as exc:
        logger.error("Failed to fetch drop alerts", error=str(exc))
        return {
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "error": str(exc),
            "alerts": [],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN CONSOLIDADO DE MONITOREO (Task 5 - Daily Check)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/daily-summary")
async def daily_summary(quick: bool = Query(False)) -> dict[str, Any]:
    """Resumen consolidado de toda la infraestructura de monitoreo.

    Agregación de:
      - HTML structure monitors (bid, unwomen, developmentaid)
      - API endpoint monitors (grantsgov, SECOP, RSS feeds)
      - Scraper success rate monitors (drops detectados hoy)

    Parámetro:
      ?quick=true  # Solo consulta BD (sin re-validar endpoints en vivo)

    Usado por: n8n daily-scraper-check workflow @ 6:15am

    Retorna status consolidado: "critical" | "warning" | "ok"
    """
    log = logger.bind(action="daily_summary", quick=quick)
    log.info("Daily summary requested")

    checked_at = datetime.utcnow().isoformat() + "Z"
    html_status = "ok"
    html_failed = []
    endpoint_status = "ok"
    endpoint_failed = []
    metrics_status = "ok"
    metrics_drops = []

    # 1. HTML Monitor Status (si quick=True, consultar BD; si False, ejecutar validación)
    if quick:
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import text
                result = await db.execute(
                    text("""
                        SELECT source_name, status FROM scraper_monitor_log
                        WHERE checked_at >= NOW() - INTERVAL '24 hours'
                        AND (status = 'failed' OR status = 'degraded')
                        ORDER BY checked_at DESC
                    """)
                )
                for row in result:
                    source_name, status = row
                    if status == "failed":
                        html_status = "critical"
                        html_failed.append(source_name)
                    elif status == "degraded" and html_status != "critical":
                        html_status = "warning"
        except Exception as exc:
            log.warning("HTML monitor BD check failed", error=str(exc))
    else:
        # Ejecutar validación en vivo
        html_results = await run_all_monitors()
        for result in html_results:
            if result["status"] == "failed":
                html_status = "critical"
                html_failed.append(result["source"])
            elif result["status"] == "degraded" and html_status != "critical":
                html_status = "warning"

    # 2. Endpoint Monitor Status
    if quick:
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import text
                result = await db.execute(
                    text("""
                        SELECT endpoint_name, status FROM endpoint_monitor_log
                        WHERE checked_at >= NOW() - INTERVAL '24 hours'
                        AND (status = 'failed' OR status = 'degraded')
                        ORDER BY checked_at DESC
                    """)
                )
                for row in result:
                    endpoint_name, status = row
                    if status == "failed":
                        endpoint_status = "critical"
                        endpoint_failed.append(endpoint_name)
                    elif status == "degraded" and endpoint_status != "critical":
                        endpoint_status = "warning"
        except Exception as exc:
            log.warning("Endpoint monitor BD check failed", error=str(exc))
    else:
        # Ejecutar validación en vivo
        endpoint_results = await run_all_endpoint_monitors()
        for result in endpoint_results:
            if result["status"] == "failed":
                endpoint_status = "critical"
                endpoint_failed.append(result["endpoint_name"])
            elif result["status"] == "degraded" and endpoint_status != "critical":
                endpoint_status = "warning"

    # 3. Scraper Metrics Status (siempre de BD)
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            result = await db.execute(
                text("""
                    SELECT
                      scraper_name,
                      (SELECT total_normalized FROM scraper_metrics
                       WHERE scraper_name = sm.scraper_name
                       AND run_date = CURRENT_DATE
                       ORDER BY created_at DESC LIMIT 1) as today_normalized,
                      AVG(total_normalized) as avg_7d
                    FROM scraper_metrics sm
                    WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY scraper_name
                    HAVING (SELECT total_normalized FROM scraper_metrics
                           WHERE scraper_name = sm.scraper_name
                           AND run_date = CURRENT_DATE
                           ORDER BY created_at DESC LIMIT 1) IS NOT NULL
                """)
            )
            for row in result:
                scraper_name, today, avg_7d = row
                if today is None or avg_7d is None:
                    continue
                if today == 0 or today < avg_7d * 0.5:
                    drop_percent = (1.0 - today / avg_7d) * 100 if avg_7d > 0 else 100.0
                    severity = "critical" if today == 0 else "warning"
                    if severity == "critical":
                        metrics_status = "critical"
                    elif severity == "warning" and metrics_status != "critical":
                        metrics_status = "warning"
                    metrics_drops.append({
                        "scraper_name": scraper_name,
                        "today": today,
                        "avg_7d": int(avg_7d),
                        "drop_percent": round(drop_percent, 1),
                        "severity": severity,
                    })
    except Exception as exc:
        log.warning("Metrics check failed", error=str(exc))

    # 4. Consolidate overall status
    overall_status = "ok"
    if html_status == "critical" or endpoint_status == "critical" or metrics_status == "critical":
        overall_status = "critical"
    elif html_status == "warning" or endpoint_status == "warning" or metrics_status == "warning":
        overall_status = "warning"

    # 5. Build response
    response = {
        "checked_at": checked_at,
        "overall_status": overall_status,
        "html_monitors": {
            "status": html_status,
            "failed_sources": html_failed,
        },
        "endpoint_monitors": {
            "status": endpoint_status,
            "failed_endpoints": endpoint_failed,
        },
        "metrics": {
            "status": metrics_status,
            "drop_alerts": metrics_drops,
        },
    }

    # Summary text for logging/debugging
    issue_count = len(html_failed) + len(endpoint_failed) + len(metrics_drops)
    response["summary_text"] = (
        f"{issue_count} issue(s) detected" if issue_count > 0 else "All systems OK"
    )

    log.info("Daily summary completed", status=overall_status, issues=issue_count)
    return response
