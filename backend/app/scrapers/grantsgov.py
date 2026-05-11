"""Scraper para Grants.gov REST API v1.

Documentación: https://api.grants.gov/v1/api/search2
Schedule: Diario 6am (cron: 0 6 * * *)
"""

import json
from datetime import date, datetime

import httpx
import structlog

from app.core.config import settings
from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()

# Keywords relevantes para aeioTU — filtro de primera pasada
RELEVANT_KEYWORDS = [
    "early childhood", "ECD", "early education", "preschool", "kindergarten",
    "child development", "teacher training", "education policy", "latin america",
    "colombia", "scalable model", "replication", "capacity building",
    "primera infancia", "educación inicial", "desarrollo infantil",
    "formación docente", "política educativa", "latinoamérica",
]

SEARCH_TERMS = [
    # ECD core
    "early childhood education",
    "early childhood development",
    "preschool capacity building",
    "ECD scalable model",
    # Latam / Colombia focus
    "child development latin america",
    "early education colombia",
    "education latin america",
    "youth development latin america",
    # Teacher / capacity building
    "teacher training developing countries",
    "education capacity building",
    # International / USAID-style
    "international education program",
    "global development education",
    "USAID basic education",
    # Gender / vulnerable populations
    "girls education developing",
    "vulnerable children education",
]

GRANTS_GOV_API = "https://api.grants.gov/v1/api/search2"


class GrantsGovScraper(BaseScraper):
    source_name = "grantsgov"
    base_url = GRANTS_GOV_API
    schedule = "0 6 * * *"

    async def fetch_raw(self) -> list[dict]:
        all_hits: list[dict] = []
        seen_ids: set[int] = set()

        async with httpx.AsyncClient(timeout=30) as client:
            for term in SEARCH_TERMS:
                start = 0
                while True:
                    payload = {
                        "keyword": term,
                        "oppStatuses": "posted|forecasted",
                        "rows": 25,
                        "startRecordNum": start,
                    }
                    try:
                        resp = await client.post(
                            GRANTS_GOV_API,
                            json=payload,
                            headers={"Content-Type": "application/json"},
                        )
                        resp.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        raise ScraperError(
                            f"Grants.gov API returned {exc.response.status_code}"
                        ) from exc

                    body = resp.json()
                    # Grants.gov v1: la respuesta envuelve los resultados en "data"
                    payload = body.get("data", body)
                    hits: list[dict] = payload.get("oppHits", [])
                    if not hits:
                        break

                    for hit in hits:
                        opp_id = hit.get("id")
                        if opp_id and opp_id not in seen_ids:
                            seen_ids.add(opp_id)
                            all_hits.append(hit)

                    # Paginar si hay más resultados
                    hit_count: int = payload.get("hitCount", 0)
                    start += len(hits)
                    if start >= hit_count or start >= 100:  # Máx 100 por término
                        break

        logger.info("Grants.gov fetch complete", total_unique=len(all_hits))
        return all_hits

    def normalize(self, raw: dict) -> OpportunityCreate | None:
        title: str = raw.get("title", "").strip()
        if not title:
            return None

        # La API search2 ya filtró por keyword — confiamos en eso.
        # Filtro adicional opcional sobre el título para descartar ruido
        # (ej. "Construction Grants" sin relación con ECD).
        # Mantenemos permisivo aquí; el LLM hace el filtro fino en el scoring.

        # Fecha límite
        deadline = _parse_date(raw.get("closeDate"))

        # La respuesta de search2 NO incluye descripción ni montos.
        # Usamos title + agency como descripción mínima; el módulo de
        # detalle (S2) puede enriquecer luego con /opportunity/details.
        agency = raw.get("agency") or raw.get("agencyName") or ""
        description = f"{title} — {agency}" if agency else title

        # URL de la oportunidad
        url_source = (
            f"https://www.grants.gov/search-results-detail/{raw['id']}"
            if raw.get("id")
            else None
        )

        return OpportunityCreate(
            title=title,
            description=description[:5000],
            funder_name=agency or None,
            amount_min_cop=None,
            amount_max_cop=None,
            deadline=deadline,
            url_rfp=url_source,
            url_source=url_source,
            source_name=self.source_name,
            org_website="https://www.grants.gov",
            eligible_countries=["USA"],
            sectors=_extract_sectors(raw),
            capital_type="grant",
            raw_content=json.dumps(raw, default=str),
        )


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _usd_to_cop(amount_usd: float | int | None) -> int | None:
    if amount_usd is None:
        return None
    return int(float(amount_usd) * settings.USD_TO_COP_RATE)


def _extract_sectors(raw: dict) -> list[str]:
    sectors: list[str] = []
    cfda = raw.get("cfdaList") or []
    if isinstance(cfda, list):
        sectors.extend(f"cfda:{c}" for c in cfda)
    elif cfda:
        sectors.append(f"cfda:{cfda}")
    if raw.get("docType"):
        sectors.append(str(raw["docType"]))
    return sectors
