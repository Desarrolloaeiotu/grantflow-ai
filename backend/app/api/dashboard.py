import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.database import get_db
from app.models.opportunity import Opportunity

router = APIRouter()


class DashboardMetrics(BaseModel):
    total_detected: int
    total_go: int
    total_pending: int
    total_no_go: int
    total_in_crm: int
    avg_score_go: float | None
    by_window: dict[str, int]
    by_urgency: dict[str, int]


class PipelineEntry(BaseModel):
    window: str
    count: int
    avg_score: float | None


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> DashboardMetrics:
    try:
        total_detected = (await db.execute(select(func.count(Opportunity.id)))).scalar_one()

        def count_by(col, val):
            return select(func.count(Opportunity.id)).where(col == val)

        go = (await db.execute(count_by(Opportunity.decision, "go"))).scalar_one()
        pending = (await db.execute(count_by(Opportunity.decision, "pending"))).scalar_one()
        no_go = (await db.execute(count_by(Opportunity.decision, "no_go"))).scalar_one()
        in_crm = (await db.execute(count_by(Opportunity.status, "in_crm"))).scalar_one()

        avg_score_row = await db.execute(
            select(func.avg(Opportunity.score_total)).where(Opportunity.decision == "go")
        )
        avg_score = avg_score_row.scalar_one()

        windows_q = await db.execute(
            select(Opportunity.market_window, func.count(Opportunity.id))
            .where(Opportunity.market_window.isnot(None))
            .group_by(Opportunity.market_window)
        )
        by_window = {row[0]: row[1] for row in windows_q.all()}

        urgency_q = await db.execute(
            select(Opportunity.urgency, func.count(Opportunity.id))
            .where(Opportunity.urgency.isnot(None))
            .group_by(Opportunity.urgency)
        )
        by_urgency = {row[0]: row[1] for row in urgency_q.all()}

        return DashboardMetrics(
            total_detected=total_detected,
            total_go=go,
            total_pending=pending,
            total_no_go=no_go,
            total_in_crm=in_crm,
            avg_score_go=float(avg_score) if avg_score else None,
            by_window=by_window,
            by_urgency=by_urgency,
        )
    except Exception:
        return DashboardMetrics(
            total_detected=0,
            total_go=0,
            total_pending=0,
            total_no_go=0,
            total_in_crm=0,
            avg_score_go=None,
            by_window={},
            by_urgency={},
        )


class SourceStats(BaseModel):
    source_name: str
    total: int
    go_count: int
    pending_count: int
    no_go_count: int
    last_detected: str | None  # ISO datetime
    avg_score: float | None


@router.get("/sources", response_model=list[SourceStats])
async def get_source_stats(db: AsyncSession = Depends(get_db)) -> list[SourceStats]:
    """Stats por fuente para la página Radar.

    Devuelve para cada source_name:
    - total de opps
    - conteo por decisión (go, pending, no_go)
    - última detección
    - score promedio
    """
    try:
        # Agregación SQL por source_name
        q = await db.execute(
            select(
                Opportunity.source_name,
                func.count(Opportunity.id).label("total"),
                func.sum(
                    func.cast(Opportunity.decision == "go", sa.Integer)
                ).label("go_count"),
                func.sum(
                    func.cast(Opportunity.decision == "pending", sa.Integer)
                ).label("pending_count"),
                func.sum(
                    func.cast(Opportunity.decision == "no_go", sa.Integer)
                ).label("no_go_count"),
                func.max(Opportunity.detected_at).label("last_detected"),
                func.avg(Opportunity.score_total).label("avg_score"),
            )
            .where(Opportunity.source_name.isnot(None))
            .group_by(Opportunity.source_name)
            .order_by(func.count(Opportunity.id).desc())
        )

        return [
            SourceStats(
                source_name=row[0] or "unknown",
                total=int(row[1] or 0),
                go_count=int(row[2] or 0),
                pending_count=int(row[3] or 0),
                no_go_count=int(row[4] or 0),
                last_detected=row[5].isoformat() if row[5] else None,
                avg_score=float(row[6]) if row[6] is not None else None,
            )
            for row in q.all()
        ]
    except Exception:
        return []


@router.get("/pipeline", response_model=list[PipelineEntry])
async def get_pipeline(db: AsyncSession = Depends(get_db)) -> list[PipelineEntry]:
    try:
        q = await db.execute(
            select(
                Opportunity.market_window,
                func.count(Opportunity.id),
                func.avg(Opportunity.score_total),
            )
            .where(Opportunity.decision == "go")
            .where(Opportunity.market_window.isnot(None))
            .group_by(Opportunity.market_window)
        )
        return [
            PipelineEntry(
                window=row[0],
                count=row[1],
                avg_score=float(row[2]) if row[2] else None,
            )
            for row in q.all()
        ]
    except Exception:
        return []
