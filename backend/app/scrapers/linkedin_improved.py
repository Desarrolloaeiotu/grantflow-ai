"""Scraper mejorado para LinkedIn - Oportunidades de educación inicial.

Estrategias:
1. LinkedIn Jobs API pública (via search.linkedin.com)
2. Scraping robusto con User-Agent rotación y retry logic
3. Fallback a APIs públicas (RapidAPI, ScraperAPI)
4. Caché local para evitar requests duplicados
5. Filtrado inteligente por keywords

Schedule: Diario 8:30am (después de otras fuentes)
Prioridad: MEDIA (complementaria, no crítica)
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog
from bs4 import BeautifulSoup

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()

# ═══════════════════════════════════════════════════════════════════════════════
# USER AGENT ROTATION — Evita bloqueos por scraping
# ═══════════════════════════════════════════════════════════════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

LINKEDIN_KEYWORDS_CORE = (
    # Primera infancia
    "early childhood", "educación inicial", "primera infancia", "ecd",
    "early childhood development", "development infantil temprano",

    # Oportunidades específicas
    "convocatoria", "opportunity", "hiring", "vacante", "job",
    "consultoría", "consulting", "grant", "fellowship",

    # Formación y liderazgo
    "formación docente", "teacher training", "capacitación",
    "liderazgo educativo", "educational leadership",

    # Economía del cuidado
    "economía del cuidado", "care economy", "trabajo de cuidado",

    # Contexto geográfico
    "colombia", "latino", "latam", "américa latina",
)

LINKEDIN_KEYWORDS_SECONDARY = (
    "educación", "infancia", "niños", "desarrollo infantil",
    "programa", "proyecto", "iniciativa",
)

# ═══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 1: LinkedIn Jobs Search API (público)
# ═══════════════════════════════════════════════════════════════════════════════

LINKEDIN_JOBS_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/searchWithCurrentFilters"

LINKEDIN_JOB_SEARCHES = [
    {
        "keywords": "early childhood development",
        "location": "Colombia",
        "remote": "remote",
    },
    {
        "keywords": "educación inicial",
        "location": "Colombia",
        "remote": "remote",
    },
    {
        "keywords": "teacher training first years",
        "location": "Latin America",
        "remote": "remote",
    },
    {
        "keywords": "education consultant colombia",
        "location": "Colombia",
    },
    {
        "keywords": "grant program education",
        "location": "Latin America",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 2: LinkedIn Company Pages (ICBF, MinEducación, etc)
# ═══════════════════════════════════════════════════════════════════════════════

LINKEDIN_COMPANY_PAGES = [
    "https://www.linkedin.com/company/icbf-colombia/",  # ICBF
    "https://www.linkedin.com/company/ministerio-de-educaci%C3%B3n-nacional-mineduaci%C3%B3n/",  # MinEducación
    "https://www.linkedin.com/company/cafam/",  # CAFAM
    "https://www.linkedin.com/company/fundaci%C3%B3n-cargill/",  # Fundación Cargill
    "https://www.linkedin.com/company/giz-deutsche-gesellschaft-f%C3%BCr-internationale-zusammenarbeit/",  # GIZ
    "https://www.linkedin.com/company/unicef/",  # UNICEF
]

# ═══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 3: Búsqueda pública via Google con LinkedIn
# ═══════════════════════════════════════════════════════════════════════════════

LINKEDIN_GOOGLE_QUERIES_NACIONAL = [
    # Búsquedas NACIONALES (Colombia específicamente)
    "site:linkedin.com educación inicial colombia oportunidad",
    "site:linkedin.com first childhood development colombia grant",
    "site:linkedin.com formación docente colombia convocatoria",
    "site:linkedin.com early childhood colombia consulting",
    "site:linkedin.com economía del cuidado colombia",

    # Búsquedas en WEB nacional
    "educación inicial colombia convocatoria 2026",
    "primera infancia colombia oportunidad",
    "formación docente colombia vacante",
    "cdi colombia contratación",
    "jardinería colombia empleo",
]

LINKEDIN_GOOGLE_QUERIES_GLOBAL = [
    # Búsquedas GLOBALES (internacional)
    "site:linkedin.com early childhood development opportunity grant",
    "site:linkedin.com first childhood education fellowship",
    "site:linkedin.com teacher training education consulting",
    "site:linkedin.com care economy opportunity",

    # Búsquedas en WEB global
    "early childhood development grant opportunity 2026",
    "education consulting first childhood international",
    "teacher training fellowship latin america",
    "child development grant opportunity",
]

# ═══════════════════════════════════════════════════════════════════════════════
# IMPLEMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════════


class LinkedInScraperImproved(BaseScraper):
    source_name = "linkedin_improved"
    base_url = "https://www.linkedin.com"
    schedule = "0 8 * * *"  # 8am diario

    def __init__(self):
        super().__init__()
        self.user_agent_idx = 0

    def _get_user_agent(self) -> str:
        """Rotar User-Agent para evitar bloqueos."""
        ua = USER_AGENTS[self.user_agent_idx % len(USER_AGENTS)]
        self.user_agent_idx += 1
        return ua

    def _get_proxy_config(self) -> dict[str, str | None]:
        """Obtener configuración de proxy desde variables de entorno.

        Retorna: {"proxies": "http://user:pass@proxy:port" | None}
        Si PROXY_URL no está configurado, devuelve None (sin proxy).
        """
        proxy_url = os.getenv("PROXY_URL")
        if proxy_url:
            logger.info("Using proxy for LinkedIn scraping", proxy=proxy_url[:20] + "...")
            return {"proxies": proxy_url}
        logger.warning("PROXY_URL not configured - LinkedIn scraping without proxy may be blocked")
        return {}

    async def fetch_raw(self) -> list[dict[str, Any]]:
        """Fetch usando 3 estrategias en paralelo con fallback y soporte de proxy."""
        all_items: list[dict[str, Any]] = []

        # Obtener configuración de proxy
        proxy_config = self._get_proxy_config()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            **proxy_config  # Pasar proxies si está disponible
        ) as client:
            # Ejecutar 3 estrategias en paralelo
            results = await asyncio.gather(
                self._fetch_jobs_api(client),
                self._fetch_company_pages(client),
                self._fetch_google_search(client),
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, Exception):
                    logger.warning("LinkedIn fetch strategy failed", error=str(result)[:100])
                    continue
                if result:
                    all_items.extend(result)

        logger.info("LinkedIn fetch complete", total_items=len(all_items))
        return all_items

    async def _fetch_jobs_api(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """ESTRATEGIA 1: LinkedIn Jobs Search API (público, no requiere autenticación)."""
        items = []

        for search in LINKEDIN_JOB_SEARCHES:
            try:
                # Delay aleatorio 2-5 segundos entre requests
                await asyncio.sleep(random.uniform(2, 5))

                # Parámetros para LinkedIn Jobs API
                params = {
                    "keywords": search["keywords"],
                    "locationId": "Colombia" if "Colombia" in search.get("location", "") else "",
                    "start": 0,
                    "count": 25,
                }

                headers = {
                    "User-Agent": self._get_user_agent(),
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                # Construir URL
                url = f"{LINKEDIN_JOBS_SEARCH_URL}?{urlencode(params)}"

                resp = await client.get(url, headers=headers)

                if resp.status_code != 200:
                    logger.debug(
                        "LinkedIn Jobs API non-200",
                        status=resp.status_code,
                        keywords=search["keywords"],
                    )
                    continue

                # Parse JSON response (si es disponible)
                try:
                    data = resp.json()
                    jobs = data.get("elements", [])

                    for job in jobs:
                        items.append({
                            "title": job.get("title", ""),
                            "company": job.get("companyName", ""),
                            "description": job.get("description", ""),
                            "url": job.get("applyUrl", ""),
                            "posted_date": job.get("listedAt"),
                            "location": job.get("location", ""),
                            "source": "linkedin_jobs_api",
                            "type": "job_posting",
                        })
                except json.JSONDecodeError:
                    # Fallback a scraping HTML si JSON falla
                    logger.debug("LinkedIn Jobs API returned non-JSON")
                    items.extend(await self._scrape_jobs_html(resp.text))

            except asyncio.TimeoutError:
                logger.debug("LinkedIn Jobs API timeout", keywords=search["keywords"])
                continue
            except Exception as e:
                logger.debug("LinkedIn Jobs API error", error=str(e)[:100])
                continue

        return items

    async def _scrape_jobs_html(self, html: str) -> list[dict[str, Any]]:
        """Fallback: scraping HTML si API JSON falla."""
        items = []
        try:
            soup = BeautifulSoup(html, "lxml")

            # Buscar base de jobs (estructura varía, intentar múltiples selectores)
            job_cards = soup.select(
                ".job-card-container, [data-job-id], .base-card--link, "
                "article[data-job-id]"
            )

            for card in job_cards[:10]:  # Limitar para no abusar
                title_el = card.select_one(
                    ".base-search-card__title, .job-card-title, h3"
                )
                company_el = card.select_one(
                    ".base-search-card__subtitle, .job-card-subtitle, .company-name"
                )
                link_el = card.select_one("a[href*='linkedin.com/jobs']")

                if not (title_el and company_el and link_el):
                    continue

                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True)
                url = link_el.get("href", "")

                if title and len(title) > 10:
                    items.append({
                        "title": title,
                        "company": company,
                        "url": url,
                        "source": "linkedin_jobs_html",
                        "type": "job_posting",
                    })
        except Exception as e:
            logger.debug("LinkedIn HTML scraping failed", error=str(e)[:100])

        return items

    async def _fetch_company_pages(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """ESTRATEGIA 2: Monitorear páginas de empresas (ICBF, MinEducación, etc)."""
        items = []

        for company_url in LINKEDIN_COMPANY_PAGES:
            try:
                # Delay aleatorio 2-5 segundos entre requests
                await asyncio.sleep(random.uniform(2, 5))

                # Obtener página de empresa
                headers = {"User-Agent": self._get_user_agent()}
                resp = await client.get(company_url, headers=headers)

                if resp.status_code != 200:
                    logger.debug("Company page fetch failed", url=company_url)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Buscar posts recientes / anuncios
                posts = soup.select(
                    ".update-components-text, .feed-shared-update-v2, "
                    ".posts, article"
                )

                for post in posts[:5]:  # Últimos 5 posts
                    text = post.get_text(strip=True)
                    link = post.select_one("a[href]")

                    # Filtrar por keywords
                    if self._has_keywords(text):
                        items.append({
                            "title": text[:100],
                            "description": text[:500],
                            "url": link.get("href") if link else company_url,
                            "source": "linkedin_company_page",
                            "type": "company_announcement",
                        })

            except Exception as e:
                logger.debug("Company page scraping failed", url=company_url, error=str(e)[:100])
                continue

        return items

    async def _fetch_google_search(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """ESTRATEGIA 3: Búsqueda pública via Google (fallback si APIs fallan).

        Ejecuta AMBAS búsquedas: nacional (Colombia) + global (internacional).
        """
        items = []

        # Ejecutar búsquedas nacionales Y globales
        search_batches = [
            (LINKEDIN_GOOGLE_QUERIES_NACIONAL, "funding_colombia"),
            (LINKEDIN_GOOGLE_QUERIES_GLOBAL, "funding_global"),
        ]

        for queries, market_window in search_batches:
            for query in queries:
                try:
                    # Delay aleatorio 2-5 segundos entre requests
                    await asyncio.sleep(random.uniform(2, 5))

                    headers = {
                        "User-Agent": self._get_user_agent(),
                        "Accept-Language": "es-ES,es;q=0.9",
                    }

                    # Usar búsqueda de Google
                    params = {"q": query, "tbm": "nws"}
                    resp = await client.get(
                        "https://www.google.com/search",
                        params=params,
                        headers=headers,
                        timeout=10,
                    )

                    soup = BeautifulSoup(resp.text, "lxml")

                    # Extraer todos los enlaces (no solo LinkedIn)
                    links = soup.select("a[href]")

                    for link in links[:5]:  # Top 5 resultados
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)

                        # Limpiar URL de búsqueda de Google
                        if "url=" in href:
                            href = href.split("url=")[1].split("&")[0]

                        if href.startswith("http") and len(title) > 10:
                            items.append({
                                "title": title,
                                "url": href,
                                "source": "linkedin_google_search",
                                "type": "public_search",
                                "market_window": market_window,  # Nacional o Global
                            })

                except Exception as e:
                    logger.debug(
                        "Google search failed",
                        query=query[:50],
                        market_window=market_window,
                        error=str(e)[:100],
                    )
                    continue

        return items

    def _has_keywords(self, text: str) -> bool:
        """Filtro: al menos 1 CORE_KEYWORD presente."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in LINKEDIN_KEYWORDS_CORE)

    async def extract_key_contacts(self, profile_data: dict) -> list[dict]:
        """Extract organization + key contacts from LinkedIn search results.

        Busca roles estratégicos (partnerships, grants, cooperación, etc) dentro
        de organizaciones encontradas en búsquedas de LinkedIn.

        Returns:
            [{
                "organization": {"name": str, "website": str, "source": "linkedin"},
                "contacts": [
                    {
                        "full_name": str,
                        "title": str,
                        "email": str | None,
                        "linkedin_url": str,
                        "priority_score": int,  # 2-5
                        "department": str
                    }
                ]
            }]
        """
        RELEVANT_ROLES = {
            "partnerships", "strategic partnerships", "alliances",
            "global partnerships", "institutional relations", "external relations",
            "business development", "program manager", "program director",
            "grants manager", "philanthropy", "development officer",
            "impact investing", "cooperation", "international cooperation",
            "innovation", "ecosystem lead", "network lead"
        }

        contacts = []
        org_name = profile_data.get("organization", "")
        org_url = profile_data.get("organization_url", "")

        for person in profile_data.get("employees", []):
            title = (person.get("title") or "").lower()
            if any(kw in title for kw in RELEVANT_ROLES):
                contacts.append({
                    "full_name": person.get("name", ""),
                    "title": person.get("title", ""),
                    "email": person.get("email"),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "priority_score": self._calculate_role_priority(title),
                    "department": self._categorize_role(title),
                })

        if contacts:
            return [{
                "organization": {
                    "name": org_name,
                    "website": org_url,
                    "source": "linkedin",
                },
                "contacts": contacts,
            }]
        return []

    def _calculate_role_priority(self, title: str) -> int:
        """Calcular prioridad del contacto basado en su rol.

        5 = Partnerships/Grants (máxima prioridad)
        4 = Business Development / Innovation
        3 = Director / Manager
        2 = Otros roles relacionados
        """
        title_lower = title.lower()
        if "partnership" in title_lower or "grant" in title_lower:
            return 5
        elif "business development" in title_lower or "innovation" in title_lower:
            return 4
        elif "director" in title_lower or "manager" in title_lower:
            return 3
        else:
            return 2

    def _categorize_role(self, title: str) -> str:
        """Categorizar el rol del contacto para búsquedas futuras."""
        title_lower = title.lower()
        if "partnership" in title_lower:
            return "partnerships"
        elif "grant" in title_lower:
            return "grants"
        elif "cooperat" in title_lower:
            return "cooperation"
        elif "innovat" in title_lower:
            return "innovation"
        else:
            return "development"

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convertir raw LinkedIn item → OpportunityCreate."""
        title = raw.get("title", "").strip()

        if not title or len(title) < 10:
            return None

        # Validar keywords
        text = (title + " " + raw.get("description", "")).lower()
        if not self._has_keywords(text):
            logger.debug("LinkedIn item discarded: no keywords", title=title[:50])
            return None

        # Parsear URL
        url = raw.get("url", "")
        if not url or not url.startswith("http"):
            return None

        # Descripción
        description = raw.get("description", "") or raw.get("company", "")

        # Funder
        funder_name = (
            raw.get("company") or
            "LinkedIn / Profesionales" if raw.get("type") == "job_posting"
            else "LinkedIn"
        )

        # Crear schema
        # Si viene market_window del raw (de búsqueda Google), usarlo; si no, inferir
        market_window = raw.get("market_window")
        if not market_window:
            # Inferir basado en keywords en título/descripción
            text_lower = (title + " " + description).lower()
            if "colombia" in text_lower:
                market_window = "funding_colombia"
            else:
                market_window = "funding_global"

        return OpportunityCreate(
            title=title[:200],
            description=description[:5000],
            funder_name=funder_name,
            deadline=None,  # LinkedIn típicamente no tiene deadlines
            url_rfp=url,
            url_source=url,
            source_name=self.source_name,
            org_website="https://www.linkedin.com",
            eligible_countries=["Colombia", "Latin America"],
            sectors=["education", "first_childhood"],
            capital_type="opportunity",  # Job postings, consulting gigs, etc
            market_window=market_window,  # Nacional o Global según búsqueda
            raw_content=json.dumps(raw, default=str),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK: ScraperAPI (opcional, costo $29-99/mes)
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_with_scraperapi(
    url: str,
    api_key: str | None = None,
) -> str:
    """Fallback premium: usar ScraperAPI para eludir bloqueos de LinkedIn.

    Requiere variable de entorno SCRAPERAPI_KEY (no incluido por defecto).
    Costo: $29/mes para 50K requests / mes.

    Uso:
        if linkedin_direct_failed:
            html = await fetch_with_scraperapi(url, api_key=settings.SCRAPERAPI_KEY)
    """
    if not api_key:
        raise ValueError("ScraperAPI key not configured")

    params = {
        "url": url,
        "api_key": api_key,
        "render": "false",  # Cambiar a "true" si se requiere JavaScript
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://api.scraperapi.com",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.text
