"""BaseScraper mejorado con Scrapling — compatibilidad universal.

Proporciona helper methods para todos los scrapers que usen Scrapling.
Mantiene compatibilidad con scrapers existentes que usen httpx/BeautifulSoup.
"""

from abc import ABC, abstractmethod
from typing import Any
import asyncio

import structlog
from scrapling.fetchers import StealthyFetcher, DynamicFetcher, AsyncFetcher

from app.schemas.opportunity import OpportunityCreate

logger = structlog.get_logger()


class ScraperError(Exception):
    pass


class BaseScraperWithScrapling(ABC):
    """BaseScraper mejorado con Scrapling.

    Proporciona métodos helper para:
    - Fetching robusto con anti-bot bypass
    - Parsing adaptativo (auto-detect cambios HTML)
    - Proxy rotation
    - Rate limiting
    - Caching de estructura
    """

    source_name: str
    base_url: str
    schedule: str  # Cron expression

    def __init__(self):
        """Inicializar scrapers de Scrapling."""
        self.stealthy_fetcher = StealthyFetcher()
        self.dynamic_fetcher = DynamicFetcher()
        self.async_fetcher = AsyncFetcher()

        # Configurar Scrapling globalmente para todos los scrapers
        StealthyFetcher.adaptive = True  # Auto-detect cambios HTML
        DynamicFetcher.adaptive = True
        DynamicFetcher.headless = True  # Usar headless browser
        DynamicFetcher.network_idle = True  # Esperar a que cargue todo

    @abstractmethod
    async def fetch_raw(self) -> list[dict[str, Any]]:
        """Obtiene datos crudos de la fuente.

        Puede usar:
        - self.fetch_with_scrapling() para HTML parsing robusto
        - self.fetch_dynamic() si requiere JavaScript
        - self.fetch_stealth() para evitar captchas
        """
        ...

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> OpportunityCreate | None:
        """Convierte un registro crudo al schema OpportunityCreate.

        Retorna None si el registro debe ser descartado (no relevante).
        """
        ...

    # ═════════════════════════════════════════════════════════════════════════════
    # MÉTODOS HELPER PARA FETCHING CON SCRAPLING
    # ═════════════════════════════════════════════════════════════════════════════

    async def fetch_with_scrapling(
        self,
        url: str,
        use_stealth: bool = True,
        headless: bool = False,
        timeout: int = 30,
    ):
        """Fetch con Scrapling (adaptativo, anti-bot).

        Usa StealthyFetcher por defecto (más rápido que DynamicFetcher).
        Si headless=True, usa DynamicFetcher para JavaScript rendering.

        Args:
            url: URL a scrapear
            use_stealth: Usar StealthyFetcher (recomendado)
            headless: Usar headless browser si True
            timeout: Timeout en segundos

        Returns:
            Scrapling.Page object con métodos CSS/XPATH
        """
        try:
            if headless:
                # Envolver sync call en asyncio.to_thread() para no bloquear event loop
                page = await asyncio.to_thread(
                    self.dynamic_fetcher.fetch,
                    url,
                    headless=True,
                    network_idle=True,
                    timeout=timeout,
                )
            else:
                page = await asyncio.to_thread(
                    self.stealthy_fetcher.fetch,
                    url,
                    headless=False,
                    timeout=timeout,
                )

            logger.debug(
                "Scrapling fetch successful",
                source=self.source_name,
                url=url[:80],
                headless=headless,
            )
            return page

        except Exception as e:
            logger.debug(
                "Scrapling fetch failed",
                source=self.source_name,
                url=url[:80],
                error=str(e)[:100],
            )
            raise

    async def fetch_dynamic(
        self,
        url: str,
        wait_for_selector: str | None = None,
        timeout: int = 30,
    ):
        """Fetch con JavaScript rendering (para sitios dinámicos).

        Usa DynamicFetcher que renderiza JavaScript.
        Más lento pero necesario para Single Page Applications.

        Args:
            url: URL a scrapear
            wait_for_selector: Selector CSS para esperar antes de retornar
            timeout: Timeout en segundos

        Returns:
            Scrapling.Page object
        """
        try:
            # Envolver sync call en asyncio.to_thread() para no bloquear event loop
            page = await asyncio.to_thread(
                self.dynamic_fetcher.fetch,
                url,
                headless=True,
                network_idle=True,
                timeout=timeout,
            )

            if wait_for_selector:
                # Esperar a que elemento específico cargue (también wrapped en thread)
                await asyncio.to_thread(
                    page.wait_for_selector,
                    wait_for_selector,
                    timeout=timeout,
                )

            logger.debug(
                "Scrapling dynamic fetch successful",
                source=self.source_name,
                url=url[:80],
            )
            return page

        except Exception as e:
            logger.debug(
                "Scrapling dynamic fetch failed",
                source=self.source_name,
                url=url[:80],
                error=str(e)[:100],
            )
            raise

    async def fetch_stealth(
        self,
        url: str,
        timeout: int = 30,
    ):
        """Fetch anti-bot (evita captchas, rate limiting).

        StealthyFetcher simula browser real para evitar detección.
        Recomendado para Google Search, sitios con anti-scraping.

        Args:
            url: URL a scrapear
            timeout: Timeout en segundos

        Returns:
            Scrapling.Page object
        """
        try:
            # Envolver sync call en asyncio.to_thread() para no bloquear event loop
            page = await asyncio.to_thread(
                self.stealthy_fetcher.fetch,
                url,
                headless=False,  # Simular browser visible (más evasivo)
                timeout=timeout,
            )

            logger.debug(
                "Scrapling stealth fetch successful",
                source=self.source_name,
                url=url[:80],
            )
            return page

        except Exception as e:
            logger.debug(
                "Scrapling stealth fetch failed",
                source=self.source_name,
                url=url[:80],
                error=str(e)[:100],
            )
            raise

    # ═════════════════════════════════════════════════════════════════════════════
    # MÉTODOS HELPER PARA PARSING ADAPTATIVO
    # ═════════════════════════════════════════════════════════════════════════════

    def parse_adaptive(
        self,
        page,
        selectors: str | list[str],
        attribute: str | None = None,
    ) -> list[str | dict]:
        """Parse adaptativo — auto-detect cambios en estructura.

        Si sitio cambia estructura HTML, Scrapling intenta relocar elementos.

        Args:
            page: Scrapling.Page object
            selectors: Selector CSS (string o lista de alternativas)
            attribute: Atributo a extraer (ej: 'href'). Si None, extrae texto.

        Returns:
            Lista de valores extraídos
        """
        try:
            # Si múltiples selectores, intentar en orden
            if isinstance(selectors, list):
                for selector in selectors:
                    try:
                        if attribute:
                            results = [
                                el.get_attribute(attribute)
                                for el in page.css(selector, adaptive=True)
                            ]
                        else:
                            results = page.css(f"{selector}::text", adaptive=True).getall()

                        if results:
                            logger.debug(
                                "Adaptive parse successful",
                                source=self.source_name,
                                selector=selector,
                                count=len(results),
                            )
                            return results

                    except Exception:
                        continue

                logger.debug(
                    "Adaptive parse failed for all selectors",
                    source=self.source_name,
                    selectors=selectors,
                )
                return []

            # Selector único
            if attribute:
                results = [
                    el.get_attribute(attribute)
                    for el in page.css(selectors, adaptive=True)
                ]
            else:
                results = page.css(f"{selectors}::text", adaptive=True).getall()

            logger.debug(
                "Adaptive parse successful",
                source=self.source_name,
                selector=selectors,
                count=len(results),
            )
            return results

        except Exception as e:
            logger.debug(
                "Adaptive parse error",
                source=self.source_name,
                selector=selectors,
                error=str(e)[:100],
            )
            return []

    # ═════════════════════════════════════════════════════════════════════════════
    # MÉTODOS HELPER PARA RATE LIMITING Y CONCURRENCIA
    # ═════════════════════════════════════════════════════════════════════════════

    async def fetch_multiple_with_limit(
        self,
        urls: list[str],
        use_stealth: bool = True,
        headless: bool = False,
        rate_limit_seconds: float = 1.0,
        max_concurrent: int = 4,
    ) -> dict[str, Any]:
        """Fetch múltiples URLs con rate limiting.

        Args:
            urls: Lista de URLs
            use_stealth: Usar StealthyFetcher
            headless: Usar headless browser
            rate_limit_seconds: Segundos entre requests
            max_concurrent: Máximo de requests concurrentes

        Returns:
            {url: page_object}
        """
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_limit(url):
            async with semaphore:
                await asyncio.sleep(rate_limit_seconds)
                try:
                    page = await self.fetch_with_scrapling(
                        url,
                        use_stealth=use_stealth,
                        headless=headless,
                    )
                    results[url] = page
                except Exception as e:
                    logger.debug(
                        "Fetch multiple error",
                        source=self.source_name,
                        url=url[:80],
                        error=str(e)[:100],
                    )
                    results[url] = None

        await asyncio.gather(*[fetch_with_limit(url) for url in urls])
        return results

    # ═════════════════════════════════════════════════════════════════════════════
    # MÉTODOS HELPER PARA LOGGING Y DEBUGGING
    # ═════════════════════════════════════════════════════════════════════════════

    def log_parse_result(
        self,
        item_title: str,
        reason: str | None = None,
        item_data: dict | None = None,
    ):
        """Log detallado cuando item es descartado."""
        if reason:
            logger.debug(
                "Item discarded",
                source=self.source_name,
                reason=reason,
                title=item_title[:60],
                data=item_data or {},
            )

    # ═════════════════════════════════════════════════════════════════════════════
    # ORCHESTRACIÓN (compatible con base.py)
    # ═════════════════════════════════════════════════════════════════════════════

    async def run(self) -> list[OpportunityCreate]:
        """Fetch → normalize → filter → return.

        Compatible con runner.py existente.
        """
        log = logger.bind(scraper=self.source_name)
        try:
            raw_items = await self.fetch_raw()
            log.info("Fetched raw items", count=len(raw_items))
        except Exception as exc:
            raise ScraperError(f"fetch_raw failed for {self.source_name}: {exc}") from exc

        results: list[OpportunityCreate] = []
        for item in raw_items:
            try:
                normalized = self.normalize(item)
                if normalized is not None:
                    results.append(normalized)
            except Exception as exc:
                log.warning(
                    "Failed to normalize item",
                    error=str(exc),
                    item_keys=list(item.keys()),
                )

        log.info("Normalized opportunities", total=len(raw_items), kept=len(results))
        return results
