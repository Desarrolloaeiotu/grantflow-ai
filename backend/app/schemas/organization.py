"""Schemas for Organizations (Funders) - GLOBAL module."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """Base organization fields."""
    name: str
    org_type: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    focus_sectors: Optional[list[str]] = None
    ticket_min_usd: Optional[int] = None
    ticket_max_usd: Optional[int] = None
    min_grant_cop: Optional[int] = None
    max_grant_cop: Optional[int] = None

    # v2 GLOBAL fields
    access_type: Optional[str] = None
    strategic_obj: Optional[str] = None
    invests_colombia: bool = False
    invests_latam: bool = False
    aeiotu_role: Optional[str] = None
    general_objective: Optional[str] = None
    has_history: bool = False
    verified_data: bool = False
    notes: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Create organization."""
    pass


class OrganizationRead(OrganizationBase):
    """Read organization with all fields."""
    model_config = {"from_attributes": True}

    id: UUID
    created_at: datetime
    last_scraped_at: Optional[datetime] = None


class OrganizationList(BaseModel):
    """List of organizations with pagination."""
    items: list[OrganizationRead]
    total: int
    page: int
    size: int
    pages: int = Field(default=0)

    def __init__(self, **data):
        super().__init__(**data)
        if self.size > 0:
            self.pages = (self.total + self.size - 1) // self.size
