"""Scraper de ONU Mujeres (UN Women).

Schedule: Diario 8am (cron: 0 8 * * *)
Fuente: https://www.unwomen.org/en/get-involved/grants

Estrategia: HTML scraping de la página de grants. ONU Mujeres expone
calls-for-proposals y fondos como Fund for Gender Equality.
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

UNWOMEN_PAGES = (
    "https://www.unwomen.org/en/get-involved/grants",
    "https://www.unwomen.org/en/about-us/procurement",
    "https://www.unwomen.org/en/news-stories?type=announcement",
)

CORE_KEYWORDS = (
    # Primera infancia
    "early childhood", "ecd", "primera infancia", "educación inicial",
    # Empoderamiento femenino + género
    "gender equality", "women empowerment", "mujeres", "género",
    "empoderamiento femenino", "women leadership", "agencia femenina",
    # Formación de líderes
    "teacher training", "formación docente", "educational leadership",
    # MEAL
    "monitoring evaluation", "sistematización", "monitoreo y evaluación",
    # Economía del cuidado
    "care economy", "economía del cuidado",
)

GEO_KEYWORDS = (
    "latin america", "latinoamérica", "colombia", "región andina",
)

USER_AGENT = "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"


class UnWomenScraper(BaseScraper):
    source_name = "unwomen"
    base_url = "https://www.unwomen.org"
    schedule = "0 8 * * *"

    async def fetch_raw(self) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            for page_url in UNWOMEN_PAGES:
                log = logger.bind(page=page_url)
                try:
                    resp = await client.get(page_url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    log.warning("UN Women page fetch failed", error=str(exc))
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # UN Women usa cards/listas con titles dentro de h2/h3 con enlaces
                articles = soup.select("article, .views-row, .news-item, .card, li")
                for art in articles:
                    heading = art.find(["h1", "h2", "h3", "h4"])
                    link = art.find("a", href=True)
                    if not heading or not link:
                        continue

                    title = heading.get_text(strip=True)
                    href = str(link.get("href", ""))
                    if not title or not href or len(title) < 10:
                        continue
                    if href.startswith("/"):
                        href = "https://www.unwomen.org" + href
                    if href in seen_urls or href.endswith(page_url.rsplit("/", 1)[-1]):
                        continue
                    seen_urls.add(href)

                    # Snippet del card si existe
                    snippet_el = art.find(["p", "div"], class_=lambda c: bool(c and ("summary" in c or "excerpt" in c or "teaser" in c)))
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    all_items.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet,
                        "list_page": page_url,
                    })

                log.info("UN Women page parsed", items_so_far=len(all_items))

            # Enriquecer detalles
            enriched: list[dict[str, Any]] = []
            for item in all_items[:40]:
                try:
                    detail = await client.get(item["url"])
                    if detail.status_code != 200:
                        continue
                    detail_soup = BeautifulSoup(detail.text, "lxml")
                    item["description"] = _extract_description(detail_soup) or item.get("snippet", "")
                    item["deadline_text"] = _extract_deadline_text(detail_soup)
                    enriched.append(item)
                except httpx.HTTPError:
                    continue

        logger.info("UN Women fetch complete", total=len(enriched))
        return enriched

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        title: str = raw.get("title", "").strip()
        if not title:
            return None

        description = raw.get("description") or raw.get("snippet", "")
        haystack = (title + " " + description).lower()

        # Filtro: al menos 1 CORE_KEYWORD (UN Women es multilateral global)
        has_core = any(kw.lower() in haystack for kw in CORE_KEYWORDS)
        if not has_core:
            return None

        deadline = _parse_deadline(raw.get("deadline_text"))

        return OpportunityCreate(
            title=title,
            description=description[:5000] or None,
            funder_name="UN Women",
            deadline=deadline,
            url_rfp=raw["url"],
            url_source=raw["url"],
            source_name=self.source_name,
            org_website="https://www.unwomen.org",
            eligible_countries=["GLOBAL"],
            sectors=["gender", "un_women"],
            capital_type="grant",
            raw_content=json.dumps(raw, default=str)[:10_000],
        )


def _extract_description(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return str(meta["content"]).strip()
    article = soup.find(["article", "main"])
    if article:
        paragraphs = article.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs[:5])
        if text:
            return text[:3000]
    return ""


def _extract_deadline_text(soup: BeautifulSoup) -> str | None:
    import re

    text = soup.get_text(" ", strip=True)
    pattern = re.compile(
        r"(?:deadline|cierre|due|closes?(?:\s+on)?)[\s:–-]*"
        r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})",
        re.IGNORECASE,
    )
    m = pattern.search(text)
    return m.group(1) if m else None


def _parse_deadline(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None
