"""API endpoints for Organizations (Funders)."""
import base64
import csv
import io
from datetime import datetime, timezone
from typing import Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.funder import Funder
from app.schemas.analysis import AnalysisResult
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services.analysis_service import AnalysisService

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=dict)
async def list_organizations(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    country: Optional[str] = None,
    invests_colombia: Optional[bool] = None,
    invests_latam: Optional[bool] = None,
    access_type: Optional[str] = None,
    search: Optional[str] = None,
) -> dict:
    """List organizations with optional filters.

    Query params:
    - country: Filter by country
    - invests_colombia: Filter by Colombia investment
    - invests_latam: Filter by Latam investment
    - access_type: convocatoria | mixto | relacional | invitacion
    - search: Search by name, website, or objective

    NOTE: Currently returns mock data for development. Connects to Supabase when available.
    """
    # Import extended mock data with global organizations
    from app.mock_data import MOCK_ORGANIZATIONS_EXTENDED
    MOCK_ORGANIZATIONS = MOCK_ORGANIZATIONS_EXTENDED

    # Filter mock data
    filtered = MOCK_ORGANIZATIONS

    if country:
        filtered = [o for o in filtered if o.get("country", "").lower() == country.lower()]
    if invests_colombia is not None:
        filtered = [o for o in filtered if o.get("invests_colombia") == invests_colombia]
    if invests_latam is not None:
        filtered = [o for o in filtered if o.get("invests_latam") == invests_latam]
    if access_type:
        filtered = [o for o in filtered if o.get("access_type") == access_type]
    if search:
        search_lower = search.lower()
        filtered = [o for o in filtered if search_lower in o.get("name", "").lower() or search_lower in o.get("general_objective", "").lower()]

    total = len(filtered)
    start = (page - 1) * size
    end = start + size
    paginated = filtered[start:end]

    return {
        "items": paginated,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/analyze-strategy/{org_id}", response_model=dict)
async def analyze_organization(
    org_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Generate strategic analysis for an organization using Claude API.

    Returns:
    {
      "org_id": "uuid",
      "analysis": {
        "capital": { "text": "...", "conclusion": "Alto|Medio|Bajo" },
        "model_export": { "text": "...", "conclusion": "SÍ|NO" },
        "network": { "text": "...", "conclusion": "SÍ (Alto|Medio|Bajo)|NO" },
        "colombia": { "text": "...", "conclusion": "Sí|No" },
        "latam": { "text": "...", "conclusion": "Prioridad|Secundaria|Marginal" },
        "primary_role": "capital|exportacion|posicionamiento"
      },
      "generated_at": "2026-06-05T12:34:56Z"
    }
    """
    # Fetch organization
    stmt = select(Funder).where(Funder.id == org_id)
    result = await session.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        # Generate analysis
        service = AnalysisService()
        analysis_result: AnalysisResult = service.analyze_organization(org)

        logger.info("Organization analysis generated", org_id=org_id, org_name=org.name)

        return {
            "org_id": str(org.id),
            "analysis": analysis_result.model_dump(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to generate analysis", org_id=org_id, error=str(e))
        raise HTTPException(status_code=500, detail="Could not generate analysis")


@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization(
    org_id: str,
    session: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    """Get organization detail."""
    stmt = select(Funder).where(Funder.id == org_id)
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


@router.get("/export/csv", response_model=dict)
async def export_organizations_csv(
    session: AsyncSession = Depends(get_db),
    country: Optional[str] = None,
    invests_colombia: Optional[bool] = None,
) -> dict:
    """Export organizations to CSV."""
    filters = []

    if country:
        filters.append(Funder.country == country)
    if invests_colombia is not None:
        filters.append(Funder.invests_colombia == invests_colombia)

    stmt = select(Funder)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(Funder.name)

    result = await session.execute(stmt)
    orgs = result.scalars().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    headers = [
        "ID", "Nombre", "Tipo", "Pais",
        "Website", "LinkedIn",
        "Tipos de Acceso", "Objetivo Estrategico",
        "Invierte Colombia", "Invierte Latam",
        "Rol aeioTU", "Objetivo General",
        "Monto Min USD", "Monto Max USD",
        "Monto Min COP", "Monto Max COP",
        "Datos Verificados", "Historial aeioTU",
    ]
    writer.writerow(headers)

    # Rows
    for org in orgs:
        writer.writerow([
            str(org.id),
            org.name,
            org.org_type or "",
            org.country or "",
            org.website or "",
            org.linkedin_url or "",
            org.access_type or "",
            org.strategic_obj or "",
            "Si" if org.invests_colombia else "No",
            "Si" if org.invests_latam else "No",
            org.aeiotu_role or "",
            org.general_objective or "",
            org.ticket_min_usd or "",
            org.ticket_max_usd or "",
            f"${org.min_grant_cop:,}" if org.min_grant_cop else "",
            f"${org.max_grant_cop:,}" if org.max_grant_cop else "",
            "Si" if org.verified_data else "No",
            "Si" if org.has_history else "No",
        ])

    csv_content = output.getvalue()
    csv_b64 = base64.b64encode(csv_content.encode()).decode()

    return {
        "filename": f"organizations_{datetime.now(timezone.utc).isoformat()}.csv",
        "content_base64": csv_b64,
        "total_rows": len(orgs),
    }
