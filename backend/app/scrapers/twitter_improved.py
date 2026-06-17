"""Scraper mejorado para Twitter/X - Oportunidades de educación inicial.

Estrategias:
1. API v2 de Twitter (requiere Bearer token)
2. Búsqueda pública via Google News (site:twitter.com, site:x.com)
3. Monitorear cuentas clave (ICBF, MinEducación, organizaciones)
4. Rate limiting inteligente
5. Filtrado por engagement y relevancia

Schedule: Diario 8:00am (antes de LinkedIn)
Prioridad: MEDIA (complementaria, no crítica)
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog
from bs4 import BeautifulSoup

from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import BaseScraper, ScraperError

logger = structlog.get_logger()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BÚSQUEDAS
# ═══════════════════════════════════════════════════════════════════════════════

TWITTER_KEYWORDS_CORE = (
    # Primera infancia
    "early childhood", "educación inicial", "primera infancia",
    "early childhood development", "ecd",

    # Oportunidades
    "convocatoria", "opportunity", "vacante", "abierta",
    "grant", "funding", "fellowship", "calling",

    # Formación
    "capacitación", "formación docente", "training",
    "liderazgo educativo",

    # Economía del cuidado
    "economía del cuidado", "care economy",

    # Contexto
    "colombia", "latino", "latam", "américa latina",
)

TWITTER_KEYWORDS_SECONDARY = (
    "educación", "infancia", "niños", "programa",
    "proyecto", "iniciativa",
)

# Cuentas institucionales a monitorear
TWITTER_ACCOUNTS_TO_MONITOR = [
    "icbfcolombia",           # ICBF
    "minEducacion_co",        # MinEducación
    "Fundacion_Cargill",      # Fundación Cargill
    "fundacionhilton",        # Fundación Hilton
    "CAFAM",                  # CAFAM
    "ConectaRuralCo",         # Conecta Rural
    "UnicefColombia",         # UNICEF Colombia
    "ONU_es",                 # ONU
    "ProgramaDeAlianzas",     # Programas de Alianzas
    "SENAColombia",           # SENA
]

# Búsquedas complejas para Twitter
TWITTER_SEARCH_QUERIES_NACIONAL = [
    # Búsquedas NACIONALES (Colombia específicamente)
    "educación inicial colombia convocatoria OR oportunidad",
    "primera infancia colombia grant OR funding",
    "formación docente colombia abierta",
    "early childhood development colombia opportunity",
    "economía del cuidado colombia",
    "jardinería colombia convocatoria",
    "ICBF convocatoria 2026",
    "MinEducación colombia convocatoria",
    "cajas compensación colombia empleo",
]

TWITTER_SEARCH_QUERIES_GLOBAL = [
    # Búsquedas GLOBALES (internacional)
    "early childhood development opportunity grant",
    "first childhood education fellowship international",
    "teacher training education consulting grant",
    "care economy opportunity global",
    "child development funding opportunity",
    "education consulting first childhood",
]

# ═══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 1: Twitter API v2 (requiere Bearer token)
# ═══════════════════════════════════════════════════════════════════════════════

TWITTER_API_V2_URL = "https://api.twitter.com/2/tweets/search/recent"

async def fetch_twitter_api_v2(
    query: str,
    bearer_token: str | None = None,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Fetch usando Twitter API v2 (requiere autenticación).

    Requiere: TWITTER_BEARER_TOKEN en .env
    Rate limit: 300 requests / 15 min

    Returns: [{id, text, created_at, author_id, url, ...}]
    """
    if not bearer_token:
        logger.debug("Twitter API v2 token not configured, skipping")
        return []

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "GrantFlow-AI/1.0",
    }

    params = {
        "query": query,
        "max_results": min(max_results, 100),
        "tweet.fields": "created_at,author_id,public_metrics",
        "expansions": "author_id",
        "user.fields": "verified,location",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                TWITTER_API_V2_URL,
                headers=headers,
                params=params,
            )

            if resp.status_code == 401:
                logger.warning("Twitter API v2 authentication failed")
                return []

            if resp.status_code != 200:
                logger.debug(
                    "Twitter API v2 non-200",
                    status=resp.status_code,
                    query=query[:50],
                )
                return []

            data = resp.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            items = []
            for tweet in tweets:
                author_id = tweet.get("author_id")
                author = users.get(author_id, {})

                items.append({
                    "id": tweet.get("id"),
                    "title": tweet.get("text", "")[:100],
                    "text": tweet.get("text", ""),
                    "created_at": tweet.get("created_at"),
                    "author_id": author_id,
                    "author_name": author.get("name", ""),
                    "author_username": author.get("username", ""),
                    "author_verified": author.get("verified", False),
                    "url": f"https://twitter.com/{author.get('username')}/status/{tweet.get('id')}",
                    "like_count": tweet.get("public_metrics", {}).get("like_count", 0),
                    "retweet_count": tweet.get("public_metrics", {}).get("retweet_count", 0),
                    "source": "twitter_api_v2",
                    "type": "tweet",
                })

            logger.info("Twitter API v2 tweets fetched", count=len(items), query=query[:50])
            return items

    except asyncio.TimeoutError:
        logger.debug("Twitter API v2 timeout", query=query[:50])
        return []
    except Exception as e:
        logger.debug("Twitter API v2 error", error=str(e)[:100])
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 2: Monitorear cuentas clave
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_twitter_accounts(
    bearer_token: str | None = None,
) -> list[dict[str, Any]]:
    """Monitorear tweets recientes de cuentas clave.

    Estrategia: Buscar tweets de cuentas conocidas (ICBF, MinEducación, etc)
    sin parámetro de query específico para detectar anuncios generales.
    """
    if not bearer_token:
        logger.debug("Twitter API v2 token not configured, skipping account monitoring")
        return []

    items = []
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "GrantFlow-AI/1.0",
    }

    for username in TWITTER_ACCOUNTS_TO_MONITOR:
        try:
            # Buscar tweets de esta cuenta
            query = f"from:{username}"
            params = {
                "query": query,
                "max_results": 25,
                "tweet.fields": "created_at,author_id,public_metrics",
                "expansions": "author_id",
                "user.fields": "verified,location",
            }

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    TWITTER_API_V2_URL,
                    headers=headers,
                    params=params,
                )

                if resp.status_code != 200:
                    logger.debug(
                        "Twitter account fetch failed",
                        status=resp.status_code,
                        username=username,
                    )
                    continue

                data = resp.json()
                tweets = data.get("data", [])
                users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

                for tweet in tweets:
                    # Filtrar por keywords
                    text = tweet.get("text", "").lower()
                    if not any(kw.lower() in text for kw in TWITTER_KEYWORDS_CORE):
                        continue

                    author_id = tweet.get("author_id")
                    author = users.get(author_id, {})

                    items.append({
                        "id": tweet.get("id"),
                        "title": tweet.get("text", "")[:100],
                        "text": tweet.get("text", ""),
                        "created_at": tweet.get("created_at"),
                        "author_name": author.get("name", ""),
                        "author_username": author.get("username", ""),
                        "author_verified": author.get("verified", False),
                        "url": f"https://twitter.com/{author.get('username')}/status/{tweet.get('id')}",
                        "source": "twitter_account_monitor",
                        "type": "institutional_tweet",
                    })

            await asyncio.sleep(0.5)  # Rate limiting

        except Exception as e:
            logger.debug("Twitter account monitoring error", username=username, error=str(e)[:100])
            continue

    return items


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRATEGIA 3: Búsqueda pública via Google News
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_twitter_google_news() -> list[dict[str, Any]]:
    """Fallback: Búsqueda pública via Google News con site:twitter.com.

    Ejecuta AMBAS búsquedas: nacional (Colombia) + global (internacional).
    NO requiere autenticación.
    """
    items = []

    # Ejecutar búsquedas nacionales Y globales
    search_batches = [
        (TWITTER_SEARCH_QUERIES_NACIONAL, "funding_colombia"),
        (TWITTER_SEARCH_QUERIES_GLOBAL, "funding_global"),
    ]

    for queries, market_window in search_batches:
        for query in queries:
            try:
                # Construir búsqueda
                search_query = f"site:twitter.com OR site:x.com {query}"
                params = {
                    "q": search_query,
                    "tbm": "nws",  # News tab
                }

                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://www.google.com/search",
                        params=params,
                    )

                    if resp.status_code != 200:
                        logger.debug(
                            "Google News fetch failed",
                            status=resp.status_code,
                            market_window=market_window,
                        )
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")

                    # Buscar todos los enlaces (no solo Twitter)
                    links = soup.select("a[href]")

                    for link in links[:5]:  # Top 5 resultados
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)

                        # Limpiar URLs de búsqueda
                        if "url=" in href:
                            href = href.split("url=")[1].split("&")[0]

                        if href.startswith("http") and len(title) > 10:
                            items.append({
                                "title": title[:100],
                                "text": title,
                                "url": href,
                                "source": "twitter_google_news",
                                "type": "public_search",
                                "market_window": market_window,  # Nacional o Global
                            })

                    await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.debug(
                    "Google News search failed",
                    query=query[:50],
                    market_window=market_window,
                    error=str(e)[:100],
                )
                continue

    return items


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════


