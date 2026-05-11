import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityRead
from app.services.scoring_engine import ScoringEngine

logger = structlog.get_logger()
router = APIRouter()


@router.post("/{opportunity_id}/score", response_model=OpportunityRead)
async def rescore_opportunity(
    opportunity_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> OpportunityRead:
    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    engine = ScoringEngine()
    background_tasks.add_task(engine.score_and_persist, opportunity_id, db)

    logger.info("Scoring enqueued", opportunity_id=str(opportunity_id))
    return OpportunityRead.model_validate(opp)
