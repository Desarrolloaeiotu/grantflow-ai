import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    title: str
    description: str | None = None
    funder_name: str | None = None  # Se resuelve a funder_id en el servicio
    amount_min_cop: int | None = None
    amount_max_cop: int | None = None
    deadline: date | None = None
    url_rfp: str | None = None
    url_source: str | None = None
    source_name: str | None = None
    org_website: str | None = None
    eligible_countries: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    capital_type: str | None = "grant"
    raw_content: str | None = None


class OpportunityUpdate(BaseModel):
    status: Literal["detected", "reviewed", "in_crm", "discarded"] | None = None
    decision: Literal["go", "no_go", "pending"] | None = None
    urgency: Literal["high", "medium", "low"] | None = None
    notes: str | None = None


class ScoreDetails(BaseModel):
    c1: int
    c2: int
    c3: int
    c4: int
    c5: int
    llm_justification: str = ""
    confidence: str = "medium"


class OpportunityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    description: str | None
    amount_min_cop: int | None
    amount_max_cop: int | None
    deadline: date | None
    target_contact_date: date | None
    url_rfp: str | None
    url_source: str | None
    source_name: str | None
    market_window: str | None
    capital_type: str | None
    score_total: int | None
    score_details: dict | None
    decision: str | None
    urgency: str | None
    status: str
    detected_at: datetime
    updated_at: datetime
    org_website: str | None
    org_email: str | None
    org_email_verified: bool
    ceo_name: str | None
    ceo_email: str | None
    ceo_email_verified: bool
    ceo_linkedin_url: str | None


class OpportunityList(BaseModel):
    items: list[OpportunityRead]
    total: int
    page: int
    size: int
