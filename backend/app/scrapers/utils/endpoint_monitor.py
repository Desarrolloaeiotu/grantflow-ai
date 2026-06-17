"""Monitor de Endpoints API — Detecta cambios en disponibilidad de APIs.

Valida que los endpoints de APIs (Grants.gov, SECOP) y feeds RSS (ICBF, MinEducacion, etc.)
siguen respondiendo correctamente. Si un endpoint falla o retorna contenido inválido,
alertar a Slack inmediatamente.

Schedule: Cada hora (5 min pasada la hora, para evitar colisiones)
Ejecución: Via n8n hourly-endpoint-monitor workflow
"""

from __future__ import annotations

import asyncio
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
import structlog

from app.core.database import AsyncSessionLocal

logger = structlog.get_logger()

ENDPOINT_CONFIG_PATH = "config/endpoint_urls.json"
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"


@dataclass(frozen=True)
class EndpointConfig:
    """Configuración de un endpoint a monitorear."""
    endpoint_name: str
    url: str
    method: str = "GET"
    content_type: str = "json"  # "json" | "xml" | "html"
    timeout_sec: int = 10
    description: str = ""
    category: str = "unknown"
    # Para POST requests, body mínimo
    request_body: dict[str, Any] | None = None


def load_endpoint_configs() -> dict[str, EndpointConfig]:
    """Carga configuración de endpoints desde JSON."""
    try:
        with open(ENDPOINT_CONFIG_PATH, "r") as f:
            config_data = json.load(f)

        configs = {}
        for endpoint_name, endpoint_cfg in config_data.items():
            configs[endpoint_name] = EndpointConfig(
                endpoint_name=endpoint_name,
                url=endpoint_cfg["url"],
                method=endpoint_cfg.get("method", "GET"),
                content_type=endpoint_cfg.get("content_type", "json"),
                timeout_sec=endpoint_cfg.get("timeout_sec", 10),
                description=endpoint_cfg.get("description", ""),
                category=endpoint_cfg.get("category", "unknown"),
                request_body=endpoint_cfg.get("request_body"),
            )
        return configs
    except Exception as exc:
        logger.error("Failed to load endpoint configs", error=str(exc))
        return {}


ENDPOINT_CONFIGS = load_endpoint_configs()


