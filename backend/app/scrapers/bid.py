"""Scraper de BID Lab (Banco Interamericano de Desarrollo).

Schedule: Diario 7am (cron: 0 7 * * *)
Fuente: https://bidlab.org/es/convocatorias  (versión española)
        https://www.iadb.org/en/projects-and-procurement (procurement)

Estrategia: HTML scraping de la página de convocatorias abiertas, filtrando
por keywords relevantes a primera infancia / educación / LATAM.

Nota: Los sitios web del BID cambian regularmente. Si la estructura HTML
cambia y el scraper devuelve 0 resultados, hay que actualizar los selectores.
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

# Páginas listadas en orden de prioridad
BID_LIST_PAGES = (
    "https://bidlab.org/es/convocatorias",
    "https://bidlab.org/en/calls-for-proposals",
)

# Keywords de relevancia
RELEVANT_KEYWORDS = (
    "primera infancia", "educación", "infancia", "niñez", "desarrollo infantil",
    "early childhood", "ecd", "education", "child", "youth",
    "latin america", "latinoamérica", "colombia", "andina",
    "innovación social", "social innovation", "transferencia",
)

USER_AGENT = "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"


class BidScraper(BaseScraper):
    source_name = "bid"
    base_url = "https://bidlab.org"
    schedule = "0 7 * * *"

    async def fetch_raw(self) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            for page_url in BID_LIST_PAGES:
                log = logger.bind(page=page_url)
                try:
                    resp = await client.get(page_url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    log.warning("BID page fetch failed", error=str(exc))
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Heurística: buscar enlaces a páginas de convocatoria.
                # BIDLab usa cards con enlaces /convocatorias/{slug} o /calls-for-proposals/{slug}
                cards = soup.select(
                    "a[href*='/convocatorias/'], a[href*='/calls-for-proposals/'], "
                    "article a[href], .card a[href]"
                )

                for a in cards:
                    href = a.get("href", "")
                    if not href or href.startswith("#"):
                        continue
                    if href.startswith("/"):
                        href = "https://bidlab.org" + href
                    if href in seen_urls or href in BID_LIST_PAGES:
                        continue
                    seen_urls.add(href)

                    # Texto del enlace o del card padre
                    title_text = (a.get_text(strip=True) or "").strip()
                    if len(title_text) < 10:
                        # Subir al ancestro card si el link es solo un ícono
                        parent = a.find_parent(["article", "div", "li"])
                        if parent:
                            heading = parent.find(["h1", "h2", "h3", "h4"])
                            if heading:
                                title_text = heading.get_text(strip=True)

                    if not title_text or len(title_text) < 10:
                        continue

                    all_items.append({
                        "title": title_text,
                        "url": href,
                        "list_page": page_url,
                    })

                log.info("BID page parsed", new_links=len(all_items))

            # Enriquecer cada candidato con su página de detalle (descripción, deadline)
            enriched: list[dict[str, Any]] = []
            for item in all_items[:50]:  # Cap para no abusar el sitio
                try:
                    detail = await client.get(item["url"])
                    if detail.status_code != 200:
                        continue
                    detail_soup = BeautifulSoup(detail.text, "lxml")
                    item["description"] = _extract_description(detail_soup)
                    item["deadline_text"] = _extract_deadline_text(detail_soup)
                    enriched.append(item)
                except httpx.HTTPError:
                    continue

        logger.info("BID fetch complete", total=len(enriched))
        return enriched

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        title: str = raw.get("title", "").strip()
        if not title:
            return None

        description: str = raw.get("description", "")
        haystack = (title + " " + description).lower()
        if not any(kw in haystack for kw in RELEVANT_KEYWORDS):
            return None

        deadline = _parse_deadline(raw.get("deadline_text"))

        return OpportunityCreate(
            title=title,
            description=description[:5000] or None,
            funder_name="BID Lab",
            deadline=deadline,
            url_rfp=raw["url"],
            url_source=raw["url"],
            source_name=self.source_name,
            org_website="https://bidlab.org",
            eligible_countries=["LATAM"],
            sectors=["bid"],
            capital_type="grant",
            raw_content=json.dumps(raw, default=str)[:10_000],
        )


def _extract_description(soup: BeautifulSoup) -> str:
    """Extrae texto principal del cuerpo de la página."""
    # Heurística: meta description > primer párrafo largo > body
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
    """Busca texto que mencione fecha de cierre."""
    text = soup.get_text(" ", strip=True).lower()
    import re

    pattern = re.compile(
        r"(?:fecha\s+(?:de\s+)?cierre|deadline|cierra(?:\s+el)?|due|closes?(?:\s+on)?)[\s:–-]*"
        r"(\d{1,2}[\/\s\-](?:de\s+)?\w+[\/\s\-](?:de\s+)?\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})",
        re.IGNORECASE,
    )
    m = pattern.search(text)
    return m.group(1) if m else None


def _parse_deadline(raw: str | None) -> date | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None
