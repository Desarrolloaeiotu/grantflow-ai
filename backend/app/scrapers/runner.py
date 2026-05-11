"""Ejecuta todos los scrapers activos y persiste los resultados.

Uso:
    python -m app.scrapers.runner                    # todos
    python -m app.scrapers.runner --source grantsgov # uno específico
    python -m app.scrapers.runner --score            # con scoring inmediato (consume cuota LLM)

Por defecto el scoring está desacoplado: el runner solo persiste opps.
Después corres `python -m app.scrapers.rescore` para scorear con LLM.
Esto evita que un fallo de cuota bloquee la ingesta de datos.
"""

import argparse
import asyncio

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.funder import Funder
from app.models.opportunity import Opportunity
from app.scrapers.base import ScraperError
from app.scrapers.bid import BidScraper
from app.scrapers.developmentaid import DevelopmentAidScraper
from app.scrapers.grantsgov import GrantsGovScraper
from app.scrapers.rss_feeds import RssFeedsScraper
from app.scrapers.unwomen import UnWomenScraper
from app.services.scoring_engine import ScoringEngine

logger = structlog.get_logger()

SCRAPERS = {
    "grantsgov": GrantsGovScraper,
    "bid": BidScraper,
    "unwomen": UnWomenScraper,
    "developmentaid": DevelopmentAidScraper,
    "rss": RssFeedsScraper,
}


async def run_scraper(name: str, do_score: bool = False) -> int:
    scraper_cls = SCRAPERS.get(name)
    if not scraper_cls:
        logger.error("Unknown scraper", name=name)
        return 0

    scraper = scraper_cls()
    try:
        opportunities = await scraper.run()
    except ScraperError as exc:
        logger.error("Scraper failed", scraper=name, error=str(exc))
        return 0

    engine = ScoringEngine() if do_score else None
    persisted = 0
    skipped = 0
    quota_exceeded = False

    async with AsyncSessionLocal() as db:
        for opp_create in opportunities:
            # Evitar duplicados por url_source
            if opp_create.url_source:
                existing = (
                    await db.execute(
                        select(Opportunity).where(Opportunity.url_source == opp_create.url_source)
                    )
                ).scalar_one_or_none()
                if existing:
                    skipped += 1
                    continue

            # Resolver funder_id
            funder_id = None
            if opp_create.funder_name:
                funder = (
                    await db.execute(
                        select(Funder).where(Funder.name.ilike(f"%{opp_create.funder_name}%"))
                    )
                ).scalar_one_or_none()
                if not funder:
                    funder = Funder(name=opp_create.funder_name)
                    db.add(funder)
                    await db.flush()
                funder_id = funder.id

            opp = Opportunity(
                title=opp_create.title,
                description=opp_create.description,
                funder_id=funder_id,
                amount_min_cop=opp_create.amount_min_cop,
                amount_max_cop=opp_create.amount_max_cop,
                deadline=opp_create.deadline,
                url_rfp=opp_create.url_rfp,
                url_source=opp_create.url_source,
                source_name=opp_create.source_name,
                org_website=opp_create.org_website,
                capital_type=opp_create.capital_type,
                raw_content=opp_create.raw_content,
                status="detected",
            )
            db.add(opp)
            await db.flush()
            persisted += 1

            # Scoring opcional. Si el provider devuelve 429, dejamos de scorear
            # pero seguimos persistiendo el resto.
            if engine and not quota_exceeded:
                try:
                    await engine.score_and_persist(opp.id, db)
                except Exception as exc:
                    msg = str(exc)
                    if "429" in msg or "quota" in msg.lower():
                        logger.warning(
                            "Quota exceeded — continuing without LLM scoring",
                            scraper=name,
                        )
                        quota_exceeded = True
                        await db.rollback()
                    else:
                        logger.error(
                            "Scoring failed", opp_id=str(opp.id), error=msg[:200]
                        )

        await db.commit()

    logger.info(
        "Scraper run complete",
        scraper=name,
        persisted=persisted,
        skipped_duplicates=skipped,
        scored=do_score and not quota_exceeded,
    )
    return persisted


async def main(source: str | None = None, do_score: bool = False) -> None:
    targets = [source] if source else list(SCRAPERS.keys())
    total = 0
    for name in targets:
        count = await run_scraper(name, do_score=do_score)
        total += count
    logger.info("All scrapers done", total_persisted=total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None)
    parser.add_argument(
        "--score",
        action="store_true",
        help="Scorear con LLM al persistir (consume cuota Gemini/Anthropic)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.source, do_score=args.score))
