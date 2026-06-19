import csv
import io
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.models.convocation import Convocation
from app.models.opportunity import Opportunity

router = APIRouter()

@router.get("/", response_model=dict)
async def list_convocations(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    type_: Optional[str] = Query(None, alias="type"),
    verified_only: bool = Query(False),
    days_to_deadline: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List convocations with filtering and pagination.

    Pulls from both convocations and opportunities tables.
    By default, only shows active convocations (deadline >= today).
    """
    query = select(Opportunity)

    # MANDATORY: Only show future convocations (deadline >= today)
    query = query.where(Opportunity.deadline >= date.today())

    if source:
        query = query.where(Opportunity.source_name.like(f"%{source}%"))

    # Get count
    count_result = await db.execute(select(func.count(Opportunity.id)).select_from(Opportunity).where(Opportunity.deadline >= date.today()))
    total = count_result.scalar() or 0

    # Paginate
    query = query.order_by(Opportunity.deadline.asc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    opps = result.scalars().all()

    items = [
        {
            "id": str(opp.id),
            "title": opp.title,
            "objective": opp.description or opp.title,
            "type": "grant",  # Default type for opportunities
            "deadline": opp.deadline.isoformat() if opp.deadline else None,
            "open_date": opp.detected_at.date().isoformat() if opp.detected_at else None,
            "url_convocation": opp.url_rfp or opp.url_source,
            "amount_min_cop": opp.amount_min_cop,
            "amount_max_cop": opp.amount_max_cop,
            "url_tor": None,
            "url_form": None,
            "organization_website": opp.org_website,
            "source_name": opp.source_name,
            "verified": False,
            "data_completeness": 60,  # Default for legacy opportunities
        }
        for opp in opps
    ]

    return {"items": items, "total": total, "page": page, "size": size}

@router.get("/export")
async def export_convocations(
    type_: Optional[str] = Query(None, alias="type"),
    verified_only: bool = False,
    days_to_deadline: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Export convocations as CSV. Only includes future convocations (deadline >= today)."""

    query = select(Convocation)

    # MANDATORY: Only export future convocations
    query = query.where(Convocation.deadline >= date.today())

    if type_:
        query = query.where(Convocation.type == type_)
    if verified_only:
        query = query.where(Convocation.verified == True)
    if days_to_deadline:
        deadline = date.today() + timedelta(days=days_to_deadline)
        query = query.where(Convocation.deadline <= deadline)

    query = query.order_by(Convocation.deadline.asc())
    result = await db.execute(query)
    convs = result.scalars().all()

    output = io.StringIO()
    output.write("﻿")  # BOM
    writer = csv.writer(output)

    writer.writerow([
        "id", "title", "objective", "type", "open_date", "deadline",
        "amount_min_cop", "amount_max_cop", "url_convocation", "url_tor", "url_form",
        "organization_website", "source_name", "verified", "data_completeness_%", "detected_at"
    ])

    for conv in convs:
        writer.writerow([
            str(conv.id),
            conv.title,
            conv.objective[:500] if conv.objective else "",
            conv.type,
            conv.open_date.isoformat() if conv.open_date else "",
            conv.deadline.isoformat(),
            conv.amount_min_cop or "",
            conv.amount_max_cop or "",
            conv.url_convocation,
            conv.url_tor or "",
            conv.url_form or "",
            conv.organization_website or "",
            conv.source_name,
            "Yes" if conv.verified else "No",
            conv.data_completeness,
            conv.detected_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=convocations.csv"}
    )
