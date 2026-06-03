"""Wrapper scraper para convocatorias/tenders filtradas por monto mínimo.

NO es BaseScraper. Ejecuta múltiples scrapers y filtra por región:
- global: ≥ COP $100M (~USD $24K)
- nacional: ≥ COP $50M (~USD $12K)

Schedule: Se ejecuta vía runner.py con prioridad según región.
"""

import structlog
from app.schemas.opportunity import OpportunityCreate
from app.scrapers.base import ScraperError
from app.scrapers.bid import BidScraper
from app.scrapers.developmentaid import DevelopmentAidScraper
from app.scrapers.grantsgov import GrantsGovScraper
from app.scrapers.nacional_colombia import NacionalColombiaScraper
from app.scrapers.rss_feeds import RssFeedsScraper
from app.scrapers.unwomen import UnWomenScraper

logger = structlog.get_logger()

# Monto mínimo en COP para cada región
MIN_AMOUNTS_COP = {
    "global": 100_000_000,      # COP $100M (~USD $24K)
    "nacional": 50_000_000,     # COP $50M (~USD $12K)
}


class TendersScraper:
    """Wrapper que ejecuta scrapers y filtra por monto mínimo."""

    source_name = "tenders"

    async def run(self, region: str = "global") -> list[OpportunityCreate]:
        """Ejecuta scrapers para la región especificada y filtra por monto.

        Args:
            region: 'global' | 'nacional' | 'both'

        Returns:
            Lista de OpportunityCreate filtradas por monto mínimo.
        """
        log = logger.bind(scraper="tenders", region=region)

        # 1. Obtener scrapers según región
        scrapers = self._get_scrapers_for_region(region)
        log.info("Running tenders scrapers", count=len(scrapers), scrapers=[s.source_name for s in scrapers])

        # 2. Ejecutar todos y agregar resultados
        all_opps: list[OpportunityCreate] = []
        errors: dict[str, str] = {}

        for scraper in scrapers:
            try:
                opps = await scraper.run()
                all_opps.extend(opps)
                log.info(
                    "Scraper completed",
                    scraper=scraper.source_name,
                    fetched=len(opps),
                )
            except ScraperError as exc:
                log.warning("Scraper failed", scraper=scraper.source_name, error=str(exc))
                errors[scraper.source_name] = str(exc)
            except Exception as exc:
                log.error("Unexpected error in scraper", scraper=scraper.source_name, error=str(exc))
                errors[scraper.source_name] = str(exc)

        # 3. Filtrar por monto mínimo
        min_amount = MIN_AMOUNTS_COP.get(region, MIN_AMOUNTS_COP["nacional"])

        # Estadísticas
        with_amount = [o for o in all_opps if o.amount_max_cop is not None]
        meets_minimum = [o for o in with_amount if o.amount_max_cop >= min_amount]
        below_minimum = [o for o in with_amount if o.amount_max_cop < min_amount]
        no_amount = [o for o in all_opps if o.amount_max_cop is None]

        log.info(
            "Tenders filtering complete",
            region=region,
            total_fetched=len(all_opps),
            with_amount=len(with_amount),
            meets_minimum=len(meets_minimum),
            below_minimum=len(below_minimum),
            no_amount=len(no_amount),
            min_amount_cop=min_amount,
            errors_count=len(errors),
        )

        return meets_minimum

    def _get_scrapers_for_region(self, region: str) -> list:
        """Retorna lista de scrapers instanciados para la región.

        Args:
            region: 'global' | 'nacional' | 'both'

        Returns:
            Lista de instancias de BaseScraper.
        """
        global_scrapers = [
            GrantsGovScraper(),      # REST API — more reliable
            BidScraper(),            # HTML scraping
            UnWomenScraper(),        # HTML scraping
            DevelopmentAidScraper(), # HTML scraping + RSS
            RssFeedsScraper(),       # Generic RSS feeds (mix of global/latam)
        ]

        nacional_scrapers = [
            NacionalColombiaScraper(),  # SECOP, ICBF, MinEducación, Cajas
        ]

        if region == "global":
            return global_scrapers
        elif region == "nacional":
            return nacional_scrapers
        elif region == "both":
            return global_scrapers + nacional_scrapers
        else:
            raise ValueError(f"Invalid region: {region}. Must be 'global', 'nacional', or 'both'.")


# Alias para que runner.py pueda instantiar como scraper normal
async def run_tenders_global() -> list[OpportunityCreate]:
    """Ejecuta TendersScraper para región global."""
    scraper = TendersScraper()
    return await scraper.run("global")


async def run_tenders_nacional() -> list[OpportunityCreate]:
    """Ejecuta TendersScraper para región nacional."""
    scraper = TendersScraper()
    return await scraper.run("nacional")
