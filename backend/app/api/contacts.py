import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactRead, EmailVerifyRequest

router = APIRouter()


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    funder_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[ContactRead]:
    q = select(Contact)
    if funder_id:
        q = q.where(Contact.funder_id == funder_id)
    rows = (await db.execute(q)).scalars().all()
    return [ContactRead.model_validate(c) for c in rows]


@router.post("/verify")
async def verify_email(body: EmailVerifyRequest) -> dict:
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
