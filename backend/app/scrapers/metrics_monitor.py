"""Monitor de Tasa de Éxito por Scraper — Detecta caídas en oportunidades detectadas.

Trackea cuántas oportunidades cada scraper normaliza por run. Si la tasa cae 50%
respecto al promedio de los últimos 7 días, alertar a Slack inmediatamente.

Ejecutado:
- Inline: después de cada scraper run en runner.py
- Weekly: n8n workflow lunes 8am con resumen
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Any

import httpx
import structlog
from sqlalchemy import select, func, desc
from sqlalchemy.sql import and_

from app.core.database import AsyncSessionLocal

logger = structlog.get_logger()

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Modelo mock para la tabla (en la práctica usarías ORM)
# from app.models.scraper_metrics import ScraperMetrics


async def get_weekly_average(
    scraper_name: str,
    days: int = 7,
    db=None,
) -> float | None:
    """Calcula promedio de oportunidades normalizadas de los últimos N días.

    Retorna:
        Promedio de total_normalized, o None si hay <3 días de datos.
    """
    log = logger.bind(scraper=scraper_name, days=days)

    try:
        async with AsyncSessionLocal() as session:
            # Query: promedio de total_normalized en los últimos N días
            cutoff_date = date.today() - timedelta(days=days)

            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT AVG(total_normalized) as avg_normalized
                    FROM scraper_metrics
                    WHERE scraper_name = :scraper_name
                      AND run_date >= :cutoff_date
                """),
                {"scraper_name": scraper_name, "cutoff_date": cutoff_date}
            )
            row = result.fetchone()

            if not row or row[0] is None:
                log.info("No historical data found")
                return None

            avg = float(row[0])
            log.info("Weekly average calculated", avg=avg)
            return avg

    except Exception as exc:
        log.error("Failed to calculate weekly average", error=str(exc))
        return None


async def detect_drop(
    scraper_name: str,
    today_count: int,
    threshold: float = 0.5,
) -> bool:
    """Detecta si hoy hay una caída significativa en oportunidades detectadas.

    Retorna True si:
      - today_count == 0 (siempre alerta, es un fallo)
      - today_count < avg_7days * threshold (caída significativa)
      - No hay datos históricos (conservative: no alerta)

    Retorna False si:
      - today_count >= avg_7days * threshold (OK)
      - Hay <3 días de datos (no hay baseline)
    """
    log = logger.bind(scraper=scraper_name, today_count=today_count, threshold=threshold)

    # Si hoy == 0, siempre es alerta
    if today_count == 0:
        log.warning("Zero opportunities detected")
        return True

    # Obtener promedio de los últimos 7 días
    avg = await get_weekly_average(scraper_name, days=7)

    if avg is None:
        log.info("No historical baseline, cannot detect drop")
        return False

    # Comparar: today < avg * threshold?
    drop_threshold = avg * threshold
    has_dropped = today_count < drop_threshold

    if has_dropped:
        drop_percent = (1.0 - today_count / avg) * 100
        log.warning(
            "Significant drop detected",
            today=today_count,
            avg=avg,
            threshold=drop_threshold,
            drop_percent=drop_percent,
        )
        return True

    log.info("No significant drop", today=today_count, avg=avg, threshold=drop_threshold)
    return False


async def alert_metrics_drop_to_slack(
    scraper_name: str,
    today_count: int,
    avg_count: float,
) -> bool:
    """Envía alerta a Slack si hay caída en oportunidades detectadas."""
    drop_percent = (1.0 - today_count / avg_count) * 100 if avg_count > 0 else 100.0

    title = f"📉 WARNING: {scraper_name} detection rate dropped"
    fields = [
        {"type": "mrkdwn", "text": f"*Scraper:*\n{scraper_name}"},
        {"type": "mrkdwn", "text": f"*Today:*\n{today_count} opp."},
        {"type": "mrkdwn", "text": f"*7-day avg:*\n{avg_count:.1f} opp."},
        {"type": "mrkdwn", "text": f"*Drop:*\n{drop_percent:.1f}%"},
    ]

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": title},
        },
        {
            "type": "section",
            "fields": fields,
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "→ Check source integrity (HTML, API, filtering rules)",
            },
        },
    ]

    payload = {"blocks": blocks}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(SLACK_WEBHOOK, json=payload, timeout=10)
            resp.raise_for_status()
        logger.info("Slack alert sent", scraper=scraper_name)
        return True
    except Exception as exc:
        logger.error("Failed to send Slack alert", scraper=scraper_name, error=str(exc))
        return False


