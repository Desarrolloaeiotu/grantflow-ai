import uuid
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityList, OpportunityRead, OpportunityUpdate

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=OpportunityList)
async def list_opportunities(
    window: str | None = Query(None),
    decision: Literal["go", "no_go", "pending"] | None = Query(None),
    urgency: Literal["high", "medium", "low"] | None = Query(None),
    score_min: int | None = Query(None, ge=0, le=10),
    days_to_deadline: int | None = Query(None, description="Solo opps con deadline ≤ N días"),
    days_to_contact: int | None = Query(None, description="Solo opps con target_contact_date ≤ N días"),
    source: str | None = Query(None),
    status: str | None = Query(None),
    q: str | None = Query(None, description="Búsqueda full-text en título y descripción"),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> OpportunityList:
    from datetime import date, timedelta

    query = select(Opportunity)

    if window:
        query = query.where(Opportunity.market_window == window)
    if decision:
        query = query.where(Opportunity.decision == decision)
    if urgency:
        query = query.where(Opportunity.urgency == urgency)
    if score_min is not None:
        query = query.where(Opportunity.score_total >= score_min)
    if source:
        query = query.where(Opportunity.source_name == source)
    if status:
        query = query.where(Opportunity.status == status)
    if days_to_deadline is not None:
        cutoff = date.today() + timedelta(days=days_to_deadline)
        query = query.where(Opportunity.deadline.isnot(None)).where(
            Opportunity.deadline <= cutoff
        )
    if days_to_contact is not None:
        cutoff = date.today() + timedelta(days=days_to_contact)
        query = query.where(Opportunity.target_contact_date.isnot(None)).where(
            Opportunity.target_contact_date <= cutoff
        )
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            func.lower(Opportunity.title).like(like)
            | func.lower(Opportunity.description).like(like)
        )

    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar_one()

    query = query.order_by(
        Opportunity.score_total.desc().nullslast(), Opportunity.detected_at.desc()
    )
    query = query.offset((page - 1) * size).limit(size)

    rows = (await db.execute(query)).scalars().all()
    return OpportunityList(items=list(rows), total=total, page=page, size=size)


def _format_cop(amount: int | None) -> str:
    """Formatea un monto COP a 'COP $XM' o 'COP $X.XB'."""
    if amount is None:
        return ""
    if amount >= 1_000_000_000:
        return f"COP ${amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"COP ${round(amount / 1_000_000)}M"
    return f"COP ${amount:,}"


def _safe_get_score_details(score_details: dict | None, key: str, default: str = "") -> str:
    if not score_details:
        return default
    val = score_details.get(key, default)
    return str(val) if val is not None else default


@router.get("/export")
async def export_opportunities(
    decision: str | None = Query("go", description="Filtrar por decisión. Vacío = todas."),
    verified_only: bool = Query(
        False, description="Solo opps con al menos un email verificado (org o CEO)"
    ),
    min_score: int | None = Query(None, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Exporta oportunidades a CSV para import al CRM.

    Incluye TODOS los campos relevantes:
    - Datos de la oportunidad (título, score, decisión, urgencia, montos)
    - Datos de contacto organización (website, email + verificado)
    - Datos de contacto CEO (nombre, cargo, email + verificado, LinkedIn)
    - Justificación del scoring LLM
    """
    import csv
    import io
    from sqlalchemy.orm import joinedload

    from app.models.funder import Funder

    # Query con join al funder para traer el nombre
    q = select(Opportunity).options(joinedload(Opportunity.funder))
    if decision:
        q = q.where(Opportunity.decision == decision)
    if min_score is not None:
        q = q.where(Opportunity.score_total >= min_score)
    q = q.order_by(Opportunity.score_total.desc().nullslast(), Opportunity.deadline.asc().nullslast())

    rows = (await db.execute(q)).unique().scalars().all()

    # Filtro post-query para verified_only (más simple que SQL)
    if verified_only:
        rows = [
            r for r in rows
            if r.org_email_verified or r.ceo_email_verified
        ]

    output = io.StringIO()
    # BOM para que Excel lo abra como UTF-8
    output.write("﻿")
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header con TODOS los campos para el CRM
    writer.writerow([
        # Identificación
        "id",
        "title",
        "description",
        # Clasificación aeioTU
        "decision",
        "score_total",
        "urgency",
        "market_window",
        "capital_type",
        # Financiador
        "funder_name",
        "source_name",
        # Montos
        "amount_min_cop",
        "amount_max_cop",
        "amount_min_formatted",
        "amount_max_formatted",
        # Plazo
        "deadline",
        "detected_at",
        # URLs
        "url_rfp",
        "url_source",
        # Organización: contacto
        "org_website",
        "org_email",
        "org_email_verified",
        # CEO: contacto
        "ceo_name",
        "ceo_title",
        "ceo_email",
        "ceo_email_verified",
        "ceo_linkedin_url",
        # Scoring breakdown
        "c1_alineacion",
        "c2_modelo",
        "c3_ticket",
        "c4_viabilidad",
        "c5_relacional",
        "llm_justification",
        "llm_confidence",
        # Estado interno
        "status",
    ])

    for opp in rows:
        funder_name = opp.funder.name if opp.funder else ""
        sd = opp.score_details or {}
        writer.writerow([
            str(opp.id),
            opp.title or "",
            (opp.description or "").replace("\n", " ").replace("\r", " ")[:1500],
            opp.decision or "",
            opp.score_total if opp.score_total is not None else "",
            opp.urgency or "",
            opp.market_window or "",
            opp.capital_type or "",
            funder_name,
            opp.source_name or "",
            opp.amount_min_cop if opp.amount_min_cop is not None else "",
            opp.amount_max_cop if opp.amount_max_cop is not None else "",
            _format_cop(opp.amount_min_cop),
            _format_cop(opp.amount_max_cop),
            opp.deadline.isoformat() if opp.deadline else "",
            opp.detected_at.isoformat() if opp.detected_at else "",
            opp.url_rfp or "",
            opp.url_source or "",
            opp.org_website or "",
            opp.org_email or "",
            "TRUE" if opp.org_email_verified else "FALSE",
            opp.ceo_name or "",
            opp.ceo_title or "",
            opp.ceo_email or "",
            "TRUE" if opp.ceo_email_verified else "FALSE",
            opp.ceo_linkedin_url or "",
            _safe_get_score_details(sd, "c1"),
            _safe_get_score_details(sd, "c2"),
            _safe_get_score_details(sd, "c3"),
            _safe_get_score_details(sd, "c4"),
            _safe_get_score_details(sd, "c5"),
            (sd.get("llm_justification") or "").replace("\n", " ").replace("\r", " "),
            sd.get("confidence") or "",
            opp.status or "",
        ])

    output.seek(0)
    filename = f"grantflow_opportunities_{decision or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> OpportunityRead:
    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return OpportunityRead.model_validate(opp)


@router.patch("/{opportunity_id}/status", response_model=OpportunityRead)
async def update_opportunity_status(
    opportunity_id: uuid.UUID,
    body: OpportunityUpdate,
    db: AsyncSession = Depends(get_db),
) -> OpportunityRead:
    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    if body.status is not None:
        opp.status = body.status
    if body.decision is not None:
        opp.decision = body.decision
    if body.urgency is not None:
        opp.urgency = body.urgency

    await db.commit()
    await db.refresh(opp)
    logger.info("Opportunity status updated", opportunity_id=str(opportunity_id), status=opp.status)
    return OpportunityRead.model_validate(opp)
