"""BID Lab Scraper mejorado con Scrapling.

Resuelve Issue #2 — HTML structure fragility.
Utiliza adaptive parsing para auto-detect cambios en estructura.

Características:
- ✅ Adaptive CSS selectors (auto-detect si estructura cambia)
- ✅ JavaScript rendering si necesario
- ✅ Auto-save estructura (auditoría de cambios)
- ✅ Logging detallado de parsing
"""

from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any
from urllib.parse import urljoin

import structlog

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base_scrapling import BaseScraperWithScrapling

logger = structlog.get_logger()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

BID_LAB_BASE_URL = "https://www.iadb.org/es/oportunidades"
BID_KEYWORDS = (
    "convocatoria", "oportunidad", "call for proposals", "opportunity",
    "educación", "educacion", "infancia", "primera infancia",
    "desarrollo", "grant", "funding", "scholarship",
)

# Selectores múltiples (fallback si cambia estructura)
BID_OPPORTUNITY_SELECTORS = [
    "article[data-opportunity-id]",  # Estructura esperada
    ".opportunity-card",  # Alternativa 1
    ".bid-call-item",  # Alternativa 2
    ".oportunidad",  # Alternativa 3 (Spanish)
    ".convocatoria",  # Alternativa 4
    "div[class*='opportunity']",  # Cualquier div con 'opportunity'
]

BID_TITLE_SELECTORS = [
    "h2, h3, .title, [class*='title']::text",
]

BID_URL_SELECTORS = [
    "a[href*='/oportunidades/']::attr(href)",
    "a[href*='/opportunities/']::attr(href)",
    ".bid-link::attr(href)",
    "[class*='link'] a::attr(href)",
]

BID_DESCRIPTION_SELECTORS = [
    ".description, .summary, p[class*='desc']::text",
    "p::text",  # Fallback: todos los párrafos
]

