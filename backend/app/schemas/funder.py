import uuid
from datetime import datetime

from pydantic import BaseModel


class FunderCreate(BaseModel):
    name: str
    country: str | None = None
    org_type: str | None = None
    focus_sectors: list[str] | None = None
    ticket_min_usd: int | None = None
    ticket_max_usd: int | None = None
    website: str | None = None
    has_history: bool = False
    notes: str | None = None


class FunderRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    country: str | None
    org_type: str | None
    focus_sectors: list[str] | None
    ticket_min_usd: int | None
    ticket_max_usd: int | None
    website: str | None
    has_history: bool
    notes: str | None
    created_at: datetime


class FunderList(BaseModel):
    items: list[FunderRead]
    total: int
    page: int = 1
    size: int = 25
