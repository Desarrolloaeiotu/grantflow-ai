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
from datetime import date

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.funder import Funder
from app.models.opportunity import Opportunity
from app.scrapers.base import ScraperError
from app.scrapers.bid import BidScraper
from app.scrapers.developmentaid import DevelopmentAidScraper
from app.scrapers.grantsgov import GrantsGovScraper
from app.scrapers.nacional_colombia import NacionalColombiaScraper
from app.scrapers.rss_feeds import RssFeedsScraper
from app.scrapers.tenders_scraper import TendersScraper
from app.scrapers.unwomen import UnWomenScraper
from app.scrapers.metrics_monitor import (
    save_scraper_metrics,
    detect_drop,
    get_weekly_average,
    alert_metrics_drop_to_slack,
)
from app.services.scoring_engine import ScoringEngine

logger = structlog.get_logger()

# Limit concurrent scrapers to avoid overloading
MAX_CONCURRENT = 4

SCRAPERS = {
    # v2: Tenders scrapers with amount filtering
    "tenders_global": ("tenders", "global"),      # ≥ COP $100M — Grants.gov, BID, UN Women, RSS
    "tenders_nacional": ("tenders", "nacional"),  # ≥ COP $50M — Nacional Colombia

    # Legacy: Individual scrapers (kept for backwards compatibility)
    "nacional_colombia": NacionalColombiaScraper,  # 5am — prioridad nacional
    "grantsgov": GrantsGovScraper,
    "bid": BidScraper,
    "unwomen": UnWomenScraper,
    "developmentaid": DevelopmentAidScraper,
    "rss": RssFeedsScraper,
}


async def run_scraper(name: str, do_score: bool = False) -> int:
    import time
    start_time = time.time()

    scraper_config = SCRAPERS.get(name)
    if not scraper_config:
        logger.error("Unknown scraper", name=name)
        return 0

    # Handle both new TendersScraper (tuple) and legacy BaseScraper (class)
    if isinstance(scraper_config, tuple):
        # v2 TendersScraper: ("tenders", "global"|"nacional")
        scraper_type, region = scraper_config
        scraper = TendersScraper()
        try:
            opportunities = await scraper.run(region=region)
        except Exception as exc:
            logger.error("Tenders scraper failed", scraper=name, region=region, error=str(exc))
            return 0
    else:
        # Legacy BaseScraper
        scraper_cls = scraper_config
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
                market_window=opp_create.market_window,
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

        # Guardar métricas del run
        duration_sec = time.time() - start_time
        await save_scraper_metrics(
            {
                "scraper_name": name,
                "total_normalized": len(opportunities),  # post-normalize, pre-dedup
                "total_persisted": persisted,
                "total_skipped": skipped,
                "errors_count": 0,  # TODO: track individual normalize errors
                "duration_sec": duration_sec,
                "run_date": date.today(),
            },
            db=db,
        )

        # Detectar caída anormal en tasa de éxito
        if await detect_drop(name, len(opportunities)):
            avg = await get_weekly_average(name)
            if avg:
                await alert_metrics_drop_to_slack(name, len(opportunities), avg)

    logger.info(
        "Scraper run complete",
        scraper=name,
        persisted=persisted,
        skipped_duplicates=skipped,
        scored=do_score and not quota_exceeded,
    )
    return persisted


async def main(source: str | None = None, do_score: bool = False) -> None:
    """Ejecuta todos los scrapers: nacional_colombia primero, resto en paralelo."""
    if source:
        # Single scraper: run sequentially as before
        count = await run_scraper(source, do_score=do_score)
        logger.info("Scraper done", scraper=source, total_persisted=count)
        return

    log = logger.bind(action="run_all_scrapers")
    log.info("Starting scraper run", max_concurrent=MAX_CONCURRENT)

    # 1. nacional_colombia PRIMERO (prioridad máxima)
    nacional_count = await run_scraper("nacional_colombia", do_score=do_score)

    # 2. Scrapers secundarios en paralelo con semáforo para limitar concurrencia
    secondary_scrapers = [n for n in SCRAPERS if n != "nacional_colombia"]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def run_with_semaphore(name: str) -> int:
        async with semaphore:
            return await run_scraper(name, do_score=do_score)

    # Ejecutar en paralelo, permitiendo que fallos individuales no bloqueen otros
    results = await asyncio.gather(
        *[run_with_semaphore(name) for name in secondary_scrapers],
        return_exceptions=True,
    )

    # Consolidar resultados (ignorar excepciones)
    secondary_count = sum(r for r in results if isinstance(r, int))
    total = nacional_count + secondary_count

    log.info(
        "All scrapers done",
        nacional=nacional_count,
        secondary=secondary_count,
        total_persisted=total,
    )


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
