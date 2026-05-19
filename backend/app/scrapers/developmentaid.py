"""Scraper de DevelopmentAid.

Schedule: Diario 9am (cron: 0 9 * * *)
Fuentes:
  - https://www.developmentaid.org/news-stream/grants  (HTML público)
  - https://www.developmentaid.org/api/feeds/grants     (RSS si existe)

Nota: DevelopmentAid tiene mucho contenido detrás de paywall. Capturamos
solo lo público (titles + snippets de la lista).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()

LIST_PAGES = (
    "https://www.developmentaid.org/news-stream/grants",
    "https://www.developmentaid.org/news-stream/posts/all/calls-for-proposals",
)

CORE_KEYWORDS = (
    # Primera infancia
    "early childhood", "ecd", "primera infancia", "educación inicial",
    "desarrollo infantil", "cero a siempre",
    # Empoderamiento femenino
    "gender equality", "women empowerment", "empoderamiento femenino",
    # Formación docente
    "teacher training", "formación docente", "educational leadership",
    # MEAL
    "monitoring evaluation", "sistematización", "monitoreo y evaluación",
    # Economía del cuidado
    "care economy", "economía del cuidado",
    # Transformación sistémica
    "transferencia", "modelo escalable", "incidencia política",
)

GEO_KEYWORDS = (
    "latin america", "latinoamérica", "colombia", "región andina",
)

USER_AGENT = "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"


class DevelopmentAidScraper(BaseScraper):
    source_name = "developmentaid"
    base_url = "https://www.developmentaid.org"
    schedule = "0 9 * * *"

    async def fetch_raw(self) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            for page_url in LIST_PAGES:
                log = logger.bind(page=page_url)
                try:
                    resp = await client.get(page_url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    log.warning("DevAid page fetch failed", error=str(exc))
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Cards típicos: contenedores con h2/h3 + link + snippet
                cards = soup.select("article, .card, .news-item, .news-card, .item")
                if not cards:
                    cards = soup.select("li:has(a[href*='/grants']), li:has(a[href*='/news-stream'])")

                for card in cards:
                    heading = card.find(["h1", "h2", "h3", "h4"])
                    link = card.find("a", href=True)
                    if not heading or not link:
                        continue

                    title = heading.get_text(strip=True)
                    href = str(link.get("href", ""))
                    if not title or not href or len(title) < 10:
                        continue
                    if href.startswith("/"):
                        href = "https://www.developmentaid.org" + href
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    snippet_el = card.find("p")
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    all_items.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet,
                    })

                log.info("DevAid page parsed", items_so_far=len(all_items))

        logger.info("DevAid fetch complete", total=len(all_items))
        return all_items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        title: str = raw.get("title", "").strip()
        if not title:
            return None

        description = raw.get("snippet", "")
        haystack = (title + " " + description).lower()

        # Filtro AND: al menos 1 CORE + al menos 1 GEO
        has_core = any(kw.lower() in haystack for kw in CORE_KEYWORDS)
        has_geo = any(kw.lower() in haystack for kw in GEO_KEYWORDS)
        if not (has_core and has_geo):
            return None

        return OpportunityCreate(
            title=title,
            description=description[:5000] or None,
            funder_name=None,  # DevAid es agregador, el funder real está en la página detalle (paywall)
            deadline=None,
            url_rfp=raw["url"],
            url_source=raw["url"],
            source_name=self.source_name,
            org_website="https://www.developmentaid.org",
            sectors=["aggregator"],
            capital_type="grant",
            raw_content=json.dumps(raw, default=str)[:10_000],
        )
