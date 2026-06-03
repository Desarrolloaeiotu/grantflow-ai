import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ContactInOrganization(BaseModel):
    """Contact embedded in organization response."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    last_name: Optional[str] = None
    title: Optional[str] = None
    role_category: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None


class OrganizationCreate(BaseModel):
    name: str
    org_type: Optional[str] = None  # Filantropía | ONG | Multilateral | Público | Privado | Banco | Cooperación | Tercer sector
    country: Optional[str] = None
    access_type: Optional[str] = None  # convocatoria | mixto | relacional | invitacion
    strategic_obj: Optional[str] = None  # capital | exportacion_modelo | red
    invests_colombia: bool = False
    invests_latam: bool = False
    general_objective: Optional[str] = None
    aeiotu_role: Optional[str] = None  # financiador | aliado | escalador | visibilidad
    website: Optional[str] = None
    focus_sectors: Optional[list[str]] = None
    ticket_min_usd: Optional[int] = None
    ticket_max_usd: Optional[int] = None
    has_history: bool = False
    notes: Optional[str] = None


class OrganizationRead(OrganizationCreate):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    created_at: datetime
    contacts: list[ContactInOrganization] = []


class OrganizationList(BaseModel):
    items: list[OrganizationRead]
    total: int
    page: int = 1
    size: int = 25
