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

import asyncio
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
from app.services.alert_service import AlertService

logger = structlog.get_logger()

# Palabras clave CORE para Nacional Colombia
# Dividida en CORE (muy relevante) y SECONDARY (moderadamente relevante)
# REFOZADAS para detectar las 4 oportunidades estratégicas O1-O4

NACIONAL_KEYWORDS_CORE = (
    # ── OPORTUNIDAD 1: Fortalecimiento de CDI en contextos de vulnerabilidad ────────────────
    # Gobierno, MinEducación, ICBF. Monto: COP $280-450M
    "cdi vulnerabilidad", "centros infantiles públicos", "cdi post-conflicto",
    "cdi zonas rurales", "cdi desplazamiento", "municipios vulnerables cdi",
    "formación docente contextos vulnerables", "acompañamiento pedagógico cdi",
    "transformación calidad cdi", "inclusión social cdi", "cdi contextos vulnerables",

    # ── OPORTUNIDAD 2: Programa de formación docente en primera infancia (Cajas) ─────────────
    # Cajas de Compensación, CAFAM, Caja Nariño, Caja Popular, etc. Monto: COP $180-320M
    "formación docente cafam", "diplomado primera infancia", "capacitación cuidadores",
    "modalidad familiar capacitación", "licenciamiento educación inicial",
    "acompañamiento pedagógico cajas", "formación cuidadores informales",
    "cajas compensación formación docente", "programas educación cajas",

    # ── OPORTUNIDAD 3: Acompañamiento pedagógico a jardines privados y rurales ──────────────
    # Sector educación privada. Monto: COP $120-200M
    "jardines privados educación inicial", "acompañamiento pedagógico jardines",
    "calidad educativa jardines", "transformación ambiental jardines",
    "medición desarrollo infantil jardines", "entornos aprendizaje jardines",
    "formación docente jardines privados", "jardines privados rurales",
    "acompañamiento jardines", "jardines educación inicial",

    # ── OPORTUNIDAD 4: Incidencia en política pública de primera infancia ──────────────────
    # Gobierno, ICBF, MinEducación, DNP, Cooperación Internacional. Monto: COP $200-350M
    "estándares calidad primera infancia", "política pública educación inicial",
    "lineamientos icbf", "marcos de calidad cdi", "guías primer año escuela",
    "tránsito armónico educación", "política nacional primera infancia",
    "estándares de calidad infantil", "política pública cdi", "incidencia política educación",
    "cero a siempre política", "sistema nacional atención primera infancia",

    # ── Palabras clave genéricas de ECD (existentes, mantener) ──────────────────────────────
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

NACIONAL_KEYWORDS_SECONDARY = (
    # Educación general (si es combinada con educación inicial)
    "educación", "enseñanza", "aprendizaje", "pedagogía",
    "escuela", "formación", "capacitación",

    # Infancia y vulnerabilidad
    "infancia", "niños", "niñas", "menores", "infantes",
    "vulnerabilidad", "riesgo", "pobreza", "pobreza extrema",

    # Salud y bienestar
    "salud", "nutrición", "bienestar", "cuidado",
    "desarrollo", "psicosocial",

    # Tipos de convocatorias y oportunidades solicitadas
    "convocatoria", "llamado", "oportunidad", "beca",
    "financiamiento", "recursos", "subsidio",
    "operación", "ejecución", "implementación",
    "grants", "premios", "contratos", "retos de innovación", "licitaciones",
    "alianzas directas", "fondos filantrópicos", "prizes", "awards", "tenders",
    "philanthropic funds", "alianzas", "proceso de selección", "propuesta",
)

# Combinar todas las palabras clave
NACIONAL_KEYWORDS = NACIONAL_KEYWORDS_CORE + NACIONAL_KEYWORDS_SECONDARY

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

            # Fuente 4: SENA (Servicio Nacional de Aprendizaje) — Formación docente y becas
            sena_items = await self._fetch_sena(client)
            all_items.extend(sena_items)

            # Fuente 5: Búsqueda genérica de Cajas de Compensación
            cajas_items = await self._fetch_cajas(client)
            all_items.extend(cajas_items)

            # Fuente 5: RSS feeds y noticias de oportunidades de educación
            rss_items = await self._fetch_news_feeds(client)
            all_items.extend(rss_items)

            # Fuente 6: Universidades y centros de investigación
            uni_items = await self._fetch_universities(client)
            all_items.extend(uni_items)

            # Fuente 7: Fundaciones y organismos de cooperación
            foundation_items = await self._fetch_foundations(client)
            all_items.extend(foundation_items)

            # Fuente 8: Google News y alertas públicas
            google_items = await self._fetch_google_news_alerts(client)
            all_items.extend(google_items)

            # Fuente 9: LinkedIn job postings relacionadas con oportunidades
            linkedin_items = await self._fetch_linkedin_opportunities(client)
            all_items.extend(linkedin_items)

            # Fuente 10: Twitter/X para anuncios de oportunidades
            twitter_items = await self._fetch_twitter_opportunities(client)
            all_items.extend(twitter_items)



        logger.info(
            "Nacional Colombia fetch complete",
            total=len(all_items),
            icbf=len(icbf_items) if icbf_items else 0,
            mineducacion=len(min_items) if min_items else 0,
            secop=len(secop_items) if secop_items else 0,
            sena=len(sena_items) if sena_items else 0,
            cajas=len(cajas_items) if cajas_items else 0,
            rss=len(rss_items) if rss_items else 0,
            universities=len(uni_items) if uni_items else 0,
            foundations=len(foundation_items) if foundation_items else 0,
            google=len(google_items) if google_items else 0,
            linkedin=len(linkedin_items) if linkedin_items else 0,
            twitter=len(twitter_items) if twitter_items else 0,

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
        Intenta primero SECOP 2.0 (nueva plataforma), luego SECOP 1.0 como fallback.
        """
        items = []

        # Búsqueda con múltiples términos para máxima cobertura
        search_terms = [
            "educación inicial",
            "primera infancia",
            "CDI",
            "formación docente",
            "desarrollo infantil",
            "acompañamiento pedagógico",
            "jardines infantiles",
            "centro de desarrollo infantil",
            "ludotecas",
            "salas de lactancia",
            "economía del cuidado",
            "inclusión social infantil",
            "retos de innovación educativa",
            "tecnología educativa"
        ]

        # Intentar SECOP 2.0 primero, luego SECOP 1.0 como fallback
        api_endpoints = [
            "https://www.secop.gov.co/api/v2/procesos",  # SECOP 2.0 (nueva plataforma)
            "https://www.contratos.gov.co/api/v1/search"  # SECOP 1.0 (actual)
        ]

        # Intentar cada endpoint en orden
        successful_endpoint = None
        for api_base in api_endpoints:
            endpoint_version = "2.0" if "v2" in api_base else "1.0"

            for term in search_terms[:3]:  # Probar con 3 términos primero
                try:
                    params = {
                        "q": term,
                        "filter": "status:publicada" if "v1" in api_base else "estado:publicada",
                        "size": 50,
                        "desde": 0,
                    }

                    resp = await client.get(api_base, params=params, timeout=15)

                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                            # Estructura es diferente en v1 vs v2
                            results = data.get("data", data.get("procesos", []))

                            if results:
                                successful_endpoint = api_base
                                logger.info("SECOP API working", version=endpoint_version, url=api_base)
                                break
                        except (json.JSONDecodeError, KeyError):
                            pass
                except httpx.HTTPError:
                    pass

            if successful_endpoint:
                break

        # Si no hay endpoint exitoso, usar fallback
        if not successful_endpoint:
            logger.debug("SECOP API not available, using HTML fallback")
            for term in search_terms[:5]:
                items.extend(await self._fetch_secop_web_fallback(client, term))
            return items

        # Buscar con todos los términos usando el endpoint exitoso
        for term in search_terms:
            try:
                params = {
                    "q": term,
                    "filter": "status:publicada" if "v1" in successful_endpoint else "estado:publicada",
                    "size": 50,
                    "desde": 0,
                }

                resp = await client.get(successful_endpoint, params=params, timeout=15)
                resp.raise_for_status()

                try:
                    data = resp.json()
                    # Parsear según versión
                    if "v2" in successful_endpoint:
                        results = data.get("procesos", [])
                        for result in results[:15]:
                            title = result.get("nombreProceso", "").strip()
                            if not title or len(title) < 10:
                                continue

                            process_id = result.get("idProceso", "")
                            url = f"https://www.secop.gov.co/portal/componentes/detalles/{process_id}" if process_id else ""

                            items.append({
                                "title": title,
                                "url": url,
                                "source": "secop",
                                "funder": "Entidad pública colombiana (SECOP 2.0)",
                                "search_term": term,
                                "deadline_text": result.get("fechaCierre", ""),
                            })
                    else:
                        # SECOP 1.0
                        results = data.get("data", [])
                        for result in results[:15]:
                            title = result.get("procesosContratacion", [{}])[0].get("nombreProceso", "").strip()
                            if not title or len(title) < 10:
                                continue

                            process_id = result.get("procesosContratacion", [{}])[0].get("id", "")
                            url = f"https://www.contratos.gov.co/consultar/detalle/{process_id}" if process_id else ""

                            items.append({
                                "title": title,
                                "url": url,
                                "source": "secop",
                                "funder": "Entidad pública colombiana (SECOP 1.0)",
                                "search_term": term,
                                "deadline_text": result.get("fechaCierre", ""),
                            })

                    if len(items) > 0:
                        logger.info("SECOP API search completed", term=term, results=len(items))

                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug("SECOP API response parse error", term=term, error=str(e)[:100])
                    items.extend(await self._fetch_secop_web_fallback(client, term))

            except httpx.HTTPError as exc:
                logger.debug("SECOP API request failed", term=term, error=str(exc)[:100])
                continue

        return items

    async def _fetch_secop_web_fallback(self, client: httpx.AsyncClient, term: str) -> list[dict[str, Any]]:
        """Fallback a búsqueda HTML en SECOP si la API no funciona."""
        items = []

        # Intentar búsqueda web como fallback
        search_url = "https://www.contratos.gov.co/consultar/buscador"
        params = {
            "buscador": term,
            "estado": "Publicada",
        }

        try:
            resp = await client.get(search_url, params=params, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Buscar resultados en múltiples selectores posibles
            results = soup.select(
                "div[class*='result'], tr[data-id], "
                "a[href*='detalle'], .proceso-item"
            )

            for result in results[:15]:
                title = result.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                link = result.select_one("a[href*='detalle']") or result.select_one("a")
                if not link:
                    continue

                href = link.get("href", "").strip()
                if not href.startswith("http"):
                    if href.startswith("/"):
                        href = "https://www.contratos.gov.co" + href
                    else:
                        continue

                items.append({
                    "title": title[:200],
                    "url": href,
                    "source": "secop",
                    "funder": "Entidad pública colombiana (SECOP)",
                    "search_term": term,
                })

            if items:
                logger.info("SECOP web fallback succeeded", term=term, results=len(items))
        except httpx.HTTPError as exc:
            logger.debug("SECOP web fallback failed", term=term, error=str(exc)[:100])

        return items

    async def _fetch_sena(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca programas de formación docente, becas y diplomados en SENA.

        SENA (Servicio Nacional de Aprendizaje) es la principal institución para
        formación técnica en Colombia. Ofrece:
        - Diplomados en educación inicial
        - Becas para formación docente
        - Programas de cuidado infantil
        - Programas de cuidadores informales

        Relevante para O1 (CDI públicos), O2 (formación docente) y O3 (jardines privados).
        """
        items = []

        urls = [
            "https://www.sena.edu.co/es-co/formaci%C3%B3n",
            "https://www.sena.edu.co/es-co/aspirantes/oferta-educativa",
            "https://www.sena.edu.co/es-co/beneficiarios/estudiantes/becas",
            "https://www.sena.edu.co/es-co/empresas/servicios-empresariales",
            "https://www.sena.edu.co/es-co/empresas/capacitacion-empresarial",
        ]

        search_terms = [
            "educación inicial",
            "primera infancia",
            "formación docente",
            "cuidadores",
            "jardines infantiles",
            "diplomado educación",
            "técnico educación",
        ]

        for url in urls:
            try:
                resp = await client.get(url, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Buscar enlaces de programas y oportunidades
                links = soup.select(
                    "a[href*='programa'], a[href*='oferta'], "
                    "a[href*='diplomado'], a[href*='beca'], "
                    "a[href*='formacion'], a[href*='curso'], "
                    ".programa a, .oferta a, .card a, .item a"
                )

                page_items = 0
                for link in links[:20]:
                    href = link.get("href", "").strip()
                    title = link.get_text(strip=True)

                    if not href or not title or not (10 <= len(title) <= 300):
                        continue

                    # Normalizar URL
                    if not href.startswith("http"):
                        href = "https://www.sena.edu.co" + href if href.startswith("/") else "https://www.sena.edu.co/" + href

                    items.append({
                        "title": title,
                        "url": href,
                        "source": "sena",
                        "funder": "Servicio Nacional de Aprendizaje (SENA)",
                        "organization": "SENA",
                    })
                    page_items += 1

                if page_items > 0:
                    logger.info("SENA page parsed", url=url, links=page_items, total=len(items))

            except httpx.HTTPError as exc:
                logger.debug("SENA fetch failed", url=url, error=str(exc)[:100])
                continue

        # Búsqueda directa en plataforma de SENA por palabras clave
        try:
            search_base = "https://www.sena.edu.co/es-co/aspirantes/buscar-programas"
            for term in search_terms:
                params = {"keyword": term}
                resp = await client.get(search_base, params=params, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    results = soup.select("a[href*='programa'], .result a, .search-result a")

                    for result in results[:10]:
                        href = result.get("href", "").strip()
                        title = result.get_text(strip=True)

                        if href and title and 10 <= len(title) <= 300:
                            if not href.startswith("http"):
                                href = "https://www.sena.edu.co" + href if href.startswith("/") else "https://www.sena.edu.co/" + href

                            items.append({
                                "title": title,
                                "url": href,
                                "source": "sena",
                                "funder": "SENA",
                                "search_term": term,
                            })

                    logger.debug("SENA search completed", term=term, results=len(results))
        except httpx.HTTPError as exc:
            logger.debug("SENA search failed", error=str(exc)[:100])

        if items:
            logger.info("SENA opportunities scraped", results=len(items))
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
                "paths": ["/servicios/educacion", "/programas/educacion", "/oportunidades", "/servicios", "/afiliadosycotizantes"],
                "keywords": ["educacion", "infantil", "jardin", "formacion", "becas"],
            },
            {
                "name": "Compensar",
                "url": "https://www.compensar.com.co",
                "paths": ["/servicios", "/programas", "/educacion", "/sobre-compensar/oportunidades"],
                "keywords": ["educacion", "infantil", "jardin", "formacion", "afiliados"],
            },
            {
                "name": "Protección",
                "url": "https://www.proteccion.com.co",
                "paths": ["/servicios", "/programas", "/educacion", "/bienestar"],
                "keywords": ["educacion", "infantil", "formacion", "beneficiarios"],
            },
            {
                "name": "Caja Nariño",
                "url": "https://www.cajanario.com.co",
                "paths": ["/servicios", "/programas", "/oportunidades", "/educacion"],
                "keywords": ["educacion", "infantil", "jardin", "formacion"],
            },
            {
                "name": "Caja Popular",
                "url": "https://www.cajapopular.com.co",
                "paths": ["/servicios", "/programas", "/educacion", "/bienestar"],
                "keywords": ["educacion", "infantil", "formacion"],
            },
            {
                "name": "COMFANDI",
                "url": "https://www.comfandi.com.co",
                "paths": ["/servicios", "/programas", "/educacion", "/bienestar-del-afiliado"],
                "keywords": ["educacion", "infantil", "formacion", "afiliados"],
            },
            {
                "name": "COMFAORIENTE",
                "url": "https://www.comfaoriente.com.co",
                "paths": ["/servicios", "/programas", "/bienestar", "/educacion"],
                "keywords": ["educacion", "infantil", "formacion"],
            },
            {
                "name": "Caja de Compensación Familiar Colombiana",
                "url": "https://www.cafacol.com.co",
                "paths": ["/servicios", "/programas", "/educacion"],
                "keywords": ["educacion", "infantil", "formacion"],
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
            "ludotecas primera infancia colombia",
            "retos innovación educación inicial colombia",
            "economía del cuidado primera infancia colombia",
            "EdTech primera infancia colombia",
            "salas lactancia empresas colombia",
            "sostenibilidad primera infancia colombia",
            "niños migrantes primera infancia colombia"
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

    async def _fetch_universities(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca oportunidades en universidades colombianas de educación inicial.

        Universidades con programas de educación inicial frecuentemente ofrecen
        becas, diplomados y programas de investigación.
        """
        items = []

        universities = [
            {
                "name": "Universidad de Antioquia",
                "url": "https://www.udea.edu.co",
                "keywords": ["educacion", "inicial", "infantil", "formacion"],
            },
            {
                "name": "Pontificia Universidad Javeriana",
                "url": "https://www.javeriana.edu.co",
                "keywords": ["educacion", "inicial", "infantil", "posgrado"],
            },
            {
                "name": "Universidad Nacional de Colombia",
                "url": "https://nacional.edu.co",
                "keywords": ["educacion", "inicial", "infantil", "investigacion"],
            },
            {
                "name": "Universidad del Valle",
                "url": "https://www.univalle.edu.co",
                "keywords": ["educacion", "infantil", "diplomado"],
            },
        ]

        for uni in universities:
            try:
                base_url = uni["url"].rstrip("/")
                # Intentar múltiples rutas comunes
                paths = [
                    "/oferta-academica",
                    "/programas",
                    "/convocatorias",
                    "/becas",
                    "/investigacion",
                    "/extension",
                ]

                for path in paths:
                    full_url = base_url + path

                    resp = await client.get(full_url, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Buscar enlaces de programas/oportunidades
                    links = soup.select(
                        "a[href*='programa'], a[href*='beca'], "
                        "a[href*='diplomado'], a[href*='maestria'], "
                        "a[href*='convocatoria'], a[href*='inscripcion'], "
                        ".programa a, .beca a, .oferta a"
                    )

                    for link in links[:10]:
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)

                        # Validar relevancia
                        title_lower = title.lower()
                        has_keyword = any(kw in title_lower for kw in uni["keywords"])

                        if href and title and 10 <= len(title) <= 300 and has_keyword:
                            if not href.startswith("http"):
                                href = base_url + href if href.startswith("/") else base_url + "/" + href

                            items.append({
                                "title": title,
                                "url": href,
                                "source": "universidad",
                                "funder": uni["name"],
                            })

                    if len(items) > 0:
                        break  # Si encontró en esta ruta, pasar a siguiente uni

            except httpx.HTTPError as exc:
                logger.debug("University fetch failed", uni=uni["name"], error=str(exc)[:100])
                continue

        if len(items) > 0:
            logger.info("Universities scraped", results=len(items))
        return items

    async def _fetch_foundations(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca oportunidades en fundaciones y organismos de cooperación.

        Fundaciones como Cargill, Hilton, GIZ, etc. frecuentemente publican
        convocatorias para educación inicial en Colombia.
        """
        items = []

        foundations = [
            {
                "name": "Fundación Cargill Colombia",
                "url": "https://www.cargill.com/page/colombia-home",
                "search_terms": ["educacion inicial", "formacion docente"],
            },
            {
                "name": "Fundación Hilton para Hoteles",
                "url": "https://www.hildonfoundation.org",
                "search_terms": ["educacion", "infancia"],
            },
            {
                "name": "GIZ Colombia",
                "url": "https://www.giz.de/en/worldwide/31415.html",
                "search_terms": ["educacion inicial", "primera infancia"],
            },
            {
                "name": "Fundación FES (Foro por la Educación)",
                "url": "https://www.fes.org.co",
                "search_terms": ["educacion", "politica publica"],
            },
        ]

        for foundation in foundations:
            try:
                base_url = foundation["url"].rstrip("/")
                paths = [
                    "/proyectos",
                    "/programas",
                    "/convocatorias",
                    "/oportunidades",
                    "/noticias",
                ]

                for path in paths:
                    full_url = base_url + path

                    resp = await client.get(full_url, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    links = soup.select(
                        "a[href*='proyecto'], a[href*='programa'], "
                        "a[href*='convocatoria'], a[href*='oportunidad'], "
                        ".proyecto a, .programa a, .news a, article a"
                    )

                    for link in links[:8]:
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)

                        if href and title and 10 <= len(title) <= 300:
                            if not href.startswith("http"):
                                href = base_url + href if href.startswith("/") else base_url + "/" + href

                            items.append({
                                "title": title,
                                "url": href,
                                "source": "fundacion",
                                "funder": foundation["name"],
                            })

                    if len(items) > 0:
                        break

            except httpx.HTTPError as exc:
                logger.debug("Foundation fetch failed", foundation=foundation["name"], error=str(exc)[:100])
                continue

        if len(items) > 0:
            logger.info("Foundations scraped", results=len(items))
        return items

    async def _fetch_google_news_alerts(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca alertas públicas de Google News sobre oportunidades en educación inicial.

        Google News es una fuente valiosa para anuncios de convocatorias, cambios en política
        pública y nuevos programas de educación inicial en Colombia.
        """
        items = []

        search_queries = [
            "educación inicial colombia convocatoria",
            "primera infancia colombia oportunidades",
            "cdis colombia financiamiento",
            "formación docentes colombia",
            "jardines infantiles convocatoria",
            "cero a siempre colombia",
            "icbf convocatorias colombia",
            "mineducación educación inicial",
            "ludotecas convocatoria",
            "salas de lactancia licitacion",
            "inclusión social infantil convocatoria",
            "retos de innovación educativa"
        ]

        for query in search_queries:
            try:
                # Google News RSS feed
                rss_url = f"https://news.google.com/rss/search?q={query}+colombia&ceid=CO:es&hl=es"

                resp = await client.get(rss_url, timeout=15)
                resp.raise_for_status()

                try:
                    root = ET.fromstring(resp.content)
                    items_in_feed = root.findall(".//item")

                    for item_elem in items_in_feed[:5]:
                        title_elem = item_elem.find("title")
                        link_elem = item_elem.find("link")
                        desc_elem = item_elem.find("description")

                        if title_elem is None or link_elem is None:
                            continue

                        title = title_elem.text or ""
                        link = link_elem.text or ""
                        desc = desc_elem.text or "" if desc_elem is not None else ""

                        if not title or not link or len(title) < 15:
                            continue

                        items.append({
                            "title": title[:200],
                            "url": link,
                            "source": "google_news",
                            "funder": "Fuente pública Colombia (Google News)",
                            "description": desc[:500],
                            "search_query": query,
                        })

                except ET.ParseError:
                    logger.debug("Google News RSS parse error", query=query)
                    continue

            except httpx.HTTPError as exc:
                logger.debug("Google News fetch failed", query=query, error=str(exc)[:100])
                continue

        if items:
            logger.info("Google News alerts scraped", results=len(items))
        return items

    async def _fetch_linkedin_opportunities(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca oportunidades en LinkedIn relacionadas con educación inicial.

        LinkedIn a menudo publica ofertas de trabajo y oportunidades de consultoría
        relacionadas con educación inicial y primera infancia.
        """
        items = []

        # LinkedIn no permite scraping directo, pero las búsquedas públicas de Google
        # indexan perfiles y publicaciones de LinkedIn
        linkedin_queries = [
            "site:linkedin.com educación inicial colombia",
            "site:linkedin.com first childhood development colombia",
            "site:linkedin.com ECDinnovation colombia",
            "site:linkedin.com jardinería colombia convocatoria",
            "site:linkedin.com economía del cuidado colombia",
            "site:linkedin.com EdTech educación inicial colombia",
            "site:linkedin.com ludotecas convocatoria colombia"
        ]

        for query in linkedin_queries:
            try:
                # Usar búsqueda pública de Google para LinkedIn
                search_url = "https://www.google.com/search"
                params = {
                    "q": query,
                    "tbm": "nws",  # News tab para resultados recientes
                }

                resp = await client.get(search_url, params=params, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Buscar links en resultados de búsqueda
                links = soup.select("a[href*='linkedin.com'], a[href*='jobs']")

                for link in links[:5]:
                    href = link.get("href", "").strip()
                    title = link.get_text(strip=True)

                    if not href or not title or len(title) < 10:
                        continue

                    # Limpiar URLs de búsqueda
                    if "url=" in href:
                        href = href.split("url=")[1].split("&")[0]
                    if not href.startswith("http"):
                        continue

                    items.append({
                        "title": title[:200],
                        "url": href,
                        "source": "linkedin",
                        "funder": "LinkedIn / Profesionales",
                        "search_query": query,
                    })

            except httpx.HTTPError as exc:
                logger.debug("LinkedIn opportunity search failed", query=query, error=str(exc)[:100])
                continue

        if items:
            logger.info("LinkedIn opportunities found", results=len(items))
        return items

    async def _fetch_twitter_opportunities(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Busca oportunidades anunciadas en Twitter/X.

        Organizaciones, gobiernos y fundaciones frecuentemente anuncian
        convocatorias y oportunidades en Twitter.
        """
        items = []

        # Twitter/X también es accesible vía búsqueda pública de Google
        twitter_queries = [
            'site:twitter.com OR site:x.com "educación inicial" colombia convocatoria',
            'site:twitter.com OR site:x.com "primera infancia" colombia oportunidad',
            'site:twitter.com OR site:x.com icbf convocatoria',
            'site:twitter.com OR site:x.com "cero a siempre" convocatoria',
            'site:twitter.com OR site:x.com "ludotecas" convocatoria',
            'site:twitter.com OR site:x.com "economía del cuidado" colombia'
        ]

        for query in twitter_queries:
            try:
                search_url = "https://www.google.com/search"
                params = {
                    "q": query,
                    "tbm": "nws",  # News tab para tweets recientes
                }

                resp = await client.get(search_url, params=params, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                links = soup.select("a[href*='twitter.com'], a[href*='x.com']")

                for link in links[:5]:
                    href = link.get("href", "").strip()
                    title = link.get_text(strip=True)

                    if not href or not title or len(title) < 15:
                        continue

                    # Limpiar URLs de búsqueda
                    if "url=" in href:
                        href = href.split("url=")[1].split("&")[0]
                    if not href.startswith("http"):
                        continue

                    items.append({
                        "title": title[:200],
                        "url": href,
                        "source": "twitter",
                        "funder": "Anuncio público (Twitter/X)",
                        "search_query": query,
                    })

            except httpx.HTTPError as exc:
                logger.debug("Twitter opportunity search failed", query=query, error=str(exc)[:100])
                continue

        if items:
            logger.info("Twitter/X opportunities found", results=len(items))
        return items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convierte registro crudo a OpportunityCreate.

        Filtra por relevancia a primera infancia/educación inicial.
        Lógica simplificada para máxima cobertura sin sacrificar calidad.
        """
        title = raw.get("title", "").strip()
        if not title or len(title) < 10:
            return None

        url = raw.get("url", "").strip()
        if not url or not url.startswith("http"):
            return None

        description = raw.get("description", "")
        source = raw.get("source", "unknown")

        # Texto para análisis
        haystack = (title + " " + url + " " + description).lower()

        # BLOQUEAR: palabras clave explícitamente NO relevantes
        reject_keywords = (
            "seleccion", "convocatoria puesto", "rrhh",
            "empleo", "vacante", "carrera", "candidato",
            "error", "404", "no encontrado", "página no disponible"
        )
        if any(kw in haystack for kw in reject_keywords):
            logger.debug("Nacional opp rejected", title=title[:60], reason="reject_keyword")
            return None

        # LÓGICA DE ACEPTACIÓN (mejorada y menos restrictiva):
        # 1. Si viene de fuente oficial (ICBF, MinEducación, SECOP), ACEPTAR sin más filtros
        official_sources = ("icbf", "mineducacion", "secop", "gobierno")
        if source in official_sources or any(src in haystack for src in official_sources):
            logger.debug("Nacional opp accepted", title=title[:60], reason="official_source")
            # Ir directamente a crear oportunidad
        else:
            # 2. Si NO es fuente oficial, aplicar filtro de keywords más flexible:
            #    - Aceptar si contiene 1+ palabra clave CORE (muy específica)
            #    - O aceptar si contiene 2+ palabras clave SECONDARY (general)
            core_matches = sum(1 for kw in NACIONAL_KEYWORDS_CORE if kw in haystack)
            secondary_matches = sum(1 for kw in NACIONAL_KEYWORDS_SECONDARY if kw in haystack)

            if core_matches >= 1:
                logger.debug("Nacional opp accepted", title=title[:60], reason=f"core_keyword({core_matches})")
            elif secondary_matches >= 2:
                logger.debug("Nacional opp accepted", title=title[:60], reason=f"secondary_keywords({secondary_matches})")
            else:
                logger.debug(
                    "Nacional opp rejected",
                    title=title[:60],
                    reason=f"insufficient_keywords(core={core_matches}, secondary={secondary_matches})"
                )
                return None

        # Parse deadline si existe
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
            market_window="funding_colombia",
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

    async def _alert_google_block(self, status_code: int) -> None:
        """Alerta a Slack cuando Google bloquea por rate limit o acceso."""
        alert_service = AlertService()
        message = (
            f"🚨 *Google Search IP Block Detected* — Status {status_code}\n"
            f"Scraper `nacional_colombia` hit rate limit while searching for opportunities.\n"
            f"Automatic retry in next scheduled run. Check VPS IP blocklist if persistent."
        )
        await alert_service.send_slack(message, channel="#dev-alerts")
        logger.warning("Google block alert sent to Slack", status_code=status_code)

    async def _fetch_general_web_search(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Realiza una búsqueda general en la web para detectar convocatorias en todo el internet."""
        import random
        items = []
        queries = [
            'convocatoria "educación inicial" colombia 2026',
            'licitacion "primera infancia" colombia',
            'grant OR "fondos filantrópicos" "primera infancia" colombia',
            'retos de innovación "educación inicial" OR "primera infancia" colombia',
            'convocatoria "ludotecas" OR "salas de lactancia" colombia',
            'concurso OR premio "primera infancia" colombia',
            '"economía del cuidado" convocatoria colombia',
            'EdTech "educación inicial" convocatoria colombia',
            'sostenibilidad "primera infancia" convocatoria colombia'
        ]

        # Seleccionar 3 consultas al azar para evitar rate limit de Google
        selected_queries = random.sample(queries, min(len(queries), 3))

        for idx, query in enumerate(selected_queries):
            # Agregar delay entre queries para evitar bloqueo IP
            if idx > 0:
                await asyncio.sleep(random.uniform(3, 5))

            try:
                search_url = "https://www.google.com/search"
                params = {"q": query}
                resp = await client.get(search_url, params=params, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                search_results = _extract_google_search_links(soup)

                # Limitar a 5 resultados por query (antes era 10)
                for title, href in search_results[:5]:
                    items.append({
                        "title": title[:200],
                        "url": href,
                        "source": "general_web",
                        "funder": "Búsqueda Web General",
                        "search_query": query
                    })

            except httpx.HTTPStatusError as exc:
                # Detectar bloqueos de Google (403, 429)
                if exc.response.status_code in (403, 429):
                    logger.warning(
                        "Google blocking detected",
                        status_code=exc.response.status_code,
                        query=query,
                    )
                    # Enviar alerta a Slack
                    await self._alert_google_block(exc.response.status_code)
                    break  # No continuar si está bloqueado
                logger.debug("General web search query failed", query=query, error=str(exc)[:100])
                continue
            except httpx.HTTPError as exc:
                logger.debug("General web search query failed", query=query, error=str(exc)[:100])
                continue
                
        if items:
            logger.info("General web opportunities scraped", results=len(items))
        return items


def _extract_google_search_links(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Extrae enlaces y títulos de una página de resultados de Google Search."""
    import urllib.parse
    results = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        
        if any(x in href for x in ["google.com", "webcache.googleusercontent.com", "search?", "/settings/"]):
            continue
            
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]
            href = urllib.parse.unquote(href)
            
        if href.startswith("http") and title and len(title) > 10:
            results.append((title, href))
            
    return results
