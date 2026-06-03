import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TenderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    funder_id: Optional[uuid.UUID] = None
    tender_type: Optional[str] = None  # grant | premio | evento | curso
    amount_min_cop: Optional[int] = None
    amount_max_cop: Optional[int] = None
    open_date: Optional[date] = None
    deadline: Optional[date] = None
    url_rfp: Optional[str] = None
    url_tor: Optional[str] = None
    url_form: Optional[str] = None
    source_name: Optional[str] = None
    market_window: Optional[str] = None  # funding_colombia | funding_global | strategic | latam


class TenderRead(TenderCreate):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    url_source: Optional[str] = None
    org_website: Optional[str] = None
    funder_name: Optional[str] = None
    score_total: Optional[int] = None
    decision: Optional[str] = None  # go | no_go | pending
    status: str = "detected"
    detected_at: datetime
    updated_at: datetime


class TenderList(BaseModel):
    items: list[TenderRead]
    total: int
    page: int = 1
    size: int = 25
