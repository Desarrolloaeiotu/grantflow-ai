import uuid
from datetime import date, datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    funder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funders.id", ondelete="SET NULL"), nullable=True
    )

    amount_min_cop: Mapped[int | None] = mapped_column(BigInteger)
    amount_max_cop: Mapped[int | None] = mapped_column(BigInteger)
    deadline: Mapped[date | None] = mapped_column(Date)
    target_contact_date: Mapped[date | None] = mapped_column(Date)
    open_date: Mapped[date | None] = mapped_column(Date)

    # URLs
    url_rfp: Mapped[str | None] = mapped_column(Text)
    url_source: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(Text)
    url_tor: Mapped[str | None] = mapped_column(Text)
    url_form: Mapped[str | None] = mapped_column(Text)

    # Contacto de la organización
    org_website: Mapped[str | None] = mapped_column(Text)
    org_email: Mapped[str | None] = mapped_column(Text)
    org_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    org_email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # CEO / Representante legal
    ceo_name: Mapped[str | None] = mapped_column(Text)
    ceo_title: Mapped[str | None] = mapped_column(Text)
    ceo_email: Mapped[str | None] = mapped_column(Text)
    ceo_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    ceo_email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    ceo_linkedin_url: Mapped[str | None] = mapped_column(Text)
    ceo_apollo_id: Mapped[str | None] = mapped_column(Text)

    # Clasificación y scoring
    market_window: Mapped[str | None] = mapped_column(Text)
    capital_type: Mapped[str | None] = mapped_column(Text)  # grant|loan|investment|contract
    tender_type: Mapped[str | None] = mapped_column(Text)  # grant|premio|evento|curso
    score_total: Mapped[int | None] = mapped_column(Integer)
    score_details: Mapped[dict | None] = mapped_column(JSONB)
    decision: Mapped[str | None] = mapped_column(Text)  # go|no_go|pending
    urgency: Mapped[str | None] = mapped_column(Text)  # high|medium|low
    status: Mapped[str] = mapped_column(Text, default="detected")

    # Vector y metadatos
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    detected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    raw_content: Mapped[str | None] = mapped_column(Text)

    funder: Mapped["app.models.funder.Funder | None"] = relationship("Funder", lazy="select")  # type: ignore[name-defined]
