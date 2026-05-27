"""Re-puntua oportunidades existentes con el ScoringEngine activo.

Útil cuando:
- Acabas de configurar GOOGLE_API_KEY o ANTHROPIC_API_KEY y quieres
  re-procesar las oportunidades que se persistieron sin LLM scoring.
- Cambias los pesos o la lógica del scoring engine.

Uso:
    python -m app.scrapers.rescore                    # solo opps sin scoring real
    python -m app.scrapers.rescore --all              # todas las opps
    python -m app.scrapers.rescore --limit 50         # primeras 50

Robustez:
- Sesión nueva por batch de 10 opps (evita connection-closed en el pooler).
- Rollback explícito en errores.
- Backoff exponencial en errores 429 / quota exceeded.
"""

import argparse
import asyncio
import uuid

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.opportunity import Opportunity
from app.services.scoring_engine import ScoringEngine

logger = structlog.get_logger()

# Gemini 2.5 Flash free tier: 10 RPM. Delay de 7s = ~8.5 RPM, margen seguro.
# Una llamada LLM por opp.
GEMINI_DELAY_SEC = 7.0
ANTHROPIC_DELAY_SEC = 0.0
BATCH_SIZE = 10
# En 429 transitorio (rate limit por minuto), reintentar.
MAX_RETRIES_429 = 2
RETRY_BACKOFF_SEC = 35  # Espera ~media ventana de RPM


async def _fetch_pending_ids(rescore_all: bool, limit: int | None) -> list[uuid.UUID]:
    async with AsyncSessionLocal() as db:
        query = select(Opportunity.id)
        if not rescore_all:
            query = query.where(
                or_(
                    Opportunity.score_total.is_(None),
                    Opportunity.market_window.is_(None),
                )
            )
        if limit:
            query = query.limit(limit)
        result = await db.execute(query)
        return [row[0] for row in result.all()]


async def _score_one_with_retry(
    engine: ScoringEngine,
    opp_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[bool, str | None]:
    """Intenta scorear una opp. Reintenta en 429 transitorios.

    Devuelve (success, fatal_error_msg).
    Si fatal_error_msg != None, el caller debe abortar todo (cuota agotada).
    """
    last_msg: str | None = None
    for attempt in range(MAX_RETRIES_429 + 1):
        try:
            await engine.score_and_persist(opp_id, db)
            return True, None
        except Exception as exc:
            msg = str(exc)
            last_msg = msg
            try:
                await db.rollback()
            except Exception:
                pass

            is_429 = "429" in msg or "rate" in msg.lower()
            is_quota = "quota" in msg.lower()

            if not (is_429 or is_quota):
                # Error no relacionado con rate/quota — fallar la opp pero no abortar
                logger.error("Score failed (non-quota)", opp_id=str(opp_id), error=msg[:200])
                return False, None

            if attempt < MAX_RETRIES_429:
                logger.warning(
                    "Rate limit hit, retrying",
                    opp_id=str(opp_id),
                    attempt=attempt + 1,
                    backoff=RETRY_BACKOFF_SEC,
                )
                await asyncio.sleep(RETRY_BACKOFF_SEC)
                continue

            # Tras varios reintentos seguidos: probablemente cuota diaria
            logger.error(
                "Quota exhausted after retries — aborting",
                opp_id=str(opp_id),
                error=msg[:200],
            )
            return False, msg

    return False, last_msg


async def _process_batch(
    engine: ScoringEngine,
    ids: list[uuid.UUID],
    delay: float,
) -> tuple[int, int, bool]:
    """Procesa un batch en su propia sesión.

    Devuelve (succeeded, failed, quota_exceeded).
    Si quota_exceeded == True, el caller debe abortar.
    """
    succeeded = 0
    failed = 0
    quota_exceeded = False

    async with AsyncSessionLocal() as db:
        for i, opp_id in enumerate(ids):
            success, fatal = await _score_one_with_retry(engine, opp_id, db)
            if success:
                succeeded += 1
            else:
                failed += 1
                if fatal:
                    quota_exceeded = True
                    break

            if delay > 0 and i < len(ids) - 1:
                await asyncio.sleep(delay)

        try:
            await db.commit()
        except Exception:
            await db.rollback()

    return succeeded, failed, quota_exceeded


async def rescore_batch(rescore_all: bool = False, limit: int | None = None) -> dict[str, int]:
    """Ejecuta rescoring y devuelve stats. Llamable como función desde endpoints."""
    engine = ScoringEngine()
    if engine._provider == "none":
        logger.error(
            "No LLM provider configured. Set GOOGLE_API_KEY or ANTHROPIC_API_KEY in .env"
        )
        return {"total": 0, "succeeded": 0, "failed": 0}

    delay = GEMINI_DELAY_SEC if engine._provider == "gemini" else ANTHROPIC_DELAY_SEC
    logger.info("Rescoring start", provider=engine._provider, delay=delay)

    ids = await _fetch_pending_ids(rescore_all, limit)
    total = len(ids)
    logger.info("Opportunities to score", count=total)

    total_ok = 0
    total_failed = 0
    aborted = False

    for batch_idx in range(0, total, BATCH_SIZE):
        batch = ids[batch_idx : batch_idx + BATCH_SIZE]
        ok, failed, quota_exceeded = await _process_batch(engine, batch, delay)
        total_ok += ok
        total_failed += failed
        logger.info(
            "Batch done",
            batch=batch_idx // BATCH_SIZE + 1,
            ok=total_ok,
            failed=total_failed,
            total=total,
        )
        if quota_exceeded:
            logger.error(
                "QUOTA EXCEEDED — aborting. Try again tomorrow or upgrade plan.",
            )
            aborted = True
            break

    logger.info(
        "Rescoring complete",
        succeeded=total_ok,
        failed=total_failed,
        total=total,
        aborted=aborted,
    )

    return {"total": total, "succeeded": total_ok, "failed": total_failed}


async def main(rescore_all: bool, limit: int | None) -> None:
    await rescore_batch(rescore_all, limit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Re-score TODAS las opps")
    parser.add_argument("--limit", type=int, default=None, help="Máximo N opps")
    args = parser.parse_args()
    asyncio.run(main(args.all, args.limit))
