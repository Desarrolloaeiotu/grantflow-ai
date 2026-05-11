from abc import ABC, abstractmethod

import structlog

from app.schemas.opportunity import OpportunityCreate

logger = structlog.get_logger()


class ScraperError(Exception):
    pass


class BaseScraper(ABC):
    source_name: str
    base_url: str
    schedule: str  # Cron expression

    @abstractmethod
    async def fetch_raw(self) -> list[dict]:
        """Obtiene datos crudos de la fuente."""
        ...

    @abstractmethod
    def normalize(self, raw: dict) -> OpportunityCreate | None:
        """Convierte un registro crudo al schema OpportunityCreate.

        Retorna None si el registro debe ser descartado (no relevante).
        """
        ...

    async def run(self) -> list[OpportunityCreate]:
        """Fetch → normalize → filter → return."""
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
                log.warning("Failed to normalize item", error=str(exc), item_keys=list(item.keys()))

        log.info("Normalized opportunities", total=len(raw_items), kept=len(results))
        return results
