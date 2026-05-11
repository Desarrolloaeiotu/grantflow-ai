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
    # Integración Apollo.io — activar en mes 5
    return {"email": body.email, "verified": False, "status": "apollo_not_configured"}


@router.post("/enrich")
async def enrich_contacts() -> dict:
    # Trigger n8n workflow para enriquecer contactos con Apollo.io
    return {"status": "enrich_triggered", "note": "Activar Apollo.io en mes 5"}
