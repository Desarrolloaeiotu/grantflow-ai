"""API endpoints for organizations (Module Global)."""
import io
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.contact import Contact
from app.models.funder import Funder
from app.schemas.organization import OrganizationCreate, OrganizationList, OrganizationRead

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=OrganizationList)
async def list_organizations(
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    org_type: Optional[str] = None,
    country: Optional[str] = None,
    invests_colombia: Optional[bool] = None,
    invests_latam: Optional[bool] = None,
    access_type: Optional[str] = None,
) -> OrganizationList:
    """List organizations with filters.

    Query params:
    - org_type: Filantropía, ONG, Multilateral, Público, Privado, Banco, Cooperación, Tercer sector
    - country: Country name or code
    - invests_colombia: True/False to filter by Colombia investment
    - invests_latam: True/False to filter by LatAm investment
    - access_type: convocatoria, mixto, relacional, invitacion
    """
    filters = []

    if org_type:
        filters.append(Funder.org_type == org_type)
    if country:
        filters.append(Funder.country.ilike(f"%{country}%"))
    if invests_colombia is not None:
        filters.append(Funder.invests_colombia == invests_colombia)
    if invests_latam is not None:
        filters.append(Funder.invests_latam == invests_latam)
    if access_type:
        filters.append(Funder.access_type == access_type)

    # Get total count
    count_stmt = select(func.count(Funder.id))
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total = await session.scalar(count_stmt)

    # Get paginated results with contacts
    stmt = select(Funder)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = (
        stmt.options(selectinload(Funder.contacts))
        .offset((page - 1) * size)
        .limit(size)
        .order_by(Funder.created_at.desc())
    )

    result = await session.execute(stmt)
    organizations = result.scalars().unique().all()

    return OrganizationList(
        items=[OrganizationRead.model_validate(o) for o in organizations],
        total=total or 0,
        page=page,
        size=size,
    )


