"""API endpoints for Global Organizations (GLOBAL module) with full metadata and CSV export."""
import csv
import io
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.contact import Contact
from app.models.funder import Funder

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=dict)
async def list_global_organizations(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    country: Optional[str] = None,
    org_type: Optional[str] = None,
    strategic_obj: Optional[str] = None,
    invests_colombia: Optional[bool] = None,
    invests_latam: Optional[bool] = None,
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List global organizations with full metadata and key contacts count.

    Query params:
    - country: Filter by country
    - org_type: foundation|multilateral|government|corporate
    - strategic_obj: capital|exportacion_modelo|red
    - invests_colombia: Filter by Colombia investment
    - invests_latam: Filter by Latam investment
    - verified_only: Include only organizations with verified data
    """
    query = select(Funder)
    filters = []

    # Apply filters
    if country:
        filters.append(Funder.country == country)
    if org_type:
        filters.append(Funder.org_type == org_type)
    if strategic_obj:
        filters.append(Funder.strategic_obj == strategic_obj)
    if invests_colombia is not None:
        filters.append(Funder.invests_colombia == invests_colombia)
    if invests_latam is not None:
        filters.append(Funder.invests_latam == invests_latam)
    if verified_only:
        filters.append(Funder.verified_data == True)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count(Funder.id))
    if filters:
        count_query = count_query.where(and_(*filters))

    total = (await db.execute(count_query)).scalar() or 0

    # Pagination and ordering
    query = query.offset((page - 1) * size).limit(size).order_by(Funder.name)
    result = await db.execute(query)
    organizations = result.scalars().all()

    # Build response with contact counts
    items = []
    for org in organizations:
        # Count contacts for this organization
        contact_query = select(func.count(Contact.id)).where(Contact.funder_id == org.id)
        contact_count = (await db.execute(contact_query)).scalar() or 0

        items.append({
            "id": str(org.id),
            "name": org.name,
            "country": org.country,
            "org_type": org.org_type,
            "website": org.website,
            "linkedin_url": org.linkedin_url,
            "focus_sectors": org.focus_sectors or [],
            "strategic_obj": org.strategic_obj,
            "aeiotu_role": org.aeiotu_role,
            "invests_colombia": org.invests_colombia,
            "invests_latam": org.invests_latam,
            "general_objective": (org.general_objective[:200] if org.general_objective else None),
            "has_history": org.has_history,
            "verified_data": org.verified_data,
            "key_contacts_count": contact_count,
            "ticket_min_usd": org.ticket_min_usd,
            "ticket_max_usd": org.ticket_max_usd,
            "min_grant_cop": org.min_grant_cop,
            "max_grant_cop": org.max_grant_cop,
        })

    logger.info(
        "Listed global organizations",
        total=total,
        page=page,
        size=size,
        filters_applied=len(filters) > 0,
    )

    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/export", response_model=None)
async def export_global_organizations(
    country: Optional[str] = None,
    org_type: Optional[str] = None,
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Export global organizations as CSV for CRM import.

    Query params:
    - country: Filter by country
    - org_type: Filter by organization type
    - verified_only: Include only verified organizations
    """
    query = select(Funder)
    filters = []

    if country:
        filters.append(Funder.country == country)
    if org_type:
        filters.append(Funder.org_type == org_type)
    if verified_only:
        filters.append(Funder.verified_data == True)

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(Funder.name)
    result = await db.execute(query)
    organizations = result.scalars().all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write UTF-8 BOM for Excel compatibility
    output.write("﻿")

    # Headers
    headers = [
        "id",
        "name",
        "country",
        "org_type",
        "website",
        "linkedin_url",
        "focus_sectors",
        "strategic_objective",
        "aeiotu_role",
        "invests_colombia",
        "invests_latam",
        "general_objective",
        "has_history",
        "verified_data",
        "ticket_min_usd",
        "ticket_max_usd",
        "min_grant_cop",
        "max_grant_cop",
    ]
    writer.writerow(headers)

    # Write rows
    for org in organizations:
        writer.writerow([
            str(org.id),
            org.name or "",
            org.country or "",
            org.org_type or "",
            org.website or "",
            org.linkedin_url or "",
            ";".join(org.focus_sectors) if org.focus_sectors else "",
            org.strategic_obj or "",
            org.aeiotu_role or "",
            "Yes" if org.invests_colombia else "No",
            "Yes" if org.invests_latam else "No",
            (org.general_objective or "")[:500],
            "Yes" if org.has_history else "No",
            "Yes" if org.verified_data else "No",
            org.ticket_min_usd or "",
            org.ticket_max_usd or "",
            org.min_grant_cop or "",
            org.max_grant_cop or "",
        ])

    # Get the CSV content
    csv_content = output.getvalue()

    logger.info(
        "Exported global organizations",
        total=len(organizations),
        filters_applied=len(filters) > 0,
    )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=global_organizations.csv"}
    )
