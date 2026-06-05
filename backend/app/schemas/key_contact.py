"""Schemas for Key Contacts."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class KeyContactBase(BaseModel):
    """Base contact fields."""
    full_name: str
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    role_category: Optional[str] = None  # partnerships | grants | cooperation | innovation | development


class KeyContactCreate(KeyContactBase):
    """Create contact."""
    funder_id: Optional[UUID] = None


class KeyContactRead(KeyContactBase):
    """Read contact."""
    model_config = {"from_attributes": True}

    id: UUID
    funder_id: Optional[UUID] = None
    funder_name: Optional[str] = None
    created_at: datetime


class KeyContactListResponse(BaseModel):
    """List response for contacts."""
    items: list[KeyContactRead]
    total: int
