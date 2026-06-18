import uuid
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.models.funder import Funder
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityList, OpportunityRead, OpportunityUpdate

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=dict)
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
    authorization: str | None = Query(None, alias="Authorization"),
    # _auth: None = Depends(require_api_key),  # DISABLED for development
) -> dict:
    from datetime import date, timedelta

    # Build query from database (not mock)
    from sqlalchemy.orm import joinedload
    query = select(Opportunity).options(joinedload(Opportunity.funder))

    # Apply filters
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
    if q:
        q_lower = q.lower()
        query = query.where(
            (Opportunity.title.ilike(f"%{q_lower}%")) |
            (Opportunity.description.ilike(f"%{q_lower}%"))
        )

    # Get total count
    count_query = select(func.count(Opportunity.id)).select_from(Opportunity)
    if window:
        count_query = count_query.where(Opportunity.market_window == window)
    if decision:
        count_query = count_query.where(Opportunity.decision == decision)
    if urgency:
        count_query = count_query.where(Opportunity.urgency == urgency)
    if score_min is not None:
        count_query = count_query.where(Opportunity.score_total >= score_min)
    if source:
        count_query = count_query.where(Opportunity.source_name == source)
    if status:
        count_query = count_query.where(Opportunity.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    # Pagination
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    opportunities = result.scalars().all()

    # Convert to dict format
    items = [
        {
            "id": str(opp.id),
            "title": opp.title,
            "description": opp.description,
            "funder_id": str(opp.funder_id) if opp.funder_id else None,
            "funder_name": opp.funder.name if opp.funder else None,
            "amount_min_cop": opp.amount_min_cop,
            "amount_max_cop": opp.amount_max_cop,
            "deadline": opp.deadline.isoformat() if opp.deadline else None,
            "url_rfp": opp.url_rfp,
            "url_source": opp.url_source,
            "source_name": opp.source_name,
            "market_window": opp.market_window,
            "capital_type": opp.capital_type,
            "score_total": opp.score_total,
            "decision": opp.decision,
            "urgency": opp.urgency,
            "status": opp.status,
            "detected_at": opp.detected_at.isoformat() if opp.detected_at else None,
        }
        for opp in opportunities
    ]

    return {"items": items, "total": total, "page": page, "size": size}


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
    decision: str | None = Query(None, description="Filtrar por decisión: go|no_go|pending. Vacío = todas."),
    window: str | None = Query(None, description="Ventana de mercado: funding_colombia|funding_global|strategic|latam"),
    urgency: str | None = Query(None, description="Urgencia: high|medium|low"),
    source: str | None = Query(None, description="Fuente: grantsgov|bid|unwomen|nacional_colombia|rss"),
    status: str | None = Query(None, description="Estado: detected|reviewed|in_crm|discarded"),
    verified_only: bool = Query(
        False, description="Solo opps con al menos un email verificado (org o CEO)"
    ),
    min_score: int | None = Query(None, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(require_api_key),
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
    if window:
        q = q.where(Opportunity.market_window == window)
    if urgency:
        q = q.where(Opportunity.urgency == urgency)
    if source:
        q = q.where(Opportunity.source_name == source)
    if status:
        q = q.where(Opportunity.status == status)
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
    from datetime import datetime
    parts = [decision or "all", window or "", urgency or ""]
    suffix = "_".join(p for p in parts if p)
    filename = f"grantflow_{suffix}_{datetime.now().strftime('%Y%m%d')}.csv"
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
    _auth: None = Depends(require_api_key),
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


@router.post("/{opportunity_id}/enrich-contacts")
async def enrich_opportunity_contacts(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Enrich an opportunity with contact info using Apollo.io.

    Verifies CEO and organization emails, and looks up CEO info.
    """
    from datetime import datetime, timezone

    from app.services.apollo_service import apollo

    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    results = {"opportunity_id": str(opportunity_id), "enhancements": []}

    # 1. Verify organization email if it exists
    if opp.org_email and not opp.org_email_verified:
        logger.info("Verifying org email", org_email=opp.org_email)
        org_verify = await apollo.verify_email(opp.org_email)
        if org_verify.get("verified"):
            opp.org_email_verified = True
            opp.org_email_verified_at = datetime.now(timezone.utc)
            results["enhancements"].append("org_email_verified")
            logger.info("Org email verified", org_email=opp.org_email)

    # 2. Verify CEO email if it exists
    if opp.ceo_email and not opp.ceo_email_verified:
        logger.info("Verifying CEO email", ceo_email=opp.ceo_email)
        ceo_verify = await apollo.verify_email(opp.ceo_email, opp.ceo_name)
        if ceo_verify.get("verified"):
            opp.ceo_email_verified = True
            opp.ceo_email_verified_at = datetime.now(timezone.utc)
            results["enhancements"].append("ceo_email_verified")
            logger.info("CEO email verified", ceo_email=opp.ceo_email)

            # Update CEO info from Apollo if available
            if not opp.ceo_name and ceo_verify.get("first_name"):
                first = ceo_verify.get("first_name", "")
                last = ceo_verify.get("last_name", "")
                opp.ceo_name = f"{first} {last}".strip()
                results["enhancements"].append("ceo_name_enriched")

            if not opp.ceo_title and ceo_verify.get("title"):
                opp.ceo_title = ceo_verify.get("title")
                results["enhancements"].append("ceo_title_enriched")

            if not opp.ceo_linkedin_url and ceo_verify.get("linkedin_url"):
                opp.ceo_linkedin_url = ceo_verify.get("linkedin_url")
                results["enhancements"].append("ceo_linkedin_enriched")

    # 3. Search for CEO if we don't have email but have organization
    if not opp.ceo_email and opp.source_name and not opp.ceo_name:
        # Try searching by organization name
        org_name = opp.source_name
        if opp.funder_id:
            funder = await db.get(Funder, opp.funder_id)
            if funder:
                org_name = funder.name

        logger.info("Searching for CEO", organization=org_name)
        people = await apollo.search_people(company_name=org_name, limit=1)
        if people:
            person = people[0]
            if person.get("first_name") or person.get("last_name"):
                first = person.get("first_name", "")
                last = person.get("last_name", "")
                opp.ceo_name = f"{first} {last}".strip()
                results["enhancements"].append("ceo_name_found")

            if person.get("email"):
                opp.ceo_email = person["email"]
                if person.get("verified"):
                    opp.ceo_email_verified = True
                    opp.ceo_email_verified_at = datetime.now(timezone.utc)
                results["enhancements"].append("ceo_email_found")

            if person.get("title"):
                opp.ceo_title = person["title"]
                results["enhancements"].append("ceo_title_found")

            if person.get("linkedin_url"):
                opp.ceo_linkedin_url = person["linkedin_url"]
                results["enhancements"].append("ceo_linkedin_found")

    opp.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(opp)

    logger.info("Opportunity enriched", opportunity_id=str(opportunity_id), enhancements=results["enhancements"])
    results["status"] = "success"
    results["enhancements_count"] = len(results["enhancements"])
    return results
