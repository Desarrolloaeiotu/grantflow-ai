"""Scraper de oportunidades nacionales colombianas.

Sources:
- ICBF (Instituto Colombiano de Bienestar Familiar): https://www.icbf.gov.co
- MinEducación: https://www.mineducacion.gov.co
- Plataforma de contratación pública (SECOP): https://www.contratos.gov.co
- Cajas de Compensación: búsqueda directa
- Fundaciones locales: búsqueda genérica

Schedule: Diario 5am (antes de otros scrapers, para priorizar)
Prioridad: Módulo Nacional Colombia según CLAUDE.md §16

Keywords busca automáticamente:
- Primera infancia, educación inicial, desarrollo infantil
- CDI, Centro de Desarrollo Infantil
- Formación docente, acompañamiento pedagógico
- CERO A SIEMPRE, estándares ICBF
- Economía del cuidado, cajas de compensación
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()

# Palabras clave que definen una oportunidad relevante para Nacional Colombia
NACIONAL_KEYWORDS = (
    # Educación inicial / Primera infancia
    "primera infancia", "educación inicial", "educación preescolar",
    "desarrollo infantil", "desarrollo temprano",
    "early childhood", "ecd", "preschool",

    # CDI y operación
    "cdi", "centro de desarrollo infantil", "centros infantiles",
    "modalidad institucional", "modalidad familiar",
    "cuidado infantil", "cuidadores",

    # Docentes y formación
    "formación docente", "capacitación docentes",
    "acompañamiento pedagógico", "asesoría pedagógica",
    "fortalecimiento de capacidades",

    # Política pública
    "cero a siempre", "política pública", "política educativa",
    "estándares icbf", "lineamientos", "orientaciones mineducación",

    # Cajas de compensación
    "cafam", "caja de compensación", "cajas de compensación",
    "afiliados", "beneficiarios",

    # Economía del cuidado
    "economía del cuidado", "sostenibilidad financiera",
    "modelo escalable", "transferencia de modelo",
)

USER_AGENT = "Mozilla/5.0 (compatible; GrantFlow-AI/1.0; +https://aeiotu.org)"


class NacionalColombiaScraper(BaseScraper):
    """Scraper de oportunidades nacionales colombianas."""

    source_name = "nacional_colombia"
    base_url = "https://www.icbf.gov.co"
    schedule = "0 5 * * *"  # 5am diario — antes que otros scrapers

    async def fetch_raw(self) -> list[dict[str, Any]]:
        """Busca en múltiples fuentes nacionales colombianas."""
        all_items: list[dict[str, Any]] = []

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            # Fuente 1: ICBF convocatorias
            icbf_items = await self._fetch_icbf(client)
            all_items.extend(icbf_items)

            # Fuente 2: MinEducación convocatorias
            min_items = await self._fetch_mineducacion(client)
            all_items.extend(min_items)

            # Fuente 3: SECOP (plataforma de contratación pública)
            secop_items = await self._fetch_secop(client)
            all_items.extend(secop_items)

            # Fuente 4: Búsqueda genérica de Cajas de Compensación
            cajas_items = await self._fetch_cajas(client)
            all_items.extend(cajas_items)

            # Fuente 5: RSS feeds y noticias de oportunidades de educación
            rss_items = await self._fetch_news_feeds(client)
            all_items.extend(rss_items)

        logger.info(
            "Nacional Colombia fetch complete",
            total=len(all_items),
            icbf=len(icbf_items) if icbf_items else 0,
            mineducacion=len(min_items) if min_items else 0,
            secop=len(secop_items) if secop_items else 0,
            cajas=len(cajas_items) if cajas_items else 0,
            rss=len(rss_items) if rss_items else 0,
        )
        return all_items

    async def _fetch_icbf(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca convocatorias del ICBF enfocadas en primera infancia."""
        items = []
        urls = [
            "https://www.icbf.gov.co/convocatorias",
            "https://www.icbf.gov.co/es/convocatorias-abiertas",
        ]

        for url in urls:
            try:
                resp = await client.get(url, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Buscar enlaces más relevantes (evitar CNSC/selección personal)
                links = soup.select(
                    "a[href*='llamado'], a[href*='oportunidad'], "
                    "a[href*='financ'], a[href*='subsidio'], "
                    "a[href*='primera'], a[href*='infantil'], "
                    "article a, .content a, .node a"
                )

                page_items = 0
                for link in links[:30]:
                    href = link.get("href", "").strip()
                    title = link.get_text(strip=True)

                    # Evitar links de selección personal / CNSC
                    if "cnsc" in href.lower() or "seleccion" in href.lower():
                        continue

                    if href and title and 10 <= len(title) <= 300:
                        if not href.startswith("http"):
                            href = "https://www.icbf.gov.co" + href if href.startswith("/") else "https://www.icbf.gov.co/" + href

                        items.append({
                            "title": title,
                            "url": href,
                            "source": "icbf",
                            "funder": "Instituto Colombiano de Bienestar Familiar (ICBF)",
                        })
                        page_items += 1

                logger.info("ICBF page parsed", url=url, links_found=page_items, total=len(items))
            except httpx.HTTPError as exc:
                logger.warning("ICBF fetch failed", url=url, error=str(exc))
                continue

        return items

    async def _fetch_mineducacion(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca convocatorias del Ministerio de Educación Nacional para primera infancia."""
        items = []
        urls = [
            "https://www.mineducacion.gov.co/portal/",
            "https://www.mineducacion.gov.co/convocatorias",
            "https://www.mineducacion.gov.co/node",
        ]

        for url in urls:
            try:
                resp = await client.get(url, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Buscar enlaces de oportunidades/llamados (evitar contenido genérico)
                links = soup.select(
                    "a[href*='llamado'], a[href*='oportunidad'], "
                    "a[href*='convocatoria'], a[href*='financ'], "
                    "a[href*='primera'], a[href*='infantil'], "
                    "a[href*='preescolar'], a[href*='cdi'], "
                    "div.node a, .content a, article a"
                )

                page_items = 0
                for link in links[:30]:
                    href = link.get("href", "").strip()
                    title = link.get_text(strip=True)

                    if href and title and 10 <= len(title) <= 300:
                        if not href.startswith("http"):
                            href = "https://www.mineducacion.gov.co" + href if href.startswith("/") else "https://www.mineducacion.gov.co/" + href

                        items.append({
                            "title": title,
                            "url": href,
                            "source": "mineducacion",
                            "funder": "Ministerio de Educación Nacional",
                        })
                        page_items += 1

                logger.info("MinEducación page parsed", url=url, links_found=page_items, total=len(items))
            except httpx.HTTPError as exc:
                logger.warning("MinEducación fetch failed", url=url, error=str(exc))
                continue

        return items

    async def _fetch_secop(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca en SECOP (Sistema Electrónico de Contratación Pública).

        SECOP es la fuente oficial de contratos públicos en Colombia.
        Busca procesos abiertos de contratación en educación inicial.
        """
        items = []

        # Búsqueda con múltiples términos para máxima cobertura
        search_terms = [
            ("educación inicial", "primary"),
            ("primera infancia", "primary"),
            ("CDI", "primary"),
            ("formación docente", "secondary"),
            ("desarrollo infantil", "secondary"),
            ("acompañamiento pedagógico", "secondary"),
        ]

        for term, priority in search_terms:
            # Intentar múltiples endpoints SECOP
            urls = [
                "https://www.contratos.gov.co/consultar/buscador",
                "https://www.contratos.gov.co/search",
            ]

            for base_url in urls:
                params = {
                    "buscador": term,
                    "estado": "Publicada",
                    "pp": 100,
                }

                try:
                    resp = await client.get(base_url, params=params, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Selectores amplios para diferentes versiones de SECOP
                    results = soup.select(
                        "div.resultado, div.result, tr[data-id], "
                        ".proceso-item, .licitacion-item, "
                        "table tbody tr, .search-result"
                    )

                    page_items = 0
                    for result in results[:50]:
                        # Extraer título y URL
                        link = result.select_one("a[href*='consultar'], a[href*='process']") or result.select_one("a")
                        if not link:
                            continue

                        href = link.get("href", "").strip()
                        title_elem = result.select_one("h3, h4, h5, .title, td:nth-child(1)") or link
                        title = title_elem.get_text(strip=True) if title_elem else ""

                        # Validar URL y título
                        if not title or len(title) < 10:
                            continue
                        if not href or not href.startswith("http"):
                            if href.startswith("/"):
                                href = "https://www.contratos.gov.co" + href
                            else:
                                continue

                        items.append({
                            "title": title,
                            "url": href,
                            "source": "secop",
                            "funder": "Entidad pública colombiana (SECOP)",
                            "search_term": term,
                            "priority": priority,
                        })
                        page_items += 1

                    if page_items > 0:
                        logger.info("SECOP search completed", term=term, base_url=base_url, results=page_items, total=len(items))
                        break  # Si encontró resultados en este endpoint, no probar el siguiente
                except httpx.HTTPError as exc:
                    logger.debug("SECOP endpoint failed", term=term, url=base_url, error=str(exc)[:100])
                    continue

        return items

    async def _fetch_cajas(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca oportunidades y programas de Cajas de Compensación.

        Cajas de compensación ofrecen programas de formación y educación
        para sus afiliados, incluyendo primera infancia/jardinería.
        """
        items = []

        cajas = [
            {
                "name": "CAFAM",
                "url": "https://www.cafam.com.co",
                "paths": ["/servicios/educacion", "/programas/educacion", "/oportunidades", "/servicios"],
                "keywords": ["educacion", "infantil", "jardin", "formacion"],
            },
            {
                "name": "Caja Nariño",
                "url": "https://www.cajanario.com.co",
                "paths": ["/servicios", "/programas", "/oportunidades"],
                "keywords": ["educacion", "infantil", "jardin"],
            },
            {
                "name": "Caja Popular",
                "url": "https://www.cajapopular.com.co",
                "paths": ["/servicios", "/programas", "/educacion"],
                "keywords": ["educacion", "infantil"],
            },
            {
                "name": "Caja de Compensación Familiar Colombiana",
                "url": "https://www.cafacol.com.co",
                "paths": ["/servicios", "/programas"],
                "keywords": ["educacion", "infantil"],
            },
        ]

        for caja in cajas:
            paths = caja.get("paths", ["/programas", "/servicios"])

            for search_path in paths:
                try:
                    base_url = caja["url"].rstrip("/")
                    full_url = base_url + search_path

                    resp = await client.get(full_url, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Buscar enlaces de programas educativos
                    links = soup.select(
                        "a[href*='programa'], a[href*='servicio'], "
                        "a[href*='educacion'], a[href*='infantil'], a[href*='jardin'], "
                        ".programa a, .servicio a, .card a, .item a, "
                        ".service-item a, .program-item a"
                    )

                    page_items = 0
                    for link in links[:20]:
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)

                        # Filtrar por relevancia
                        if not href or not title or not (10 <= len(title) <= 300):
                            continue

                        # Validar que sea educación-relacionado
                        title_lower = title.lower()
                        has_edu_keyword = any(kw in title_lower for kw in caja.get("keywords", []))
                        if not has_edu_keyword:
                            continue

                        # Normalizar URL
                        if not href.startswith("http"):
                            href = base_url + href if href.startswith("/") else base_url + "/" + href

                        items.append({
                            "title": title,
                            "url": href,
                            "source": "caja",
                            "funder": caja["name"],
                            "organization": caja["name"],
                        })
                        page_items += 1

                    if page_items > 0:
                        logger.info("Caja page parsed", caja=caja["name"], path=search_path, links=page_items, total=len(items))
                except httpx.HTTPError as exc:
                    logger.warning("Caja fetch failed", caja=caja["name"], path=search_path, error=str(exc)[:100])
                    continue

        return items

    async def _fetch_news_feeds(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca en Google News y RSS feeds sobre educación inicial en Colombia.

        Detecta anuncios públicos de convocatorias, programas y oportunidades
        de financiamiento relacionadas con primera infancia.
        """
        items = []

        # Google News search para educación inicial en Colombia
        google_news_queries = [
            "educación inicial colombia convocatoria 2026",
            "primera infancia colombia llamado",
            "jardines infantiles colombia financiamiento",
            "formación docente colombia oportunidades",
        ]

        for query in google_news_queries:
            try:
                # Google News RSS feed
                url = f"https://news.google.com/rss/search?q={query}"
                resp = await client.get(url, timeout=15)
                resp.raise_for_status()

                try:
                    root = ET.fromstring(resp.content)
                    # Namespace para Google News
                    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}

                    for item in root.findall(".//item")[:10]:
                        title_elem = item.find("title")
                        link_elem = item.find("link")
                        desc_elem = item.find("description")

                        if title_elem is not None and link_elem is not None:
                            title = title_elem.text or ""
                            link = link_elem.text or ""
                            description = desc_elem.text or "" if desc_elem is not None else ""

                            if title and link and len(title) > 10:
                                items.append({
                                    "title": title,
                                    "url": link,
                                    "source": "news",
                                    "description": description[:500],
                                    "funder": "Anuncio público (Google News)",
                                    "search_query": query,
                                })

                    logger.info("Google News feed parsed", query=query, results=len(items))
                except ET.ParseError as e:
                    logger.debug("Could not parse RSS XML", error=str(e)[:100])
                    continue

            except httpx.HTTPError as exc:
                logger.warning("Google News fetch failed", query=query, error=str(exc)[:100])
                continue

        # RSS feeds de instituciones colombianas
        rss_feeds = [
            ("https://www.icbf.gov.co/rss", "ICBF"),
            ("https://www.mineducacion.gov.co/rss", "MinEducación"),
        ]

        for feed_url, source_name in rss_feeds:
            try:
                resp = await client.get(feed_url, timeout=15)
                resp.raise_for_status()

                try:
                    root = ET.fromstring(resp.content)

                    for item in root.findall(".//item")[:15]:
                        title_elem = item.find("title")
                        link_elem = item.find("link")
                        desc_elem = item.find("description")

                        if title_elem is not None and link_elem is not None:
                            title = title_elem.text or ""
                            link = link_elem.text or ""
                            description = desc_elem.text or "" if desc_elem is not None else ""

                            if title and link and len(title) > 10:
                                items.append({
                                    "title": title,
                                    "url": link,
                                    "source": "rss",
                                    "description": description[:500],
                                    "funder": source_name,
                                })

                    logger.info("RSS feed parsed", source=source_name, results=len(items))
                except ET.ParseError:
                    logger.debug("Could not parse RSS feed", source=source_name)
                    continue

            except httpx.HTTPError as exc:
                logger.warning("RSS feed fetch failed", source=source_name, error=str(exc)[:100])
                continue

        return items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convierte registro crudo a OpportunityCreate.

        Filtra por relevancia a primera infancia/educación inicial.
        """
        title = raw.get("title", "").strip()
        if not title or len(title) < 10:
            return None

        url = raw.get("url", "").strip()
        if not url or not url.startswith("http"):
            return None

        # Buscar descripción en la página (opcional)
        description = raw.get("description", "")

        # Filtro de relevancia: REQUERIDO contener al menos una palabra clave
        haystack = (title + " " + url + " " + description).lower()

        # Rechazar explícitamente si contiene palabras de selección/RRHH
        reject_keywords = (
            "seleccion", "personal", "cnsc", "rrhh", "empleo",
            "vacante", "puesto", "candidato", "cv",
            "error", "404", "no encontrado"
        )
        if any(kw in haystack for kw in reject_keywords):
            logger.debug("Nacional opp rejected", title=title[:60], reason="reject_keyword")
            return None

        # REQUERIDO: contener al menos una palabra clave positiva
        if not any(kw in haystack for kw in NACIONAL_KEYWORDS):
            logger.debug("Nacional opp rejected", title=title[:60], reason="no_positive_keyword")
            return None

        logger.debug("Nacional opp accepted", title=title[:60])

        # Parseear deadline si existe (formato flexible)
        deadline = self._parse_deadline(raw.get("deadline_text"))

        return OpportunityCreate(
            title=title,
            description=description[:2000] or None,
            funder_name=raw.get("funder", "Entidad pública/privada colombiana"),
            deadline=deadline,
            url_rfp=url,
            url_source=url,
            source_name=self.source_name,
            org_website=raw.get("funder_url", ""),
            eligible_countries=["Colombia"],
            sectors=["educacion_inicial", "primera_infancia"],
            capital_type="consultoria",
            raw_content=json.dumps(raw, default=str)[:10_000],
        )

    @staticmethod
    def _parse_deadline(raw: str | None) -> date | None:
        """Parsea fecha en múltiples formatos comunes en Colombia."""
        if not raw:
            return None

        raw = raw.strip()

        # Intentar formatos comunes
        for fmt in (
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
            "%d de %B de %Y", "%d de %b de %Y",
            "%B %d, %Y", "%b %d, %Y",
        ):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue

        # Regex para "dd de mes de yyyy"
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
            raw,
            re.IGNORECASE,
        )
        if match:
            day, month_str, year = match.groups()
            months = {
                "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
            }
            month = months.get(month_str.lower())
            if month:
                try:
                    return date(int(year), month, int(day))
                except ValueError:
                    pass

        return None