@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization(
    org_id: str,
    session: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    """Get organization detail with related contacts."""
    stmt = select(Funder).where(Funder.id == org_id).options(selectinload(Funder.contacts))
    result = await session.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationRead.model_validate(org)


@router.post("", response_model=OrganizationRead, status_code=201)
async def create_organization(
    org: OrganizationCreate,
    session: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    """Create a new organization manually."""
    db_org = Funder(**org.model_dump())
    session.add(db_org)
    await session.commit()
    await session.refresh(db_org)

    logger.info("Created organization", org_id=str(db_org.id), name=db_org.name)

    return OrganizationRead.model_validate(db_org)


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_organization(
    org_id: str,
    org_update: OrganizationCreate,
    session: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    """Update organization fields."""
    stmt = select(Funder).where(Funder.id == org_id)
    result = await session.execute(stmt)
    db_org = result.scalar_one_or_none()

    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Update only provided fields
    for field, value in org_update.model_dump(exclude_unset=True).items():
        setattr(db_org, field, value)

    await session.commit()
    await session.refresh(db_org)

    logger.info("Updated organization", org_id=str(db_org.id))

    return OrganizationRead.model_validate(db_org)


@router.post("/{org_id}/enrich")
async def enrich_organization_contacts(
    org_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Enrich organization with contacts from Apollo.io.

    Searches Apollo for people at the organization and creates Contact records
    with role_category inferred from title keywords.

    Returns:
        {
            "status": "success"|"error",
            "org_id": str,
            "org_name": str,
            "contacts_found": int,
            "contacts": [{"name": "...", "email": "...", "role_category": "..."}]
        }
    """
    from app.services.apollo_service import apollo

    # Get organization
    stmt = select(Funder).where(Funder.id == org_id)
    result = await session.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    log = logger.bind(org_id=org_id, org_name=org.name)
    log.info("Starting Apollo enrichment for organization")

    try:
        # Search Apollo for contacts
        people = await apollo.search_people(
            company_name=org.name,
            limit=15,  # Get top 15 contacts
        )

        if not people:
            return {
                "status": "success",
                "org_id": str(org.id),
                "org_name": org.name,
                "contacts_found": 0,
                "contacts": [],
            }

        # Create Contact records with role_category inference
        from app.models.contact import Contact

        contacts_created = []
        for person in people:
            role_category = _infer_role_category(person)

            contact = Contact(
                full_name=person.get("name", "Unknown"),
                title=person.get("title"),
                email=person.get("email"),
                linkedin_url=person.get("linkedin_url"),
                funder_id=org.id,
                source="apollo",
                role_category=role_category,
                aeiotu_connection=False,
            )
            session.add(contact)
            contacts_created.append({
                "name": contact.full_name,
                "email": contact.email,
                "title": contact.title,
                "role_category": contact.role_category,
            })

        await session.commit()

        log.info(
            "Enrichment complete",
            contacts_created=len(contacts_created),
        )

        return {
            "status": "success",
            "org_id": str(org.id),
            "org_name": org.name,
            "contacts_found": len(contacts_created),
            "contacts": contacts_created,
        }

    except Exception as exc:
        log.error("Apollo enrichment failed", error=str(exc))
        return {
            "status": "error",
            "org_id": str(org.id),
            "org_name": org.name,
            "contacts_found": 0,
            "message": str(exc),
        }


def _infer_role_category(person: dict) -> str:
    """Infer role_category from person title using keywords.

    Returns: 'partnerships' | 'grants' | 'cooperation' | 'innovation' | 'development'
    """
    title = (person.get("title") or "").lower()

    role_keywords = {
        "partnerships": [
            "partnership", "alliance", "relationship", "strategic", "business development",
            "director of partnerships", "manager partnerships",
        ],
        "grants": [
            "grant", "funding", "proposal", "funder", "grants manager",
            "director of grants", "head of funding",
        ],
        "cooperation": [
            "cooperation", "cooperation officer", "cooperation specialist",
            "international", "bilateral", "multilateral",
        ],
        "innovation": [
            "innovation", "innovation officer", "innovation manager",
            "r&d", "research", "development", "technology",
        ],
        "development": [
            "development", "program", "community", "social", "csr",
            "director of development", "development officer",
        ],
    }

    for category, keywords in role_keywords.items():
        if any(kw in title for kw in keywords):
            return category

    # Default to 'development' if no match
    return "development"


@router.get("/export/csv")
async def export_organizations_csv(
    session: AsyncSession = Depends(get_db),
    org_type: Optional[str] = None,
    country: Optional[str] = None,
) -> dict:
    """Export organizations to CSV.

    Returns CSV content as base64-encoded string.
    """
    import csv
    import base64

    filters = []
    if org_type:
        filters.append(Funder.org_type == org_type)
    if country:
        filters.append(Funder.country.ilike(f"%{country}%"))

    stmt = select(Funder)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(Funder.created_at.desc())

    result = await session.execute(stmt)
    organizations = result.scalars().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    headers = [
        "ID", "Nombre", "Tipo", "País", "Sitio Web",
        "Acceso", "Objetivo Estratégico", "Invierte Colombia", "Invierte LatAm",
        "Rol aeioTU", "Objetivo General", "Historial", "Rango Ticket (USD)",
    ]
    writer.writerow(headers)

    # Rows
    for org in organizations:
        writer.writerow([
            str(org.id),
            org.name,
            org.org_type or "",
            org.country or "",
            org.website or "",
            org.access_type or "",
            org.strategic_obj or "",
            "Sí" if org.invests_colombia else "No",
            "Sí" if org.invests_latam else "No",
            org.aeiotu_role or "",
            org.general_objective or "",
            "Sí" if org.has_history else "No",
            f"${org.ticket_min_usd:,} - ${org.ticket_max_usd:,}" if org.ticket_min_usd and org.ticket_max_usd else "",
        ])

    csv_content = output.getvalue()
    csv_b64 = base64.b64encode(csv_content.encode()).decode()

    return {
        "filename": "organizations.csv",
        "content_base64": csv_b64,
    }
