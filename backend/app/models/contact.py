import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    funder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funders.id", ondelete="SET NULL"), nullable=True
    )
    aeiotu_connection: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(Text, default="apollo")  # apollo|manual|linkedin

    # ── Key contact v2 fields ────────────────────────────────────────────
    role_category: Mapped[str | None] = mapped_column(Text)  # partnerships|grants|cooperation|innovation|development
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True
    )

    # ── GLOBAL module extended fields ────────────────────────────────────────
    priority_score: Mapped[int | None] = mapped_column(Integer)  # 1-5, relevance to aeioTU
    department: Mapped[str | None] = mapped_column(Text)  # partnerships|grants|program|development
    last_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    verified_email_apollo: Mapped[bool] = mapped_column(Boolean, default=False)
    social_profiles: Mapped[dict | None] = mapped_column(JSONB)  # {twitter, github, personal_web, etc}

    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
