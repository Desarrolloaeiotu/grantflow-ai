"""Scraper genérico de feeds RSS / Atom.

Consume múltiples fuentes RSS configuradas en RSS_FEEDS y unifica
sus entradas como oportunidades. Filtra por keywords ECD relevantes.

Schedule: Diario 10am (cron: 0 10 * * *)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import feedparser
import httpx
import structlog

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()


@dataclass(frozen=True)
class FeedSource:
    name: str          # "developmentaid"
    url: str           # URL del feed
    funder_hint: str | None = None  # Nombre del financiador si todo el feed es de uno solo
    org_website: str | None = None  # Website principal del financiador
    capital_type: str = "grant"


# Fuentes RSS globales que publican grants/oportunidades relevantes ECD.
# Lista organizada por categoría. Agregar/quitar feeds según se descubran.
RSS_FEEDS: tuple[FeedSource, ...] = (
    # ── Agregadores filantrópicos ─────────────────────────────────────────────
    FeedSource(
        name="philanthropy_news_digest",
        url="https://philanthropynewsdigest.org/rfps/rss",
        org_website="https://philanthropynewsdigest.org",
    ),
    FeedSource(
        name="grantstation_news",
        url="https://grantstation.com/rss.xml",
        org_website="https://grantstation.com",
    ),
    FeedSource(
        name="fundsforngos",
        url="https://www2.fundsforngos.org/feed/",
        org_website="https://www.fundsforngos.org",
    ),
    FeedSource(
        name="fundsforngos_latam",
        url="https://es.fundsforngos.org/feed/",
        org_website="https://es.fundsforngos.org",
    ),
    FeedSource(
        name="terra_viva_grants",
        url="https://www.terravivagrants.org/feed/",
        org_website="https://www.terravivagrants.org",
    ),

    # ── Sistema ONU / multilaterales ──────────────────────────────────────────
    FeedSource(
        name="reliefweb_jobs",
        url="https://reliefweb.int/jobs/rss.xml",
        org_website="https://reliefweb.int",
    ),
    FeedSource(
        name="reliefweb_training",
        url="https://reliefweb.int/training/rss.xml",
        org_website="https://reliefweb.int",
    ),
    FeedSource(
        name="unicef_press",
        url="https://www.unicef.org/press-releases/rss.xml",
        funder_hint="UNICEF",
        org_website="https://www.unicef.org",
    ),
    FeedSource(
        name="unesco_news",
        url="https://www.unesco.org/en/rss.xml",
        funder_hint="UNESCO",
        org_website="https://www.unesco.org",
    ),
    FeedSource(
        name="worldbank_news",
        url="https://www.worldbank.org/en/news/all?format=atom",
        funder_hint="World Bank",
        org_website="https://www.worldbank.org",
    ),

    # ── Fundaciones globales estratégicas (CLAUDE.md) ─────────────────────────
    FeedSource(
        name="lego_foundation",
        url="https://www.legofoundation.com/en/about-us/news/rss/",
        funder_hint="LEGO Foundation",
        org_website="https://www.legofoundation.com",
    ),
    FeedSource(
        name="grand_challenges_canada",
        url="https://www.grandchallenges.ca/feed/",
        funder_hint="Grand Challenges Canada",
        org_website="https://www.grandchallenges.ca",
    ),
    FeedSource(
        name="hilton_foundation",
        url="https://www.hiltonfoundation.org/news/feed",
        funder_hint="Conrad N. Hilton Foundation",
        org_website="https://www.hiltonfoundation.org",
    ),
    FeedSource(
        name="ford_foundation",
        url="https://www.fordfoundation.org/news-and-stories/news-and-ideas/feed/",
        funder_hint="Ford Foundation",
        org_website="https://www.fordfoundation.org",
    ),
    FeedSource(
        name="open_society",
        url="https://www.opensocietyfoundations.org/newsroom/rss.xml",
        funder_hint="Open Society Foundations",
        org_website="https://www.opensocietyfoundations.org",
    ),
    FeedSource(
        name="bernard_van_leer",
        url="https://bernardvanleer.org/feed/",
        funder_hint="Bernard van Leer Foundation",
        org_website="https://bernardvanleer.org",
    ),

    # ── Cooperación europea y bilateral ───────────────────────────────────────
    FeedSource(
        name="giz_news",
        url="https://www.giz.de/en/rss/newsroom.xml",
        funder_hint="GIZ",
        org_website="https://www.giz.de",
    ),
    FeedSource(
        name="eu_funding_tenders",
        url="https://ec.europa.eu/info/funding-tenders/opportunities/portal/api/announcement/get-rss",
        funder_hint="European Commission",
        org_website="https://ec.europa.eu",
    ),

    # ── ECD / Educación inicial ───────────────────────────────────────────────
    FeedSource(
        name="ecdan_news",
        url="https://www.ecdan.org/feed",
        funder_hint="Early Childhood Development Action Network",
        org_website="https://www.ecdan.org",
    ),
)

# Keywords para descartar entradas claramente irrelevantes a ECD.
# El filtro es laxo aquí — el LLM scoring hace el filtro fino.
RELEVANT_KEYWORDS = (
    # Inglés
    "early childhood", "ecd", "early education", "preschool", "kindergarten",
    "child development", "children", "youth", "education", "teacher", "school",
    "latin america", "colombia", "global south", "developing", "capacity",
    # Español
    "primera infancia", "educación inicial", "desarrollo infantil", "preescolar",
    "formación docente", "política educativa", "latinoamérica", "niñez",
    "infancia", "educación", "escuela", "docente",
)


class RssFeedsScraper(BaseScraper):
    source_name = "rss"
    base_url = "various"
    schedule = "0 10 * * *"

    async def fetch_raw(self) -> list[dict[str, Any]]:
        all_entries: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for feed in RSS_FEEDS:
                log = logger.bind(feed=feed.name, url=feed.url)
                try:
                    resp = await client.get(
                        feed.url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"
                            ),
                            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                        },
                    )
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    log.warning("Feed fetch failed", error=str(exc))
                    continue

                parsed = feedparser.parse(resp.text)
                if parsed.bozo and not parsed.entries:
                    log.warning("Feed parse failed", reason=str(parsed.bozo_exception)[:120])
                    continue

                log.info("Feed fetched", entries=len(parsed.entries))
                for entry in parsed.entries:
                    all_entries.append({"_feed": feed, "entry": dict(entry)})

        logger.info("RSS fetch complete", total=len(all_entries))
        return all_entries

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        feed: FeedSource = raw["_feed"]
        entry: dict[str, Any] = raw["entry"]

        title = (entry.get("title") or "").strip()
        if not title:
            return None

        # Description: prefer summary/description, fallback to content[0].value
        description: str = entry.get("summary") or entry.get("description") or ""
        if not description:
            content = entry.get("content")
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict):
                    description = first.get("value", "") or ""
            elif isinstance(content, str):
                description = content
        description = _clean_html(str(description))[:5000]

        # Filtro laxo de relevancia
        haystack = (title + " " + description).lower()
        if not any(kw in haystack for kw in RELEVANT_KEYWORDS):
            return None

        # URL de la oportunidad
        url_rfp = entry.get("link") or entry.get("id")

        # Fecha de cierre — a menudo no está en el feed (lo deja al LLM/manual)
        deadline = _extract_deadline(entry, description)

        # Funder: prefiere el hint del feed; si no, intenta del autor del entry
        funder_name = feed.funder_hint or _extract_author(entry)

        return OpportunityCreate(
            title=title,
            description=description if description else None,
            funder_name=funder_name,
            deadline=deadline,
            url_rfp=url_rfp,
            url_source=url_rfp or feed.url,
            source_name=f"rss:{feed.name}",
            org_website=feed.org_website,
            capital_type=feed.capital_type,
            sectors=_extract_categories(entry),
            raw_content=json.dumps({"feed": feed.name, "entry": entry}, default=str)[:10_000],
        )


def _clean_html(html: str) -> str:
    """Strip HTML tags básico sin pesar BeautifulSoup."""
    import re

    no_tags = re.sub(r"<[^>]+>", " ", html)
    no_entities = (
        no_tags.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return " ".join(no_entities.split())


def _extract_deadline(entry: dict[str, Any], description: str) -> date | None:
    """Intenta inferir deadline. Estrategia conservadora: solo formato YYYY-MM-DD explícito."""
    import re

    # 1) Campo dc:date o pubDate del entry (no es deadline pero a veces se reusa)
    # No lo usamos para deadline — es fecha de publicación.

    # 2) Buscar fechas en el texto: "Deadline: 2026-06-15" o similar
    pattern = re.compile(
        r"(?:deadline|cierre|fecha límite|due|closes?)[\s:–-]*"
        r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE,
    )
    m = pattern.search(description)
    if m:
        raw = m.group(1)
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    return None


def _extract_author(entry: dict[str, Any]) -> str | None:
    if entry.get("author"):
        return str(entry["author"])
    authors = entry.get("authors")
    if isinstance(authors, list) and authors:
        first = authors[0]
        if isinstance(first, dict):
            return first.get("name")
        return str(first)
    return None


def _extract_categories(entry: dict[str, Any]) -> list[str]:
    cats = entry.get("tags") or entry.get("categories") or []
    out: list[str] = []
    if isinstance(cats, list):
        for c in cats:
            if isinstance(c, dict) and c.get("term"):
                out.append(str(c["term"]))
            elif isinstance(c, str):
                out.append(c)
    return out[:10]
