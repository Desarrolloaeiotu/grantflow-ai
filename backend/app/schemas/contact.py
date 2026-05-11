import uuid
from datetime import datetime

from pydantic import BaseModel


class ContactRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    title: str | None
    email: str | None
    linkedin_url: str | None
    funder_id: uuid.UUID | None
    aeiotu_connection: bool
    source: str
    fetched_at: datetime


class EmailVerifyRequest(BaseModel):
    email: str
    name: str | None = None
