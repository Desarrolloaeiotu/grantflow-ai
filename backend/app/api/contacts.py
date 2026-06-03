import base64
import csv
import io
import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_api_key
from app.models.contact import Contact
from app.models.funder import Funder
from app.schemas.contact import ContactRead, EmailVerifyRequest, KeyContactRead

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    funder_id: uuid.UUID | None = Query(None),
    role_category: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ContactRead]:
    """List contacts with optional filters.

    Query params:
    - funder_id: Filter by organization ID
    - role_category: partnerships | grants | cooperation | innovation | development
    """
    filters = []
    if funder_id:
        filters.append(Contact.funder_id == funder_id)
    if role_category:
        filters.append(Contact.role_category == role_category)

    q = select(Contact)
    if filters:
        q = q.where(and_(*filters))
    q = q.offset((page - 1) * size).limit(size).order_by(Contact.fetched_at.desc())

    rows = (await db.execute(q)).scalars().all()
    return [ContactRead.model_validate(c) for c in rows]


@router.post("/verify")
async def verify_email(body: EmailVerifyRequest, _auth: None = Depends(require_api_key)) -> dict:
    """Verify an email address using Apollo.io."""
    from app.services.apollo_service import apollo

    result = await apollo.verify_email(body.email, body.name)
    return result


@router.post("/enrich")
async def enrich_contacts(
    funder_id: str | None = Query(None),
    limit: int = Query(10),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Enrich contacts by searching Apollo.io for people at a specific organization.

    Usage:
        POST /api/v1/contacts/enrich?funder_id={uuid}&limit=10

    Returns:
        {
            "status": "success"|"error",
            "funder_id": str,
            "contacts_found": int,
            "contacts": [...]
        }
    """
    from app.services.apollo_service import apollo
    from app.models.funder import Funder

    if not funder_id:
        return {
            "status": "error",
            "message": "funder_id required",
            "contacts_found": 0,
        }

    try:
        funder = (
            await db.execute(
                select(Funder).where(Funder.id == uuid.UUID(funder_id))
            )
        ).scalar_one_or_none()

        if not funder:
            return {
                "status": "error",
                "message": f"Funder {funder_id} not found",
                "contacts_found": 0,
            }

        people = await apollo.search_people(
            company_name=funder.name,
            limit=limit,
        )

        return {
            "status": "success",
            "funder_id": str(funder.id),
            "funder_name": funder.name,
            "contacts_found": len(people),
            "contacts": people,
        }
    except ValueError:
        return {
            "status": "error",
            "message": f"Invalid UUID: {funder_id}",
            "contacts_found": 0,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "contacts_found": 0,
        }


@router.get("/export/csv")
async def export_contacts_csv(
    session: AsyncSession = Depends(get_db),
    role_category: Optional[str] = None,
    region: Optional[str] = None,  # colombia | global
) -> dict:
    """Export contacts to CSV.

    Returns CSV content as base64-encoded string.

    Query params:
    - role_category: Filter by role (partnerships, grants, cooperation, innovation, development)
    - region: 'colombia' for national contacts | 'global' for international | None for all
    """
    filters = []

    if role_category:
        filters.append(Contact.role_category == role_category)

    stmt = select(Contact)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.options(selectinload(Contact.funder)).order_by(Contact.fetched_at.desc())

    result = await session.execute(stmt)
    contacts = result.scalars().unique().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    headers = [
        "ID", "Nombre", "Apellido", "Cargo", "Categoría de Rol",
        "Email", "LinkedIn", "Organización", "Historial aeioTU",
        "Fuente", "Fecha de Obtención",
    ]
    writer.writerow(headers)

    # Rows
    for contact in contacts:
        writer.writerow([
            str(contact.id),
            contact.full_name,
            contact.last_name or "",
            contact.title or "",
            contact.role_category or "",
            contact.email or "",
            contact.linkedin_url or "",
            contact.funder.name if contact.funder else "",
            "Sí" if contact.aeiotu_connection else "No",
            contact.source,
            contact.fetched_at.strftime("%Y-%m-%d") if contact.fetched_at else "",
        ])

    csv_content = output.getvalue()
    csv_b64 = base64.b64encode(csv_content.encode()).decode()

    return {
        "filename": f"contacts_{region or 'all'}.csv",
        "content_base64": csv_b64,
    }