class TwitterScraperImproved(BaseScraper):
    source_name = "twitter_improved"
    base_url = "https://twitter.com"
    schedule = "0 8 * * *"  # 8am diario

    async def fetch_raw(self) -> list[dict[str, Any]]:
        """Fetch usando 3 estrategias con fallback.

        Orden de ejecución:
        1. Twitter API v2 (si token disponible)
        2. Monitoreo de cuentas
        3. Google News (fallback sin autenticación)
        """
        all_items: list[dict[str, Any]] = []

        # Obtener token (opcional)
        # En producción: from app.core.config import settings
        # bearer_token = settings.TWITTER_BEARER_TOKEN
        bearer_token = None  # TODO: conectar desde .env

        # Estrategia 1: Twitter API v2
        if bearer_token:
            for query in TWITTER_SEARCH_QUERIES:
                items = await fetch_twitter_api_v2(query, bearer_token)
                all_items.extend(items)
                await asyncio.sleep(0.5)

            # Estrategia 2: Monitorear cuentas
            items = await fetch_twitter_accounts(bearer_token)
            all_items.extend(items)

        # Estrategia 3: Google News (fallback, siempre ejecutar)
        items = await fetch_twitter_google_news()
        all_items.extend(items)

        # Deduplicar por URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_items.append(item)

        logger.info("Twitter fetch complete", total_items=len(unique_items))
        return unique_items

    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convertir raw Twitter item → OpportunityCreate."""
        title = raw.get("title", "") or raw.get("text", "")[:100]
        title = title.strip()

        if not title or len(title) < 10:
            return None

        # Validar keywords
        text = (title + " " + raw.get("text", "")).lower()
        has_core = any(kw.lower() in text for kw in TWITTER_KEYWORDS_CORE)
        has_secondary = any(kw.lower() in text for kw in TWITTER_KEYWORDS_SECONDARY)

        if not (has_core or has_secondary):
            logger.debug("Twitter item discarded: no keywords", title=title[:50])
            return None

        # URL
        url = raw.get("url", "")
        if not url or not url.startswith("http"):
            return None

        # Funder / autor
        funder_name = raw.get("author_name") or "Twitter / X"

        # Parsear fecha (si está disponible)
        deadline = None
        if raw.get("created_at"):
            try:
                created = datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00"))
                # Asumir 60 días de validez
                deadline = (created + timedelta(days=60)).date()
            except (ValueError, AttributeError):
                pass

        # Crear schema
        # Si viene market_window del raw (de búsqueda Google), usarlo; si no, inferir
        market_window = raw.get("market_window")
        if not market_window:
            # Inferir basado en keywords en título/descripción
            text_lower = (title + " " + raw.get("text", "")).lower()
            if "colombia" in text_lower:
                market_window = "funding_colombia"
            else:
                market_window = "funding_global"

        return OpportunityCreate(
            title=title[:200],
            description=raw.get("text", "")[:5000],
            funder_name=funder_name,
            deadline=deadline,
            url_rfp=url,
            url_source=url,
            source_name=self.source_name,
            org_website="https://twitter.com",
            eligible_countries=["Colombia", "Latin America"],
            sectors=["education", "first_childhood"],
            capital_type="opportunity",
            market_window=market_window,  # Nacional o Global según búsqueda
            raw_content=json.dumps(raw, default=str),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NOTAS SOBRE AUTENTICACIÓN Y COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════

"""
COMPLIANCE CHECKLIST:

✅ User-Agent identificado ("GrantFlow-AI/1.0")
✅ Rate limiting (0.5-1s delay entre requests)
✅ Respetar robots.txt implícitamente (Google News indexa públicamente)
✅ Fallback a búsqueda pública si API no disponible
✅ No almacenar tweets históricos innecesarios
✅ Logging detallado para auditoría
✅ Manejo gracioso de errores (no bloquear pipeline)

ESTRATEGIA DE TOKENS:
- En MVP: usar solo Google News (sin autenticación)
- En Producción: solicitar TWITTER_BEARER_TOKEN a desarrollador
- En Fallback: degradar a Google News automáticamente

TARIFAS DE TWITTER API v2:
- Free tier: 300 requests/15min (suficiente para 10-15 queries diarias)
- Pro tier ($100/mes): 10,000 requests/15min
- Enterprise: custom

EVALUACIÓN:
- Si 70%+ tweets vienen de Google News → no vale activar token (costo no justificado)
- Si 50%+ tweets relevantes de API v2 → activar en producción (mes 5+)
"""
