import uuid
from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Convocation(Base):
    __tablename__ = "convocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Mandatory fields
    title: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)  # grant|premio|evento|curso
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    open_date: Mapped[date] = mapped_column(Date, nullable=False)
    url_convocation: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional but important
    amount_min_cop: Mapped[int | None] = mapped_column(BigInteger)
    amount_max_cop: Mapped[int | None] = mapped_column(BigInteger)
    url_tor: Mapped[str | None] = mapped_column(Text)
    url_form: Mapped[str | None] = mapped_column(Text)

    # Organization & lineage
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funders.id", ondelete="SET NULL"), nullable=True
    )
    organization_website: Mapped[str | None] = mapped_column(Text)

    # Metadata
    source_name: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)

    # Quality
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    data_completeness: Mapped[int] = mapped_column(default=0)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization: Mapped["app.models.funder.Funder | None"] = relationship("Funder", lazy="select")  # type: ignore[name-defined]
