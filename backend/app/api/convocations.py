import csv
import io
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.models.convocation import Convocation

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
    """List convocations with filtering and pagination"""
    query = select(Convocation)

    if type_:
        query = query.where(Convocation.type == type_)
    if verified_only:
        query = query.where(Convocation.verified == True)
    if days_to_deadline:
        deadline = date.today() + timedelta(days=days_to_deadline)
        query = query.where(Convocation.deadline <= deadline)
    if source:
        query = query.where(Convocation.source_name.like(f"%{source}%"))

    # Get count
    count_result = await db.execute(select(func.count(Convocation.id)).select_from(Convocation))
    total = count_result.scalar() or 0

    # Paginate
    query = query.order_by(Convocation.deadline.asc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    convs = result.scalars().all()

    items = [
        {
            "id": str(conv.id),
            "title": conv.title,
            "objective": conv.objective,
            "type": conv.type,
            "deadline": conv.deadline.isoformat(),
            "open_date": conv.open_date.isoformat(),
            "url_convocation": conv.url_convocation,
            "amount_min_cop": conv.amount_min_cop,
            "amount_max_cop": conv.amount_max_cop,
            "url_tor": conv.url_tor,
            "url_form": conv.url_form,
            "organization_website": conv.organization_website,
            "source_name": conv.source_name,
            "verified": conv.verified,
            "data_completeness": conv.data_completeness,
        }
        for conv in convs
    ]

    return {"items": items, "total": total, "page": page, "size": size}

@router.get("/export")
async def export_convocations(
    type_: Optional[str] = Query(None, alias="type"),
    verified_only: bool = False,
    days_to_deadline: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Export convocations as CSV"""

    query = select(Convocation)
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
