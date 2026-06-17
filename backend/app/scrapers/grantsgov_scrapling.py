"""Grants.gov Scraper mejorado con Scrapling.

Reemplaza grantsgov.py con:
- ✅ Adaptive parsing (auto-detect cambios en API response)
- ✅ Robust retry logic con Scrapling
- ✅ Rate limiting inteligente
- ✅ Fallback a página web si API falla

Nota: Grants.gov proporciona API oficial, así que es confiable.
Scrapling mejora el HTML parsing de descripciones detalladas.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx
import structlog

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base_scrapling import BaseScraperWithScrapling

logger = structlog.get_logger()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

GRANTSGOV_API_URL = "https://api.grants.gov/v1/api/search2"
GRANTSGOV_WEB_URL = "https://www.grants.gov"

SEARCH_TERMS = [
    "early childhood education",
    "educación inicial",
    "primera infancia",
    "ECD",
    "child development",
    "teacher training",
    "formación docente",
]

KEYWORDS_CORE = (
    "early childhood", "educación inicial", "primera infancia",
    "teacher training", "formación docente",
    "grant", "funding", "convocatoria",
)


class GrantsGovScraperScrapling(BaseScraperWithScrapling):
    source_name = "grantsgov_scrapling"
    base_url = GRANTSGOV_API_URL
    schedule = "0 6 * * *"  # 6am diario

    async def fetch_raw(self) -> list[dict[str, Any]]:
        """Fetch desde Grants.gov API con fallback a web scraping."""
        items = []

        # Estrategia 1: API oficial
        try:
            api_items = await self._fetch_api()
            items.extend(api_items)
            logger.info("GrantsGov API fetch successful", count=len(api_items))
        except Exception as e:
            logger.warning(
                "GrantsGov API fetch failed, trying web scraping",
                error=str(e)[:100],
            )

            # Estrategia 2: Fallback a web scraping con Scrapling
            try:
                web_items = await self._fetch_web_scrapling()
                items.extend(web_items)
                logger.info("GrantsGov web scraping successful", count=len(web_items))
            except Exception as e2:
                logger.error(
                    "GrantsGov both strategies failed",
                    api_error=str(e)[:100],
                    web_error=str(e2)[:100],
                )
                raise

        return items

    async def _fetch_api(self) -> list[dict[str, Any]]:
        """Fetch desde API oficial de Grants.gov."""
        items = []

        async with httpx.AsyncClient(timeout=30) as client:
            for search_term in SEARCH_TERMS:
                try:
                    for page in range(1, 4):  # 3 páginas
                        params = {
                            "searchString": search_term,
                            "pageNumber": page,
                            "pageSize": 100,
                        }

                        resp = await client.get(GRANTSGOV_API_URL, params=params)

                        if resp.status_code != 200:
                            logger.debug(
                                "GrantsGov API non-200",
                                status=resp.status_code,
                                search_term=search_term,
                            )
                            break

                        data = resp.json()
                        opportunities = data.get("opportunities", [])

                        if not opportunities:
                            break

                        items.extend(opportunities)

                        # Rate limiting
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.debug(
                        "GrantsGov API search failed",
                        search_term=search_term,
                        error=str(e)[:100],
                    )
                    continue

        return items

    async def _fetch_web_scrapling(self) -> list[dict[str, Any]]:
        """Fallback: Scrape página web de Grants.gov con Scrapling."""
        items = []

        try:
            # Usar Scrapling para eludir anti-bot
            page = await self.fetch_dynamic(
                f"{GRANTSGOV_WEB_URL}/search-results",
                timeout=30,
            )

            # Parse adaptativo de oportunidades
            opportunity_selectors = [
                "a[href*='/search/show']",  # Estructura esperada
                ".opportunity-item a",
                "[class*='grant'] a",
                "article a[href*='grant']",
            ]

            opportunities = self.parse_adaptive(
                page,
                selectors=opportunity_selectors,
            )

            for opp_link in opportunities[:50]:
                try:
                    href = opp_link.get_attribute("href")
                    title = opp_link.css("::text").get()

                    if not href or not title:
                        continue

                    items.append({
                        "title": title.strip(),
                        "url": href,
                        "description": "",  # Se obtiene en normalize
                        "source": "grantsgov_web_scrapling",
                    })

                except Exception as e:
                    logger.debug("GrantsGov web parse error", error=str(e)[:100])
                    continue

        except Exception as e:
            logger.error(
                "GrantsGov web scraping failed",
                error=str(e)[:100],
            )
            raise

        return items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convertir raw Grants.gov item → OpportunityCreate."""
        title = raw.get("title", "").strip()

        if not title or len(title) < 10:
            self.log_parse_result("GrantsGov item", reason="empty_title")
            return None

        # Validar keywords
        text = (title + " " + raw.get("description", "")).lower()
        has_keywords = any(kw.lower() in text for kw in KEYWORDS_CORE)

        if not has_keywords:
            self.log_parse_result(
                title[:50],
                reason="no_keywords",
            )
            return None

        url = raw.get("url", raw.get("funding_id", ""))
        if not url:
            self.log_parse_result(title[:50], reason="no_url")
            return None

        if not url.startswith("http"):
            url = f"{GRANTSGOV_WEB_URL}{url}" if url.startswith("/") else url

        # Parsear deadline
        deadline_str = raw.get("deadline_date") or raw.get("closeDate")
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).date()
            except Exception:
                pass

        # Parsear monto
        amount_min = None
        amount_max = None
        if raw.get("estimated_total_program_funding"):
            try:
                amount_max = int(raw["estimated_total_program_funding"])
            except (ValueError, TypeError):
                pass

        return OpportunityCreate(
            title=title[:200],
            description=raw.get("description", "")[:5000],
            funder_name=raw.get("funder_name", "Grants.gov"),
            deadline=deadline,
            amount_min_cop=None,  # En USD, se convierte en runner.py
            amount_max_cop=None,
            url_rfp=url,
            url_source=url,
            source_name=self.source_name,
            org_website=GRANTSGOV_WEB_URL,
            eligible_countries=["United States", "Global"],
            sectors=raw.get("sectors", ["education", "development"]),
            capital_type="grant",
            market_window="funding_global",
            raw_content=json.dumps(raw, default=str),
        )


# ═════════════════════════════════════════════════════════════════════════════
# IMPORTAR ASYNCIO (necesario para asyncio.sleep)
# ═════════════════════════════════════════════════════════════════════════════

import asyncio
