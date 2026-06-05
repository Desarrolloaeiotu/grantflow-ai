"""
Orquestador de Scrapers para Tenders Global
Integra múltiples fuentes: Grants.gov, BID, UN Women, RSS feeds
"""
import asyncio
from datetime import datetime, timezone
import hashlib
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity
from app.models.funder import Funder
from app.core.database import AsyncSessionLocal
from app.scrapers.grantsgov import GrantsGovScraper
from app.scrapers.bid import BidScraper
from app.scrapers.unwomen import UnWomenScraper
from app.scrapers.rss_feeds import RssFeedsScraper
from app.schemas.opportunity import OpportunityCreate

logger = structlog.get_logger()

# Monto mínimo para GLOBAL: COP $100M (~USD $25K)
GLOBAL_MIN_COP = 100_000_000
USD_TO_COP = 4050


class TendersGlobalScraper:
    """Orquestador de scrapers para convocatorias GLOBAL"""

    def __init__(self):
        self.scrapers = [
            GrantsGovScraper(),
            BidScraper(),
            UnWomenScraper(),
            RssFeedsScraper(),
        ]

    async def scrape_all_tenders(self) -> dict:
        """Ejecutar todos los scrapers y agregar resultados"""
        results = {
            "total_scraped": 0,
            "total_imported": 0,
            "by_source": {},
        }

        for scraper in self.scrapers:
            try:
                logger.info(f"Running scraper: {scraper.source_name}")

                # Ejecutar scraper
                opps = await scraper.run()

                # Filtrar por monto mínimo
                filtered_opps = [
                    opp for opp in opps
                    if self._meets_global_criteria(opp)
                ]

                logger.info(
                    f"Scraper {scraper.source_name} found {len(opps)} opportunities, "
                    f"{len(filtered_opps)} meet global criteria"
                )

                # Importar a BD
                imported = await self._import_opportunities(filtered_opps)

                results["total_scraped"] += len(opps)
                results["total_imported"] += imported
                results["by_source"][scraper.source_name] = {
                    "scraped": len(opps),
                    "imported": imported,
                }

            except Exception as e:
                logger.error(f"Error in scraper {scraper.source_name}: {e}")
                results["by_source"][scraper.source_name] = {
                    "error": str(e),
                }

        return results

    def _meets_global_criteria(self, opp: OpportunityCreate) -> bool:
        """Verificar si cumple criterios GLOBAL"""
        # 1. Monto mínimo
        if opp.amount_max_cop and opp.amount_max_cop < GLOBAL_MIN_COP:
            return False

        # 2. Si es USD, convertir y revisar
        if opp.amount_max_cop is None and hasattr(opp, "amount_max_usd"):
            amount_usd = getattr(opp, "amount_max_usd", None)
            if amount_usd and (amount_usd * USD_TO_COP) < GLOBAL_MIN_COP:
                return False

        # 3. Verificar palabras clave de ECD/educación
        keywords = ["early childhood", "ecd", "educación inicial", "education", "development"]
        combined_text = (
            f"{opp.title} {opp.description or ''}".lower()
        )
        if not any(kw in combined_text for kw in keywords):
            return False

        return True

    async def _import_opportunities(self, opps: list[OpportunityCreate]) -> int:
        """Importar oportunidades a BD, evitando duplicados"""
        async with AsyncSessionLocal() as session:
            imported = 0

            for opp in opps:
                try:
                    # Crear hash para detectar duplicados
                    opp_hash = self._hash_opportunity(opp)

                    # Verificar si existe
                    existing = await session.execute(
                        select(Opportunity).where(
                            Opportunity.title == opp.title,
                            Opportunity.deadline == opp.deadline,
                            Opportunity.source_name == opp.source_name,
                        )
                    )
                    if existing.scalar():
                        logger.debug(f"Opportunity already exists: {opp.title}")
                        continue

                    # Obtener funder si existe
                    funder_id = None
                    if opp.funder_name:
                        funder_result = await session.execute(
                            select(Funder).where(Funder.name.ilike(f"%{opp.funder_name}%"))
                        )
                        funder = funder_result.scalar()
                        if funder:
                            funder_id = funder.id

                    # Crear oportunidad
                    db_opp = Opportunity(
                        title=opp.title,
                        description=opp.description,
                        funder_id=funder_id,
                        amount_min_cop=opp.amount_min_cop,
                        amount_max_cop=opp.amount_max_cop,
                        deadline=opp.deadline,
                        open_date=opp.open_date,
                        url_rfp=opp.url_rfp,
                        url_source=opp.url_source,
                        source_name=opp.source_name,
                        market_window="funding_global",
                        tender_type=getattr(opp, "tender_type", None),
                        status="detected",
                        detected_at=datetime.now(timezone.utc),
                        raw_content=getattr(opp, "raw_content", None),
                    )
                    session.add(db_opp)
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing opportunity: {e}")
                    await session.rollback()
                    continue

            if imported > 0:
                await session.commit()
                logger.info(f"Imported {imported} opportunities")

            return imported

    def _hash_opportunity(self, opp: OpportunityCreate) -> str:
        """Crear hash para detectar duplicados"""
        text = f"{opp.title}|{opp.deadline}|{opp.source_name}"
        return hashlib.md5(text.encode()).hexdigest()


async def run_global_scraping():
    """Ejecutar scraping global"""
    scraper = TendersGlobalScraper()
    results = await scraper.scrape_all_tenders()

    logger.info("Global scraping complete", results=results)
    return results


if __name__ == "__main__":
    asyncio.run(run_global_scraping())
