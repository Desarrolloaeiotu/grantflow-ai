from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class ConvocationCreate(BaseModel):
    model_config = ConfigDict(validate_assignment=False)

    title: str = Field(..., min_length=5, max_length=500)
    objective: str = Field(..., min_length=10, max_length=5000)
    type: str = Field(...)
    deadline: date = Field(...)
    open_date: date = Field(...)
    url_convocation: str = Field(...)

    amount_min_cop: Optional[int] = Field(None, ge=0)
    amount_max_cop: Optional[int] = Field(None, ge=0)
    url_tor: Optional[str] = None
    url_form: Optional[str] = None
    organization_id: Optional[str] = None
    organization_website: Optional[str] = None

    source_name: str = Field(...)
    source_url: Optional[str] = None

    # Will be set by validators
    data_completeness: int = 0
    verified: bool = False

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = {"grant", "premio", "evento", "curso"}
        if v.lower() not in valid_types:
            raise ValueError(f"type must be one of {valid_types}")
        return v.lower()

    @model_validator(mode='after')
    def validate_dates(self):
        if self.deadline < self.open_date:
            raise ValueError("deadline must be after open_date")
        return self

    @model_validator(mode='after')
    def validate_amounts(self):
        if self.amount_min_cop and self.amount_max_cop and self.amount_max_cop < self.amount_min_cop:
            raise ValueError("amount_max_cop must be >= amount_min_cop")
        return self

    @model_validator(mode='after')
    def calculate_completeness(self):
        mandatory_fields = {"title", "objective", "type", "deadline", "open_date", "url_convocation", "source_name"}
        optional_fields = {"amount_min_cop", "amount_max_cop", "url_tor", "url_form", "organization_id"}

        mandatory_filled = sum(1 for f in mandatory_fields if getattr(self, f))
        optional_filled = sum(1 for f in optional_fields if getattr(self, f))

        completeness = int((mandatory_filled / len(mandatory_fields)) * 70 + (optional_filled / len(optional_fields)) * 30)
        object.__setattr__(self, "data_completeness", min(100, completeness))
        object.__setattr__(self, "verified", mandatory_filled == len(mandatory_fields))

        return self


class ConvocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    objective: str
    type: str
    deadline: str
    open_date: str
    url_convocation: str
    amount_min_cop: Optional[int] = None
    amount_max_cop: Optional[int] = None
    url_tor: Optional[str] = None
    url_form: Optional[str] = None
    organization_id: Optional[str] = None
    organization_website: Optional[str] = None
    source_name: str
    verified: bool
    data_completeness: int
    detected_at: str
