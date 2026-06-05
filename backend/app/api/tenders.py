"""API endpoints for tenders/convocations (Global and Nacional modules)."""
import base64
import csv
import io
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.funder import Funder
from app.models.opportunity import Opportunity
from app.schemas.tender import TenderCreate, TenderListResponse, TenderRead

logger = structlog.get_logger()
router = APIRouter()

# Monto mínimo por ventana
TENDER_MIN_AMOUNTS = {
    "global": 100_000_000,  # COP $100M (~USD $24K)
    "nacional": 50_000_000,  # COP $50M (~USD $12K)
}


@router.get("", response_model=TenderListResponse)
async def list_tenders(
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    region: Optional[str] = Query(None),  # global | nacional | None (both)
    amount_min: Optional[int] = None,
    decision: Optional[str] = None,
    tender_type: Optional[str] = None,
    days_to_deadline: Optional[int] = None,
) -> TenderListResponse:
    """List tenders with optional region filter.

    Query params:
    - region: 'global' (≥100M COP) | 'nacional' (≥50M COP) | None (both with ≥50M minimum)
    - amount_min: Monto mínimo en COP (override región)
    - decision: go | no_go | pending
    - tender_type: grant | premio | evento | curso
    - days_to_deadline: Filtrar por días hasta cierre
    """
    filters = []

    # Determine minimum amount based on region
    if amount_min:
        min_amount = amount_min
    elif region == "global":
        min_amount = TENDER_MIN_AMOUNTS["global"]
    elif region == "nacional":
        min_amount = TENDER_MIN_AMOUNTS["nacional"]
    else:
        min_amount = TENDER_MIN_AMOUNTS["nacional"]  # Default to nacional minimum

    # Amount filter
    filters.append(or_(
        Opportunity.amount_max_cop >= min_amount,
        Opportunity.amount_max_cop.is_(None),  # Include if amount not specified
    ))

    # Region filter
    nacional_sources = ["nacional_colombia", "secop", "manual_nacional"]
    if region == "nacional":
        # Include SECOP, nacional_colombia, and manual_nacional in nacional view
        filters.append(Opportunity.source_name.in_(nacional_sources))
    elif region == "global":
        # Exclude nacional sources from global view
        filters.append(
            and_(
                Opportunity.source_name != nacional_sources[0],
                Opportunity.source_name != nacional_sources[1],
                Opportunity.source_name != nacional_sources[2],
            )
        )

    # Additional filters
    if decision:
        filters.append(Opportunity.decision == decision)
    if tender_type:
        filters.append(Opportunity.tender_type == tender_type)
    if days_to_deadline:
        from datetime import datetime, timedelta, timezone
        cutoff_date = datetime.now(timezone.utc).date() + timedelta(days=days_to_deadline)
        filters.append(Opportunity.deadline <= cutoff_date)

    # Get total count
    count_stmt = select(func.count(Opportunity.id))
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total = await session.scalar(count_stmt)

    # Get paginated results with funder
    stmt = select(Opportunity)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = (
        stmt.options(selectinload(Opportunity.funder))
        .offset((page - 1) * size)
        .limit(size)
        .order_by(Opportunity.deadline.asc())  # Upcoming deadlines first
    )

    result = await session.execute(stmt)
    tenders = result.scalars().unique().all()

    # Map to TenderRead with funder_name
    items = []
    for tender in tenders:
        tender_data = TenderRead.model_validate(tender)
        if tender.funder:
            tender_data.funder_name = tender.funder.name
        items.append(tender_data)

    return TenderListResponse(
        items=items,
        total=total or 0,
        page=page,
        size=size,
    )


@router.get("/{tender_id}", response_model=TenderRead)
async def get_tender(
    tender_id: str,
    session: AsyncSession = Depends(get_db),
) -> TenderRead:
    """Get tender detail."""
    stmt = select(Opportunity).where(Opportunity.id == tender_id).options(selectinload(Opportunity.funder))
    result = await session.execute(stmt)
    tender = result.scalar_one_or_none()

    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    tender_data = TenderRead.model_validate(tender)
    if tender.funder:
        tender_data.funder_name = tender.funder.name
    return tender_data


@router.post("", response_model=TenderRead, status_code=201)
async def create_tender(
    tender: TenderCreate,
    session: AsyncSession = Depends(get_db),
) -> TenderRead:
    """Create a new tender manually."""
    db_tender = Opportunity(**tender.model_dump())
    session.add(db_tender)
    await session.commit()
    await session.refresh(db_tender)

    logger.info("Created tender", tender_id=str(db_tender.id), title=db_tender.title)

    tender_data = TenderRead.model_validate(db_tender)
    return tender_data


@router.get("/export/csv")
async def export_tenders_csv(
    session: AsyncSession = Depends(get_db),
    region: Optional[str] = Query(None),  # global | nacional
    decision: Optional[str] = None,
) -> dict:
    """Export tenders to CSV.

    Returns CSV content as base64-encoded string.
    """
    filters = []

    # Determine minimum amount based on region
    if region == "global":
        min_amount = TENDER_MIN_AMOUNTS["global"]
        # Exclude nacional sources from global
        filters.append(and_(
            Opportunity.source_name != "nacional_colombia",
            Opportunity.source_name != "secop",
            Opportunity.source_name != "manual_nacional",
        ))
    elif region == "nacional":
        min_amount = TENDER_MIN_AMOUNTS["nacional"]
        # Include nacional, SECOP, and manual_nacional
        filters.append(or_(
            Opportunity.source_name == "nacional_colombia",
            Opportunity.source_name == "secop",
            Opportunity.source_name == "manual_nacional",
        ))
    else:
        min_amount = TENDER_MIN_AMOUNTS["nacional"]

    filters.append(or_(
        Opportunity.amount_max_cop >= min_amount,
        Opportunity.amount_max_cop.is_(None),
    ))

    if decision:
        filters.append(Opportunity.decision == decision)

    stmt = select(Opportunity)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.options(selectinload(Opportunity.funder)).order_by(Opportunity.deadline.asc())

    result = await session.execute(stmt)
    tenders = result.scalars().unique().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    headers = [
        "ID", "Título", "Tipo", "Descripción Resumida",
        "Financiador", "Monto Mín (COP)", "Monto Máx (COP)",
        "Fecha Apertura", "Cierre", "Días para Cierre",
        "URL RFP", "URL ToR", "URL Formulario",
        "Decisión", "Score", "Estado", "Ventana",
    ]
    writer.writerow(headers)

    # Rows
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()

    for tender in tenders:
        days_to_deadline = ""
        if tender.deadline:
            delta = (tender.deadline - today).days
            days_to_deadline = str(delta)

        writer.writerow([
            str(tender.id),
            tender.title,
            tender.tender_type or "",
            (tender.description or "")[:100],
            tender.funder.name if tender.funder else "",
            f"${tender.amount_min_cop:,}" if tender.amount_min_cop else "",
            f"${tender.amount_max_cop:,}" if tender.amount_max_cop else "",
            tender.open_date or "",
            tender.deadline or "",
            days_to_deadline,
            tender.url_rfp or "",
            tender.url_tor or "",
            tender.url_form or "",
            tender.decision or "",
            tender.score_total or "",
            tender.status,
            tender.market_window or "",
        ])

    csv_content = output.getvalue()
    csv_b64 = base64.b64encode(csv_content.encode()).decode()

    return {
        "filename": f"tenders_{region or 'all'}.csv",
        "content_base64": csv_b64,
    }
