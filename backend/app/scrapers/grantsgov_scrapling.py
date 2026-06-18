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

import asyncio
import json
import random
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

# ═══════════════════════════════════════════════════════════════════════════════
# USER-AGENT POOL — Rotar headers para evitar bloqueos 403
# ═══════════════════════════════════════════════════════════════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

REFERER_URLS = [
    "https://www.grants.gov/",
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://search.yahoo.com/",
]


def get_random_headers() -> dict[str, str]:
    """Generar headers legítimos con User-Agent y Referer variados."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERER_URLS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }


class GrantsGovScraperScrapling(BaseScraperWithScrapling):
    source_name = "grantsgov_scrapling"
    base_url = GRANTSGOV_API_URL
    schedule = "0 6 * * *"  # 6am diario
    max_retries = 4
    initial_backoff = 1  # segundos

    async def _fetch_with_retry(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> httpx.Response | None:
        """
        Fetch con retry y backoff exponencial.

        Intenta 4 veces con backoff: 1s → 2s → 4s → 8s
        Cambia User-Agent en cada reintento.

        Returns:
            Response objeto si éxito, None si falla después de max_retries.
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(self.max_retries):
                headers = get_random_headers()
                backoff_wait = self.initial_backoff * (2 ** attempt)

                try:
                    logger.debug(
                        "GrantsGov API attempt",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        url=url[:80],
                        user_agent=headers["User-Agent"][:50],
                    )

                    response = await client.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=timeout,
                    )

                    if response.status_code == 200:
                        logger.info(
                            "GrantsGov API success",
                            attempt=attempt + 1,
                            status=response.status_code,
                        )
                        return response

                    elif response.status_code == 403:
                        logger.warning(
                            "GrantsGov API 403 Forbidden",
                            attempt=attempt + 1,
                            url=url[:80],
                        )
                        # Continuar con retry

                    else:
                        logger.warning(
                            "GrantsGov API non-200 status",
                            attempt=attempt + 1,
                            status=response.status_code,
                            url=url[:80],
                        )
                        # Continuar con retry

                except asyncio.TimeoutError:
                    logger.warning(
                        "GrantsGov API timeout",
                        attempt=attempt + 1,
                        timeout=timeout,
                    )
                    # Continuar con retry

                except httpx.ConnectError as e:
                    logger.warning(
                        "GrantsGov API connection error",
                        attempt=attempt + 1,
                        error=str(e)[:100],
                    )
                    # Continuar con retry

                except Exception as e:
                    logger.warning(
                        "GrantsGov API unexpected error",
                        attempt=attempt + 1,
                        error_type=type(e).__name__,
                        error=str(e)[:100],
                    )
                    # Continuar con retry

                # Wait before retry (excepto en último intento)
                if attempt < self.max_retries - 1:
                    logger.info(
                        "GrantsGov backoff wait",
                        attempt=attempt + 1,
                        wait_seconds=backoff_wait,
                    )
                    await asyncio.sleep(backoff_wait)

        logger.error(
            "GrantsGov API failed after all retries",
            max_retries=self.max_retries,
            url=url[:80],
        )
        return None

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
        """
        Fetch desde API oficial de Grants.gov con retry y backoff.

        - 3 search terms
        - 4 reintentos por request con backoff exponencial (1s → 2s → 4s → 8s)
        - Headers variados (User-Agent rotante)
        - Rate limiting entre búsquedas y páginas
        """
        items = []

        for search_term in SEARCH_TERMS:
            logger.info("GrantsGov search term starting", search_term=search_term)

            try:
                for page in range(1, 4):  # 3 páginas máximo
                    params = {
                        "searchString": search_term,
                        "pageNumber": page,
                        "pageSize": 100,
                    }

                    # Usar retry con backoff
                    resp = await self._fetch_with_retry(
                        GRANTSGOV_API_URL,
                        params=params,
                        timeout=30,
                    )

                    if resp is None:
                        # Falló después de todos los reintentos
                        logger.warning(
                            "GrantsGov page fetch exhausted",
                            search_term=search_term,
                            page=page,
                        )
                        break

                    try:
                        data = resp.json()
                        opportunities = data.get("opportunities", [])

                        if not opportunities:
                            logger.info(
                                "GrantsGov no opportunities in page",
                                search_term=search_term,
                                page=page,
                            )
                            break

                        items.extend(opportunities)
                        logger.info(
                            "GrantsGov page fetched",
                            search_term=search_term,
                            page=page,
                            count=len(opportunities),
                        )

                    except json.JSONDecodeError as e:
                        logger.error(
                            "GrantsGov JSON parse error",
                            search_term=search_term,
                            page=page,
                            error=str(e)[:100],
                        )
                        break

                    # Rate limiting entre páginas
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(
                    "GrantsGov search term error",
                    search_term=search_term,
                    error_type=type(e).__name__,
                    error=str(e)[:100],
                )
                # Continuar con siguiente search term

            # Rate limiting entre search terms
            await asyncio.sleep(1)

        logger.info("GrantsGov API fetch complete", total_items=len(items))
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