BID_DEADLINE_SELECTORS = [
    ".deadline, [class*='deadline']::text",
    ".fecha, [class*='fecha']::text",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════


class BidLabScraperScrapling(BaseScraperWithScrapling):
    source_name = "bid_lab_scrapling"
    base_url = BID_LAB_BASE_URL
    schedule = "0 7 * * *"  # 7am diario

    async def fetch_raw(self) -> list[dict[str, Any]]:
        """Fetch BID Lab opportunities con Scrapling adaptativo.

        Estructura:
        1. Fetch página principal con DynamicFetcher (puede tener JS)
        2. Parse adaptativo de oportunidades
        3. Para cada oportunidad, fetch detalles con URL
        4. Return lista consolidada
        """
        items = []

        try:
            # Paso 1: Fetch página principal con JavaScript rendering
            logger.info("BID Lab scraper starting", url=self.base_url)

            page = await self.fetch_dynamic(
                self.base_url,
                wait_for_selector=".opportunity-card, article",  # Esperar a que cargue
                timeout=30,
            )

            # Paso 2: Parse adaptativo de oportunidades (fallback a múltiples selectores)
            opportunities = self.parse_adaptive(
                page,
                selectors=BID_OPPORTUNITY_SELECTORS,
            )

            if not opportunities:
                # Si no encontró elementos, intentar parse manual
                logger.warning("Adaptive parse returned 0 items, trying manual parse")
                opportunities = page.css(", ".join(BID_OPPORTUNITY_SELECTORS))

            logger.info("BID Lab parsed opportunities", count=len(opportunities))

            # Paso 3: Extraer datos de cada oportunidad
            for opportunity_element in opportunities[:50]:  # Limitar a 50 para no abusar
                try:
                    # Extraer título (múltiples selectores)
                    title = self._extract_text_adaptive(
                        opportunity_element,
                        BID_TITLE_SELECTORS,
                    )

                    if not title or len(title.strip()) < 10:
                        self.log_parse_result(
                            "BID opportunity",
                            reason="empty_title",
                        )
                        continue

                    # Extraer URL (múltiples selectores)
                    url = self._extract_attr_adaptive(
                        opportunity_element,
                        BID_URL_SELECTORS,
                        attr="href",
                    )

                    if not url:
                        self.log_parse_result(
                            title[:50],
                            reason="no_url",
                        )
                        continue

                    # Hacer URL absoluta
                    url = urljoin(self.base_url, url)

                    # Extraer descripción
                    description = self._extract_text_adaptive(
                        opportunity_element,
                        BID_DESCRIPTION_SELECTORS,
                    )

                    # Extraer deadline
                    deadline_text = self._extract_text_adaptive(
                        opportunity_element,
                        BID_DEADLINE_SELECTORS,
                    )

                    # Parsear deadline
                    deadline = self._parse_deadline(deadline_text) if deadline_text else None

                    items.append({
                        "title": title.strip(),
                        "description": description.strip() if description else "",
                        "url": url,
                        "deadline_text": deadline_text,
                        "deadline": deadline,
                        "source": "bid_lab_scrapling",
                    })

                except Exception as e:
                    logger.debug(
                        "Error parsing BID opportunity",
                        error=str(e)[:100],
                    )
                    continue

            logger.info("BID Lab fetch complete", total_items=len(items))

        except Exception as e:
            logger.error("BID Lab scraper failed", error=str(e)[:200])
            raise

        return items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convertir raw BID item → OpportunityCreate."""
        title = raw.get("title", "").strip()

        if not title or len(title) < 10:
            self.log_parse_result("BID item", reason="invalid_title")
            return None

        # Validar keywords
        text = (title + " " + raw.get("description", "")).lower()
        has_keywords = any(kw.lower() in text for kw in BID_KEYWORDS)

        if not has_keywords:
            self.log_parse_result(
                title[:50],
                reason="no_keywords",
                item_data={"keywords": BID_KEYWORDS},
            )
            return None

        url = raw.get("url", "")
        if not url or not url.startswith("http"):
            self.log_parse_result(title[:50], reason="invalid_url")
            return None

        return OpportunityCreate(
            title=title[:200],
            description=raw.get("description", "")[:5000],
            funder_name="BID / IADB",
            deadline=raw.get("deadline"),
            url_rfp=url,
            url_source=url,
            source_name=self.source_name,
            org_website="https://www.iadb.org",
            eligible_countries=["Latin America"],
            sectors=["education", "development"],
            capital_type="grant",
            market_window="funding_global",
            raw_content=json.dumps(raw, default=str),
        )

    # ═════════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═════════════════════════════════════════════════════════════════════════════

    def _extract_text_adaptive(
        self,
        element,
        selectors: list[str],
    ) -> str:
        """Extraer texto con múltiples selectores (fallback)."""
        for selector in selectors:
            try:
                # Scrapling soporta ::text pseudo-selector
                selector_clean = selector.replace("::text", "")
                text = element.css(selector_clean + "::text", adaptive=True).get()

                if text and len(text.strip()) > 0:
                    return text.strip()
            except Exception:
                continue

        return ""

    def _extract_attr_adaptive(
        self,
        element,
        selectors: list[str],
        attr: str = "href",
    ) -> str:
        """Extraer atributo con múltiples selectores (fallback)."""
        for selector in selectors:
            try:
                # Limpiar selector
                selector_clean = selector.replace(f"::attr({attr})", "")
                elements = element.css(selector_clean, adaptive=True)

                if elements:
                    el = elements[0] if isinstance(elements, list) else elements
                    value = el.get_attribute(attr) if hasattr(el, "get_attribute") else None

                    if value:
                        return value
            except Exception:
                continue

        return ""

    def _parse_deadline(self, deadline_text: str | None) -> date | None:
        """Parse deadline de texto.

        Soporta formatos:
        - "31 de Diciembre de 2026"
        - "31/12/2026"
        - "2026-12-31"
        - "Dec 31, 2026"
        """
        if not deadline_text:
            return None

        try:
            # Intentar múltiples formatos
            for fmt in [
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y-%m-%d",
                "%B %d, %Y",
                "%d de %B de %Y",
            ]:
                try:
                    return datetime.strptime(deadline_text.strip(), fmt).date()
                except ValueError:
                    continue

            # Si nada funciona, retornar None
            logger.debug(
                "Could not parse deadline",
                deadline_text=deadline_text[:50],
                source=self.source_name,
            )
            return None

        except Exception as e:
            logger.debug(
                "Deadline parse error",
                error=str(e)[:100],
            )
            return None