async def validate_endpoint(endpoint_name: str) -> dict[str, Any]:
    """Valida que un endpoint API/RSS está disponible y retorna contenido válido.

    Retorna:
        {
            "endpoint_name": "grantsgov_api",
            "url": "https://api.grants.gov/v1/api/search2",
            "method": "POST",
            "status": "healthy" | "degraded" | "failed",
            "http_status_code": 200,
            "latency_ms": 450,
            "results": {
                "parsed_ok": True,
                "content_type": "json",
                "entry_count": 5  # para XML/RSS
            },
            "error": None | "error message",
            "checked_at": "2026-06-01T12:00:00Z"
        }
    """
    config = ENDPOINT_CONFIGS.get(endpoint_name)
    if not config:
        return {
            "endpoint_name": endpoint_name,
            "status": "failed",
            "error": f"Unknown endpoint: {endpoint_name}",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

    log = logger.bind(endpoint=endpoint_name, url=config.url, method=config.method)
    start_time = datetime.utcnow()

    try:
        async with httpx.AsyncClient(timeout=config.timeout_sec, follow_redirects=True) as client:
            if config.method == "POST":
                resp = await client.post(config.url, json=config.request_body or {})
            else:
                resp = await client.get(config.url)

            resp.raise_for_status()

    except httpx.HTTPError as exc:
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        log.error(
            "HTTP request failed",
            status_code=getattr(exc.response, "status_code", "N/A"),
            latency_ms=latency,
        )
        return {
            "endpoint_name": endpoint_name,
            "url": config.url,
            "method": config.method,
            "status": "failed",
            "http_status_code": getattr(exc.response, "status_code", None),
            "latency_ms": int(latency),
            "error": f"HTTP error: {exc}",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }
    except asyncio.TimeoutError:
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        log.error("Timeout", latency_ms=latency)
        return {
            "endpoint_name": endpoint_name,
            "url": config.url,
            "method": config.method,
            "status": "failed",
            "latency_ms": int(latency),
            "error": "Timeout exceeded",
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
    results = {"parsed_ok": False, "content_type": config.content_type}

    # Validar contenido según tipo
    try:
        if config.content_type == "json":
            data = resp.json()
            if isinstance(data, (dict, list)):
                results["parsed_ok"] = True
                results["entry_count"] = len(data) if isinstance(data, list) else 1
        elif config.content_type == "xml":
            root = ET.fromstring(resp.content)
            # Contar entries (Atom) o items (RSS2)
            entries = root.findall(".//entry") + root.findall(".//item")
            results["parsed_ok"] = len(entries) > 0
            results["entry_count"] = len(entries)
        elif config.content_type == "html":
            results["parsed_ok"] = "<html" in resp.text.lower() or "<!doctype" in resp.text.lower()

    except Exception as exc:
        log.warning("Content parsing failed", error=str(exc), content_type=config.content_type)
        results["parsed_ok"] = False
        results["parse_error"] = str(exc)[:100]

    # Determinar status
    if resp.status_code != 200:
        overall_status = "failed"
    elif not results["parsed_ok"]:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    log.info(
        f"Endpoint validation completed",
        status=overall_status,
        http_status=resp.status_code,
        latency_ms=int(latency),
    )

    return {
        "endpoint_name": endpoint_name,
        "url": config.url,
        "method": config.method,
        "status": overall_status,
        "http_status_code": resp.status_code,
        "latency_ms": int(latency),
        "results": results,
        "error": None,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }


async def run_all_endpoint_monitors() -> list[dict[str, Any]]:
    """Ejecuta validación de endpoints en paralelo."""
    log = logger.bind(action="run_all_endpoint_monitors")
    log.info("Starting endpoint monitor run", total_endpoints=len(ENDPOINT_CONFIGS))

    # Ejecutar todas las validaciones en paralelo
    tasks = [validate_endpoint(endpoint_name) for endpoint_name in ENDPOINT_CONFIGS.keys()]
    results = await asyncio.gather(*tasks)

    # Log summary
    healthy = sum(1 for r in results if r["status"] == "healthy")
    degraded = sum(1 for r in results if r["status"] == "degraded")
    failed = sum(1 for r in results if r["status"] == "failed")

    log.info(
        "Endpoint monitor run completed",
        healthy=healthy,
        degraded=degraded,
        failed=failed,
        total=len(results),
    )

    return results


async def alert_to_slack(result: dict[str, Any]) -> bool:
    """Envía alerta a Slack si hay problema detectado.

    Solo alerta si status == "degraded" o "failed".
    """
    if result["status"] == "healthy":
        return True

    endpoint = result["endpoint_name"]
    status = result["status"]
    error = result.get("error")
    http_status = result.get("http_status_code")

    # Construir mensaje
    if status == "failed":
        color = "danger"  # Rojo
        title = f"🚨 CRITICAL: {endpoint} endpoint failed"
    else:
        color = "warning"  # Amarillo
        title = f"⚠️ WARNING: {endpoint} endpoint degraded"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": title},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Endpoint:*\n{endpoint}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{status.upper()}"},
                {"type": "mrkdwn", "text": f"*URL:*\n{result.get('url', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*HTTP Status:*\n{http_status or 'N/A'}"},
                {"type": "mrkdwn", "text": f"*Latency:*\n{result.get('latency_ms', 'N/A')}ms"},
                {"type": "mrkdwn", "text": f"*Checked:*\n{result.get('checked_at', 'N/A')}"},
            ],
        },
    ]

    # Detalles del contenido
    if result.get("results"):
        results = result["results"]
        if not results.get("parsed_ok"):
            parse_error = results.get("parse_error", "Content format invalid")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Parse Error:*\n{parse_error}"},
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
        logger.info("Slack alert sent", endpoint=endpoint, status=status)
        return True
    except Exception as exc:
        logger.error("Failed to send Slack alert", endpoint=endpoint, error=str(exc))
        return False


async def persist_endpoint_log(
    result: dict[str, Any],
    db=None
) -> None:
    """Persiste histórico de monitors en tabla endpoint_monitor_log.

    Facilita tracking: ¿cuándo falló?, tendencias de disponibilidad.
    """
    # TODO: Implementar inserción en tabla endpoint_monitor_log (Sprint S7)
    # Por ahora solo log estructurado
    logger.info(
        "Endpoint monitor log persisted",
        endpoint=result["endpoint_name"],
        status=result["status"],
        checked_at=result["checked_at"],
    )


if __name__ == "__main__":

    async def main():
        results = await run_all_endpoint_monitors()
        for result in results:
            print(json.dumps(result, indent=2))

    asyncio.run(main())
