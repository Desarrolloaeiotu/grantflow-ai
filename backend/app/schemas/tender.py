"""Schemas for Tenders (formal opportunities with amounts/deadlines)."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TenderBase(BaseModel):
    """Base tender fields."""
    title: str
    description: Optional[str] = None
    tender_type: Optional[str] = None  # grant | premio | evento | curso
    amount_min_cop: Optional[int] = None
    amount_max_cop: Optional[int] = None
    deadline: Optional[date] = None
    open_date: Optional[date] = None
    url_rfp: Optional[str] = None
    url_tor: Optional[str] = None
    url_form: Optional[str] = None
    org_website: Optional[str] = None
    org_email: Optional[str] = None
    region: str = "nacional"  # nacional | global | latam


class TenderCreate(TenderBase):
    """Create tender."""
    funder_id: Optional[UUID] = None
    funder_name: str


class TenderRead(TenderBase):
    """Read tender."""
    model_config = {"from_attributes": True}

    id: UUID
    funder_id: Optional[UUID] = None
    funder_name: Optional[str] = None
    score_total: Optional[int] = None
    decision: Optional[str] = None

    # GLOBAL module fields
    sector_alignment: Optional[dict] = None  # {ecd: 0.9, education: 0.8}
    region_target: Optional[str] = None  # global | latam | colombia | specific_countries
    funder_strategic_fit: Optional[int] = None  # 1-10
    market_window: Optional[str] = None  # funding_colombia | funding_global | strategic | latam
    urgency: Optional[str] = None  # high | medium | low

    detected_at: datetime
    last_scraped_at: Optional[datetime] = None


class TenderListResponse(BaseModel):
    """List response for tenders."""
    items: list[TenderRead]
    total: int
    page: int
    size: int
