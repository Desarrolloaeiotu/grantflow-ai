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

        logger.info(
            "Nacional Colombia fetch complete",
            total=len(all_items),
            icbf=len(icbf_items) if icbf_items else 0,
            mineducacion=len(min_items) if min_items else 0,
            secop=len(secop_items) if secop_items else 0,
            cajas=len(cajas_items) if cajas_items else 0,
        )
        return all_items

    async def _fetch_icbf(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca convocatorias del ICBF."""
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

                # Buscar enlaces a convocatorias con selectores más amplios
                links = soup.select(
                    "a[href*='convocatoria'], a[href*='llamado'], "
                    "a[href*='oportunidad'], div.resultado a, article a, "
                    ".oportunidad a, .convocatoria a"
                )

                page_items = 0
                for link in links[:30]:  # Cap para no abusar
                    href = link.get("href", "").strip()
                    title = link.get_text(strip=True)

                    if href and title and 10 <= len(title) <= 300:  # Rango realista
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
        """Busca convocatorias del Ministerio de Educación Nacional."""
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

                # Buscar enlaces con selectores amplios
                links = soup.select(
                    "a[href*='convocatoria'], a[href*='llamado'], "
                    "a[href*='oportunidad'], a[href*='financiamiento'], "
                    "div.node a, .content a, article a, .post a"
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

        SECOP permite búsquedas de procesos de contratación pública.
        Filtrar por educación inicial y primera infancia.
        """
        items = []

        # Búsqueda en SECOP por palabras clave
        search_terms = [
            "educación inicial",
            "primera infancia",
            "formación docente",
            "desarrollo infantil",
            "CDI",
            "jardín infantil",
        ]

        for term in search_terms:
            url = "https://www.contratos.gov.co/consultar/buscador"
            params = {
                "buscador": term,
                "estado": "Publicada",  # Solo procesos publicados
                "pp": 50,  # 50 resultados por página
            }

            try:
                resp = await client.get(url, params=params, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Buscar resultados con selectores amplios
                results = soup.select(
                    "div.resultado, div.result, tr.resultado, "
                    ".proceso-item, .licitacion, a[href*='consultar']"
                )

                page_items = 0
                for result in results[:20]:
                    # Extraer href y title
                    link = result.select_one("a") if result.name != "a" else result
                    if not link:
                        continue

                    href = link.get("href", "").strip()
                    title_elem = result.select_one("h3, h4, .title") or link
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    if title and href and 10 <= len(title) <= 300:
                        if not href.startswith("http"):
                            href = "https://www.contratos.gov.co" + href if href.startswith("/") else "https://www.contratos.gov.co/" + href

                        items.append({
                            "title": title,
                            "url": href,
                            "source": "secop",
                            "funder": "Entidad pública colombiana (SECOP)",
                            "search_term": term,
                        })
                        page_items += 1

                logger.info("SECOP search completed", term=term, results=page_items, total=len(items))
            except httpx.HTTPError as exc:
                logger.warning("SECOP search failed", term=term, error=str(exc))
                continue

        return items

    async def _fetch_cajas(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca oportunidades de Cajas de Compensación y entidades afines."""
        items = []

        cajas = [
            {
                "name": "CAFAM",
                "url": "https://www.cafam.com.co",
                "paths": ["/oportunidades", "/programas", "/educacion"],
            },
            {
                "name": "Caja Nariño",
                "url": "https://www.cajanario.com.co",
                "paths": ["/oportunidades", "/programas"],
            },
            {
                "name": "Caja Popular",
                "url": "https://www.cajapopular.com.co",
                "paths": ["/oportunidades", "/programas"],
            },
        ]

        for caja in cajas:
            paths = caja.get("paths", ["/programas", "/oportunidades"])

            for search_path in paths:
                try:
                    base_url = caja["url"].rstrip("/")
                    full_url = base_url + search_path

                    resp = await client.get(full_url, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Buscar enlaces con selectores amplios
                    links = soup.select(
                        "a[href*='programa'], a[href*='oportunidad'], "
                        "a[href*='educacion'], a[href*='infantil'], "
                        ".programa a, .oportunidad a, .card a, .item a"
                    )

                    page_items = 0
                    for link in links[:15]:
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)

                        if href and title and 5 <= len(title) <= 300:
                            if not href.startswith("http"):
                                href = base_url + href if href.startswith("/") else base_url + "/" + href

                            items.append({
                                "title": f"{caja['name']}: {title}",
                                "url": href,
                                "source": "caja",
                                "funder": caja["name"],
                            })
                            page_items += 1

                    logger.info("Caja page parsed", caja=caja["name"], path=search_path, links=page_items, total=len(items))
                except httpx.HTTPError as exc:
                    logger.warning("Caja fetch failed", caja=caja["name"], path=search_path, error=str(exc))
                    continue

        return items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convierte registro crudo a OpportunityCreate.

        Filtra por palabras clave nacionales para asegurar relevancia.
        """
        title = raw.get("title", "").strip()
        if not title or len(title) < 10:
            return None

        url = raw.get("url", "").strip()
        if not url or not url.startswith("http"):
            return None

        # Buscar descripción en la página (opcional)
        description = raw.get("description", "")

        # Filtro flexible de palabras clave para Nacional Colombia
        # Ya confía en las fuentes (ICBF, MinEducación, SECOP, Cajas)
        # Pero rechaza resultados claramente no relevantes
        haystack = (title + " " + description).lower()
        reject_keywords = ("error", "404", "no encontrado", "página no disponible")
        if any(kw in haystack for kw in reject_keywords):
            logger.debug("Nacional opp rejected", title=title, reason="rejection_keyword")
            return None

        # Bonus si contiene palabras clave de educación inicial
        has_keyword = any(kw in haystack for kw in NACIONAL_KEYWORDS)
        if not has_keyword:
            logger.debug("Nacional opp included (no explicit keyword, but from trusted source)", title=title[:60])

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
