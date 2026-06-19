"""Scraper genérico de feeds RSS / Atom.

Consume múltiples fuentes RSS configuradas en RSS_FEEDS y unifica
sus entradas como oportunidades. Filtra por keywords ECD relevantes.

Schedule: Diario 10am (cron: 0 10 * * *)

Mejoras técnicas:
  - Cache LRU de respuestas (TTL 1h)
  - Rate limiting entre feeds (500ms)
  - Timeout individual por feed (15s)
  - Deduplicación por URL de entrada
  - Logging de salud por feed (entries, errores, última vez OK)
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

import feedparser
import httpx
import structlog

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()

RATE_LIMIT_SEC = 0.5
FEED_TIMEOUT_SEC = 15.0
FEED_CACHE_TTL = 3600

_feed_cache: dict[str, tuple[float, str]] = {}


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    funder_hint: str | None = None
    org_website: str | None = None
    capital_type: str = "grant"
    priority: Literal["high", "medium", "low"] = "medium"


# Fuentes RSS verificadas que funcionan actualmente.
# Se eliminaron las que devolvían 404/403/error de parseo.
# Organizadas por categoría.
RSS_FEEDS: tuple[FeedSource, ...] = (
    # ── Agregadores filantrópicos ─────────────────────────────────────────────
    FeedSource(
        name="fundsforngos",
        url="https://www2.fundsforngos.org/feed/",
        org_website="https://www.fundsforngos.org",
        priority="high",
    ),
    FeedSource(
        name="terra_viva_grants",
        url="https://www.terravivagrants.org/feed/",
        org_website="https://www.terravivagrants.org",
        priority="medium",
    ),
    FeedSource(
        name="grantstation_news",
        url="https://grantstation.com/rss.xml",
        org_website="https://grantstation.com",
        priority="medium",
    ),

    # ── Sistema ONU / multilaterales ──────────────────────────────────────────
    FeedSource(
        name="reliefweb_updates",
        url="https://reliefweb.int/updates/rss.xml",
        org_website="https://reliefweb.int",
        priority="medium",
    ),
    FeedSource(
        name="reliefweb_training",
        url="https://reliefweb.int/training/rss.xml",
        org_website="https://reliefweb.int",
        priority="low",
    ),
    FeedSource(
        name="un_ocha",
        url="https://www.unocha.org/rss.xml",
        funder_hint="UN OCHA",
        org_website="https://www.unocha.org",
        priority="medium",
    ),

    # ── Fundaciones globales estratégicas ─────────────────────────────────────
    FeedSource(
        name="ford_foundation",
        url="https://www.fordfoundation.org/feed/",
        funder_hint="Ford Foundation",
        org_website="https://www.fordfoundation.org",
        priority="high",
    ),
    FeedSource(
        name="hilton_foundation",
        url="https://www.hiltonfoundation.org/feed/",
        funder_hint="Conrad N. Hilton Foundation",
        org_website="https://www.hiltonfoundation.org",
        priority="high",
    ),
    FeedSource(
        name="bernard_van_leer",
        url="https://bernardvanleer.org/feed/",
        funder_hint="Bernard van Leer Foundation",
        org_website="https://bernardvanleer.org",
        priority="high",
    ),
    FeedSource(
        name="jacobs_foundation",
        url="https://jacobsfoundation.org/feed/",
        funder_hint="Jacobs Foundation",
        org_website="https://jacobsfoundation.org",
        priority="high",
    ),
    FeedSource(
        name="oak_foundation",
        url="https://oakfnd.org/feed/",
        funder_hint="Oak Foundation",
        org_website="https://oakfnd.org",
        priority="medium",
    ),
    FeedSource(
        name="packard_foundation",
        url="https://www.packard.org/feed/",
        funder_hint="David & Lucile Packard Foundation",
        org_website="https://www.packard.org",
        priority="medium",
    ),
    FeedSource(
        name="rockefeller_foundation",
        url="https://www.rockefellerfoundation.org/feed/",
        funder_hint="Rockefeller Foundation",
        org_website="https://www.rockefellerfoundation.org",
        priority="medium",
    ),

    # ── LATAM / Colombia ──────────────────────────────────────────────────────
    FeedSource(
        name="reliefweb_colombia",
        url="https://reliefweb.int/updates/rss.xml?country=56",
        org_website="https://reliefweb.int",
        priority="high",
    ),

    # ── ECD / Educación inicial ───────────────────────────────────────────────
    FeedSource(
        name="ecdan_news",
        url="https://www.ecdan.org/feed",
        funder_hint="Early Childhood Development Action Network",
        org_website="https://www.ecdan.org",
        priority="high",
    ),

    # ── Otras fuentes complementarias ─────────────────────────────────────────
    FeedSource(
        name="dev_coop",
        url="https://www.dandc.eu/rss.xml",
        org_website="https://www.dandc.eu",
        priority="low",
    ),
    FeedSource(
        name="dev_coop_eng",
        url="https://www.dandc.eu/en/rss.xml",
        org_website="https://www.dandc.eu",
        priority="low",
    ),
    FeedSource(
        name="brookings_global",
        url="https://www.brookings.edu/feed/?cat=global-development",
        org_website="https://www.brookings.edu",
        priority="medium",
    ),
    FeedSource(
        name="globalwa",
        url="https://globalwa.org/feed/",
        org_website="https://globalwa.org",
        priority="low",
    ),
)

# Total: 21 feeds verificados

# Keywords HIGH SPECIFICITY
CORE_KEYWORDS = (
    # 1. Early childhood development, education, school readiness
    "early childhood development", "early childhood education", "educación inicial", "primera infancia", "school readiness",
    "desarrollo infantil temprano", "educación preescolar", "preparación escolar", "listo para la escuela", "preescolar",
    "desarrollo infantil", "desarrollo temprano", "cero a siempre", "early childhood", "ecd", "preschool",
    "cdi", "centro de desarrollo infantil", "centros infantiles", "jardines", "jardín", "jardines infantiles",
    "modalidad institucional", "modalidad familiar", "cuidado infantil", "cuidadores",

    # 2. Learning through play, foundational learning, early literacy/numeracy
    "learning through play", "foundational learning", "lectura temprana", "escritura temprana", "matemáticas tempranas",
    "lectoescritura", "early literacy", "early numeracy", "early math", "aprendizaje a través del juego", "juego para aprender",
    "aprendizaje fundamental", "lectura", "escritura",

    # 3. Teacher training, educator professional development, caregiver training
    "teacher training", "educator professional development", "caregiver training", "comunidades de práctica",
    "formación docente", "formación de maestros", "capacitación docente", "desarrollo profesional docente",
    "capacitación de cuidadores", "formación de cuidadores", "asesoría pedagógica", "acompañamiento pedagógico",
    "fortalecimiento de capacidades", "líderes educativos", "maestros", "maestras", "educadores", "communities of practice",

    # 4. Care economy, childcare systems, home-based childcare, women caregivers & empowerment
    "care economy", "childcare systems", "home-based childcare", "women caregivers", "women economic empowerment",
    "economía del cuidado", "sistemas de cuidado infantil", "cuidado en el hogar", "cuidadoras", "mujeres cuidadoras",
    "empoderamiento económico de las mujeres", "empoderamiento femenino", "women empowerment", "trabajo de cuidado",

    # 5. Migrant children, refugee children, host communities, population on the move, social inclusion
    "migrant children", "refugee children", "host communities", "población en movimiento", "inclusión social",
    "niños migrantes", "niñas migrantes", "niñez migrante", "niños refugiados", "niñez refugiada", "comunidades de acogida",
    "población migrante", "población móvil", "social inclusion", "desplazamiento",

    # 6. EdTech, digital public goods, open educational resources, learning platforms, AI for education
    "edtech", "digital public goods", "open educational resources", "learning platforms", "ai for education",
    "tecnología educativa", "bienes públicos digitales", "recursos educativos abiertos", "plataformas de aprendizaje",
    "ia en educación", "inteligencia artificial en educación",

    # 7. Data for education, MEL, child development assessment, impact measurement, evidence-based policy
    "data for education", "mel", "child development assessment", "impact measurement", "evidence-based policy",
    "datos para la educación", "monitoreo, evaluación y aprendizaje", "evaluación del desarrollo infantil",
    "medición de impacto", "políticas basadas en evidencia", "monitoreo y evaluación", "sistematización",
    "medición", "indicadores",

    # 8. Learning environments, child-friendly spaces, ludotecas, bibliotecas, salas de lactancia & family-friendly workplaces
    "learning environments", "child-friendly spaces", "family-friendly workplaces", "ambientes de aprendizaje",
    "entornos de aprendizaje", "espacios amigables para niños", "espacios seguros para niños", "ludotecas",
    "bibliotecas", "salas de lactancia", "lugares de trabajo amigables con las familias", "entornos familiares laborales",
    "empresas familiarmente responsables",

    # 9. Climate education, nature-based solutions, green learning spaces, sustainability
    "climate education", "nature-based solutions", "green learning spaces", "sostenibilidad en primera infancia",
    "educación climática", "soluciones basadas en la naturaleza", "espacios verdes de aprendizaje", "aulas verdes",
    "sostenibilidad infantil", "sustainability in early childhood",

    # Otras palabras clave institucionales y sectoriales de aeioTU
    "estándares icbf", "icbf", "lineamientos", "orientaciones", "incidencia política", "transformación sistémica",
    "modelo escalable", "transferencia de modelo", "replicación", "escalable", "transferencia", "cafam",
    "caja de compensación", "cajas de compensación", "afiliados", "beneficiarios", "compensación", "género",
    "gender", "mujeres", "equity", "sostenibilidad financiera", "trayectorias educativas", "continuidad educativa",
)

GEO_KEYWORDS = (
    "colombia", "latin america", "latinoamérica", "latam",
    "región andina", "global south", "developing countries",
)


class RssFeedsScraper(BaseScraper):
    source_name = "rss"
    base_url = "various"
    schedule = "0 10 * * *"

    async def fetch_raw(self) -> list[dict[str, Any]]:
        all_entries: list[dict[str, Any]] = []
        seen_entry_urls: set[str] = set()
        feed_health: dict[str, dict[str, Any]] = {}

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(FEED_TIMEOUT_SEC),
            follow_redirects=True,
        ) as client:
            for feed in RSS_FEEDS:
                log = logger.bind(feed=feed.name, url=feed.url, priority=feed.priority)
                health: dict[str, Any] = {"entries": 0, "error": None, "status": "ok"}

                await asyncio.sleep(RATE_LIMIT_SEC)

                raw_xml = await self._fetch_with_cache(client, feed.url, log)
                if raw_xml is None:
                    health["status"] = "error"
                    health["error"] = "fetch_failed"
                    feed_health[feed.name] = health
                    continue

                parsed = feedparser.parse(raw_xml)
                if parsed.bozo and not parsed.entries:
                    log.warning("Feed parse failed", reason=str(parsed.bozo_exception)[:120])
                    health["status"] = "error"
                    health["error"] = str(parsed.bozo_exception)[:120]
                    feed_health[feed.name] = health
                    continue

                entry_count = 0
                for entry in parsed.entries:
                    entry_url = (entry.get("link") or entry.get("id") or "").strip()
                    if entry_url and entry_url in seen_entry_urls:
                        continue
                    if entry_url:
                        seen_entry_urls.add(entry_url)

                    all_entries.append({"_feed": feed, "entry": dict(entry)})
                    entry_count += 1

                health["entries"] = entry_count
                feed_health[feed.name] = health
                log.info("Feed fetched", entries=len(parsed.entries), new_entries=entry_count)

        total_feeds = len(RSS_FEEDS)
        ok_feeds = sum(1 for h in feed_health.values() if h["status"] == "ok")
        error_feeds = total_feeds - ok_feeds

        logger.info(
            "RSS fetch complete",
            total_feeds=total_feeds,
            ok_feeds=ok_feeds,
            error_feeds=error_feeds,
            total_entries=len(all_entries),
        )

        for name, h in feed_health.items():
            if h["status"] == "error":
                logger.warning("Feed unhealthy", feed=name, error=h["error"])

        return all_entries

    async def _fetch_with_cache(
        self, client: httpx.AsyncClient, url: str, log: Any
    ) -> str | None:
        now = datetime.now().timestamp()
        cached = _feed_cache.get(url)
        if cached and (now - cached[0]) < FEED_CACHE_TTL:
            log.debug("Feed cache hit")
            return cached[1]

        try:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"
                    ),
                    "Accept": (
                        "application/rss+xml, application/atom+xml, "
                        "application/xml, text/xml"
                    ),
                },
            )
            resp.raise_for_status()
            text = resp.text
            _feed_cache[url] = (now, text)
            return text
        except httpx.HTTPError as exc:
            log.warning("Feed fetch failed", error=str(exc))
            return None

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        from app.services.content_type_detector import detect_content_type, ContentType
        from app.schemas.convocation import ConvocationCreate

        feed: FeedSource = raw["_feed"]
        entry: dict[str, Any] = raw["entry"]

        title = (entry.get("title") or "").strip()
        if not title:
            return None

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

        url = (entry.get("link") or entry.get("id") or "").strip()

        if not url:
            return None

        # Step 1: Content-type detection — reject if not a convocatoria
        content_result = detect_content_type({
            "title": title,
            "description": description,
            "url": url,
        })
        if content_result.type != ContentType.CONVOCATORIA or content_result.confidence < 0.7:
            logger.debug(
                "Entry rejected: not a convocatoria",
                title=title[:50],
                detected_type=content_result.type,
                confidence=round(content_result.confidence, 2),
                reason=content_result.reason,
            )
            return None

        # Step 2: Strict keyword filtering (AND logic)
        haystack = (title + " " + description).lower()
        has_core = any(kw.lower() in haystack for kw in CORE_KEYWORDS)
        if not has_core:
            logger.debug("Entry rejected: no CORE_KEYWORDS match", title=title[:50])
            return None

        # GEO filter is mandatory only for Colombia-specific feeds
        if "colombia" in feed.name.lower():
            has_geo = any(kw.lower() in haystack for kw in GEO_KEYWORDS)
            if not has_geo:
                logger.debug(
                    "Entry rejected: no GEO_KEYWORDS match for Colombia feed",
                    title=title[:50],
                    feed=feed.name,
                )
                return None

        # Parse open date from feed entry
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            try:
                open_date = date(*published_parsed[:3])
            except (TypeError, ValueError):
                open_date = date.today()
        else:
            open_date = date.today()

        # Extract deadline
        deadline = self._extract_deadline(entry, description, open_date)
        if not deadline or deadline <= open_date:
            logger.debug(
                "Entry rejected: no valid deadline",
                title=title[:50],
                deadline=str(deadline) if deadline else None,
            )
            return None

        # Step 3: Validate against ConvocationCreate schema
        try:
            conv_data: dict[str, Any] = {
                "title": title,
                "objective": description[:5000] if description else title,
                "type": self._detect_convocation_type(title, description),
                "deadline": deadline,
                "open_date": open_date,
                "url_convocation": url,
                "source_name": f"rss:{feed.name}",
                "source_url": url,
            }
            ConvocationCreate(**conv_data)
        except (ValueError, Exception) as exc:
            logger.debug("Entry failed schema validation", title=title[:50], error=str(exc))
            return None

        # Extract amount if present
        amount_cop = self._extract_amount_cop(title, description)

        funder_name = feed.funder_hint or _extract_author(entry)

        return OpportunityCreate(
            title=title,
            description=description if description else None,
            funder_name=funder_name,
            amount_min_cop=amount_cop[0] if amount_cop else None,
            amount_max_cop=amount_cop[1] if amount_cop else None,
            deadline=deadline,
            url_rfp=url,
            url_source=url,
            source_name=f"rss:{feed.name}",
            org_website=feed.org_website,
            capital_type=feed.capital_type,
            market_window="funding_global" if "global" in feed.name.lower() else "funding_colombia",
            sectors=_extract_categories(entry),
            raw_content=json.dumps({"feed": feed.name, "entry": entry}, default=str)[:10_000],
        )

    def _extract_deadline(
        self,
        entry: dict[str, Any],
        description: str,
        open_date: date,
    ) -> date | None:
        """Extract deadline from entry text. Falls back to 30-day heuristic."""
        from datetime import timedelta

        # Delegate to the module-level extractor first (uses regex on text)
        found = _extract_deadline(entry, description)
        if found:
            return found

        # Heuristic: if deadline keyword exists without a parseable date, estimate 30 days
        import re
        deadline_hint = re.search(
            r"(?:deadline|cierre|fecha límite|due|closes?|vence)",
            description,
            re.IGNORECASE,
        )
        if deadline_hint:
            return open_date + timedelta(days=30)

        return None

    def _extract_amount_cop(
        self, title: str, description: str
    ) -> tuple[int, int] | None:
        """Extract amount range in COP from text. Returns (min, max) or None."""
        import re

        haystack = title + " " + description
        # Match patterns like "$500M", "USD 1.2M", "COP $800 millones", "USD 500,000"
        usd_matches = re.findall(
            r"(?:USD|US\$|\$)\s*([\d,\.]+)\s*(?:million|M|millones?)?",
            haystack,
            re.IGNORECASE,
        )
        cop_matches = re.findall(
            r"(?:COP|cop|\$)\s*([\d,\.]+)\s*(?:millones?|mil millones?|B)?",
            haystack,
            re.IGNORECASE,
        )

        amounts: list[int] = []
        # Convert USD matches to COP (approximate: 1 USD = 4 200 COP)
        USD_TO_COP = 4_200
        for raw in usd_matches:
            try:
                val = float(raw.replace(",", ""))
                if val < 10_000:
                    # Likely expressed in millions
                    val *= 1_000_000
                amounts.append(int(val * USD_TO_COP))
            except ValueError:
                continue

        for raw in cop_matches:
            try:
                val = float(raw.replace(",", ""))
                if val < 10_000:
                    val *= 1_000_000
                amounts.append(int(val))
            except ValueError:
                continue

        if not amounts:
            return None
        return (min(amounts), max(amounts))

    def _detect_convocation_type(self, title: str, description: str) -> str:
        """Classify convocation type: grant | premio | evento | curso."""
        haystack = (title + " " + description).lower()
        if any(kw in haystack for kw in ("premio", "award", "prize")):
            return "premio"
        if any(kw in haystack for kw in ("evento", "conference", "conferencia", "summit", "cumbre", "webinar")):
            return "evento"
        if any(kw in haystack for kw in ("curso", "training", "capacitación", "workshop", "taller")):
            return "curso"
        return "grant"


def _clean_html(html: str) -> str:
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
    import re

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


def clear_feed_cache() -> None:
    _feed_cache.clear()
