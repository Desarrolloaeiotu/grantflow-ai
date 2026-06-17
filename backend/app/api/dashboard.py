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
    from app.mock_data import MOCK_OPPORTUNITIES

    # Calculate metrics from mock data
    opps = MOCK_OPPORTUNITIES

    total_detected = len(opps)
    go = len([o for o in opps if o.get("decision") == "go"])
    pending = len([o for o in opps if o.get("decision") == "pending"])
    no_go = len([o for o in opps if o.get("decision") == "no_go"])
    in_crm = len([o for o in opps if o.get("status") == "in_crm"])

    go_scores = [o.get("score_total", 0) for o in opps if o.get("decision") == "go"]
    avg_score = sum(go_scores) / len(go_scores) if go_scores else None

    # Group by window
    by_window = {}
    for o in opps:
        window = o.get("market_window", "unknown")
        by_window[window] = by_window.get(window, 0) + 1

    # Group by urgency
    by_urgency = {}
    for o in opps:
        urgency = o.get("urgency", "unknown")
        by_urgency[urgency] = by_urgency.get(urgency, 0) + 1

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