async def save_scraper_metrics(
    run_result: dict[str, Any],
    db=None,
) -> None:
    """Persiste métricas de un scraper run en tabla scraper_metrics."""
    scraper_name = run_result.get("scraper_name")
    total_normalized = run_result.get("total_normalized", 0)
    total_persisted = run_result.get("total_persisted", 0)
    total_skipped = run_result.get("total_skipped", 0)
    errors_count = run_result.get("errors_count", 0)
    duration_sec = run_result.get("duration_sec", 0.0)
    run_date = run_result.get("run_date", date.today())

    log = logger.bind(
        action="save_scraper_metrics",
        scraper=scraper_name,
        total_normalized=total_normalized,
    )

    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text

            await session.execute(
                text("""
                    INSERT INTO scraper_metrics
                    (scraper_name, run_date, total_normalized, total_persisted,
                     total_skipped, errors_count, run_duration_sec, created_at)
                    VALUES (:scraper, :date, :norm, :pers, :skip, :err, :dur, NOW())
                """),
                {
                    "scraper": scraper_name,
                    "date": run_date,
                    "norm": total_normalized,
                    "pers": total_persisted,
                    "skip": total_skipped,
                    "err": errors_count,
                    "dur": duration_sec,
                },
            )
            await session.commit()
            log.info("Scraper metrics saved")

    except Exception as exc:
        log.error("Failed to save metrics", error=str(exc))


async def get_weekly_summary() -> dict[str, Any]:
    """Obtiene resumen semanal de todos los scrapers.

    Retorna:
        {
            "summary_date": "2026-06-01",
            "scrapers": {
                "grantsgov": {
                    "last_7_days": {...},
                    "today": {...},
                    "trend": "up" | "down" | "stable"
                },
                ...
            }
        }
    """
    log = logger.bind(action="get_weekly_summary")

    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text

            # Query de resumen últimos 7 días + hoy
            result = await session.execute(
                text("""
                    SELECT
                      scraper_name,
                      AVG(total_normalized) as avg_7d,
                      MIN(total_normalized) as min_7d,
                      MAX(total_normalized) as max_7d,
                      (SELECT total_normalized FROM scraper_metrics
                       WHERE scraper_name = sm.scraper_name
                       AND run_date = CURRENT_DATE
                       ORDER BY created_at DESC LIMIT 1) as today_normalized
                    FROM scraper_metrics sm
                    WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY scraper_name
                    ORDER BY scraper_name
                """)
            )

            summary = {
                "summary_date": date.today().isoformat(),
                "summary_time": datetime.utcnow().isoformat() + "Z",
                "scrapers": {},
            }

            for row in result:
                scraper_name, avg_7d, min_7d, max_7d, today_normalized = row

                # Determinar tendencia
                if today_normalized is None:
                    trend = "no_run_today"
                elif today_normalized > avg_7d:
                    trend = "up"
                elif today_normalized < avg_7d * 0.8:
                    trend = "down"
                else:
                    trend = "stable"

                summary["scrapers"][scraper_name] = {
                    "avg_7d": int(avg_7d) if avg_7d else 0,
                    "min_7d": int(min_7d) if min_7d else 0,
                    "max_7d": int(max_7d) if max_7d else 0,
                    "today": int(today_normalized) if today_normalized else 0,
                    "trend": trend,
                }

            log.info("Weekly summary generated", scraper_count=len(summary["scrapers"]))
            return summary

    except Exception as exc:
        log.error("Failed to generate weekly summary", error=str(exc))
        return {
            "summary_date": date.today().isoformat(),
            "error": str(exc),
            "scrapers": {},
        }
