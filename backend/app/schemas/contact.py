import uuid
from datetime import datetime

from pydantic import BaseModel


class ContactRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    last_name: str | None = None
    title: str | None
    email: str | None
    linkedin_url: str | None
    funder_id: uuid.UUID | None
    aeiotu_connection: bool
    source: str
    role_category: str | None = None  # partnerships | grants | cooperation | innovation | development
    opportunity_id: uuid.UUID | None = None
    fetched_at: datetime


class KeyContactRead(BaseModel):
    """Key contact with organization reference."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    last_name: str | None = None
    title: str | None
    role_category: str | None = None
    email: str | None
    linkedin_url: str | None
    funder_name: str | None = None


class ContactList(BaseModel):
    items: list[KeyContactRead]
    total: int
    page: int = 1
    size: int = 25


class EmailVerifyRequest(BaseModel):
    email: str
    name: str | None = None
