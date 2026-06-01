"""Monitor de Estructura HTML — Detecta cambios en selectores CSS.

Valida que los selectores CSS de scrapers HTML (bid, unwomen, developmentaid)
siguen encontrando elementos. Si un selector deja de encontrar datos,
alertar a Slack inmediatamente.

Schedule: 30min antes de cada scraper (4:30am, 6:30am, 7:30am, 8:30am, 9:30am)
Ejecución: Via n8n daily-monitor-html workflow
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityCreate

logger = structlog.get_logger()

MONITOR_CONFIG_PATH = "config/scraper_selectors.json"
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"


@dataclass(frozen=True)
class SelectorConfig:
    """Configuración de selectores para una fuente HTML."""
    source_name: str
    url: str
    selectors: dict[str, str]  # {element_type: "css_selector", ...}
    funder_hint: str | None = None
    user_agent: str = "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"
    timeout_sec: int = 15


# Configuración centralizada de selectores CSS por fuente
SELECTOR_CONFIGS: dict[str, SelectorConfig] = {
    "bid": SelectorConfig(
        source_name="bid",
        url="https://bidlab.org/es/convocatorias",
        selectors={
            "card": "article, .views-row, .card, li",  # contenedor principal
            "title": "h1, h2, h3, h4",  # título dentro del card
            "link": "a[href]",  # enlace
            "description": "p, .description, .snippet",  # descripción opcional
        },
        funder_hint="BID",
    ),
    "unwomen": SelectorConfig(
        source_name="unwomen",
        url="https://www.unwomen.org/en/get-involved/grants",
        selectors={
            "card": "article, .views-row, .news-item, .card, li",
            "title": "h1, h2, h3, h4",
            "link": "a[href]",
            "description": "p, .excerpt, .summary",
        },
        funder_hint="UN Women",
    ),
    "developmentaid": SelectorConfig(
        source_name="developmentaid",
        url="https://www.developmentaid.org/news-stream/grants",
        selectors={
            "card": "article, .card, .news-item, .news-card, .item",
            "title": "h1, h2, h3, h4",
            "link": "a[href]",
            "description": "p, .snippet, .excerpt",
        },
        funder_hint="Development Aid",
    ),
}


async def validate_selectors(source_name: str) -> dict[str, Any]:
    """Valida que los selectores de una fuente siguen encontrando elementos.

    Retorna:
        {
            "source": "bid",
            "url": "...",
            "status": "healthy" | "degraded" | "failed",
            "results": {
                "card": {"found": 5, "expected_min": 3, "status": "ok"},
                "title": {"found": 8, "expected_min": 3, "status": "ok"},
                ...
            },
            "error": None | "mensaje error",
            "checked_at": "2026-06-01T04:32:00Z"
        }
    """
    config = SELECTOR_CONFIGS.get(source_name)
    if not config:
        return {
            "source": source_name,
            "status": "failed",
            "error": f"Unknown source: {source_name}",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

    log = logger.bind(source=source_name, url=config.url)

    try:
        async with httpx.AsyncClient(
            timeout=config.timeout_sec,
            headers={"User-Agent": config.user_agent},
            follow_redirects=True,
        ) as client:
            resp = await client.get(config.url)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.error("HTML fetch failed", error=str(exc), status_code=getattr(exc.response, 'status_code', 'N/A'))
        return {
            "source": source_name,
            "status": "failed",
            "error": f"HTTP error: {exc}",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

    soup = BeautifulSoup(resp.text, "lxml")
    results = {}
    overall_status = "healthy"

    # Validar cada selector
    for element_type, selector in config.selectors.items():
        try:
            elements = soup.select(selector)
            found_count = len(elements)
            expected_min = 3  # Mínimo esperado para considerar "ok"

            element_status = "ok" if found_count >= expected_min else "warning"
            if element_status == "warning":
                overall_status = "degraded"

            results[element_type] = {
                "selector": selector,
                "found": found_count,
                "expected_min": expected_min,
                "status": element_status,
            }
            log.info(f"Selector {element_type} validated", found=found_count, status=element_status)
        except Exception as exc:
            log.error(f"Selector {element_type} failed", selector=selector, error=str(exc))
            results[element_type] = {
                "selector": selector,
                "found": 0,
                "expected_min": 3,
                "status": "failed",
                "error": str(exc)[:100],
            }
            overall_status = "failed"

    # Si algún selector crítico (card, title) falla, es crítico
    if results.get("card", {}).get("status") == "failed" or results.get("title", {}).get("status") == "failed":
        overall_status = "failed"

    return {
        "source": source_name,
        "url": config.url,
        "status": overall_status,
        "results": results,
        "error": None,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }


async def run_all_monitors() -> list[dict[str, Any]]:
    """Ejecuta validación de selectores para todas las fuentes."""
    log = logger.bind(action="run_all_monitors")
    results = []

    for source_name in SELECTOR_CONFIGS.keys():
        result = await validate_selectors(source_name)
        results.append(result)

        # Log result
        if result["status"] == "failed":
            log.error("Monitor failed", source=source_name, error=result.get("error"))
        elif result["status"] == "degraded":
            log.warning("Monitor degraded", source=source_name)
        else:
            log.info("Monitor healthy", source=source_name)

    return results


async def alert_to_slack(result: dict[str, Any]) -> bool:
    """Envía alerta a Slack si hay problema detectado.

    Solo alerta si status == "degraded" o "failed".
    """
    if result["status"] == "healthy":
        return True

    source = result["source"]
    status = result["status"]
    error = result.get("error")

    # Construir mensaje
    if status == "failed":
        color = "danger"  # Rojo
        title = f"🚨 CRITICAL: {source.upper()} scraper monitor failed"
    else:
        color = "warning"  # Amarillo
        title = f"⚠️ WARNING: {source.upper()} scraper monitor degraded"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": title},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Source:*\n{source}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{status.upper()}"},
                {"type": "mrkdwn", "text": f"*URL:*\n{result.get('url', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*Checked:*\n{result.get('checked_at', 'N/A')}"},
            ],
        },
    ]

    # Detalles de selectores fallidos
    if result.get("results"):
        failed_selectors = []
        for elem_type, elem_result in result["results"].items():
            if elem_result.get("status") != "ok":
                failed_selectors.append(
                    f"• *{elem_type}*: {elem_result.get('found', 0)} found "
                    f"(expected ≥{elem_result.get('expected_min', 3)})"
                )

        if failed_selectors:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Failed Selectors:*\n" + "\n".join(failed_selectors),
                },
            })

    if error:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error}```"},
        })

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "→ Check GrantFlow dashboard or logs for details.",
        },
    })

    payload = {"blocks": blocks}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(SLACK_WEBHOOK, json=payload, timeout=10)
            resp.raise_for_status()
        logger.info("Slack alert sent", source=source, status=status)
        return True
    except Exception as exc:
        logger.error("Failed to send Slack alert", source=source, error=str(exc))
        return False


async def persist_monitor_log(
    result: dict[str, Any],
    db = None
) -> None:
    """Persiste histórico de monitors en tabla scraper_monitor_log (nueva).

    Facilita tracking: ¿cuándo falló?, ¿qué selectores?, tendencias.
    """
    # TODO: Crear tabla scraper_monitor_log en BD (Sprint S7.2)
    # Por ahora solo log estructurado
    logger.info(
        "Monitor log persisted",
        source=result["source"],
        status=result["status"],
        checked_at=result["checked_at"],
    )


if __name__ == "__main__":
    import asyncio

    async def main():
        results = await run_all_monitors()
        for result in results:
            print(json.dumps(result, indent=2))
            if result["status"] != "healthy":
                await alert_to_slack(result)

    asyncio.run(main())
