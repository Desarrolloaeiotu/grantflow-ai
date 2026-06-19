"""Cleanup script to mark non-convocatoria entries in funding_global as discarded."""

import asyncio
import sys
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.opportunity import Opportunity
from app.services.content_type_detector import ContentType, detect_content_type

logger = structlog.get_logger()


async def cleanup_global_opportunities() -> int:
    """
    Remove news/articles from existing global opportunities table.

    Queries all opportunities where market_window='funding_global',
    classifies each by content type, and marks non-convocatoria items
    as discarded.

    Returns:
        Number of items marked as discarded
    """
    async with AsyncSessionLocal() as session:
        # Fetch all global opportunities
        query = select(Opportunity).where(
            Opportunity.market_window == "funding_global"
        )
        result = await session.execute(query)
        opps = result.scalars().all()

        logger.info("Starting cleanup", total_global_opps=len(opps))

        rejected_count = 0
        for opp in opps:
            # Classify content type
            content_result = detect_content_type(
                {
                    "title": opp.title,
                    "description": opp.description or "",
                    "url": opp.url_source or "",
                }
            )

            # Mark as discarded if not a convocatoria
            if content_result.type != ContentType.CONVOCATORIA:
                logger.info(
                    "Marking as discarded",
                    opp_id=str(opp.id),
                    title=opp.title[:50],
                    content_type=content_result.type,
                    reason=content_result.reason,
                    confidence=content_result.confidence,
                )
                opp.status = "discarded"
                opp.updated_at = datetime.now(timezone.utc)
                rejected_count += 1

        # Commit all changes
        await session.commit()
        logger.info("Cleanup complete", rejected_count=rejected_count)
        return rejected_count


async def main():
    """Entry point for CLI execution."""
    try:
        count = await cleanup_global_opportunities()
        print(f"\n[OK] Cleanup done: {count} items marked as discarded")
        return 0
    except Exception as e:
        logger.error("Cleanup failed", error=str(e), exc_info=True)
        print(f"\n[ERROR] Cleanup failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
