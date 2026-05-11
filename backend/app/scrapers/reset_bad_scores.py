"""Resetea scores corruptos por errores 429/quota del rescore.

Identifica oportunidades cuyo score_details.llm_justification contiene
"LLM error" y las devuelve a estado neutro para re-scorearlas más tarde.

Uso:
    python -m app.scrapers.reset_bad_scores
"""

import asyncio

import structlog
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = structlog.get_logger()


async def main() -> None:
    async with AsyncSessionLocal() as db:
        # Contar antes
        count_q = text("""
            SELECT COUNT(*) FROM opportunities
            WHERE score_details->>'llm_justification' ILIKE '%LLM error%'
        """)
        before = (await db.execute(count_q)).scalar_one()
        logger.info("Bad scores found", count=before)

        if before == 0:
            logger.info("Nothing to reset.")
            return

        # Reset: limpiar score, decision, market_window
        # Mantener urgency (es deterministic-from-deadline)
        update_q = text("""
            UPDATE opportunities
            SET
              score_total = NULL,
              score_details = NULL,
              decision = NULL,
              market_window = NULL
            WHERE score_details->>'llm_justification' ILIKE '%LLM error%'
        """)
        await db.execute(update_q)
        await db.commit()

        logger.info("Reset complete", reset=before)


if __name__ == "__main__":
    asyncio.run(main())
