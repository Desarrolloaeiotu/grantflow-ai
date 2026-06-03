import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, Boolean, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Funder(Base):
    __tablename__ = "funders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str | None] = mapped_column(Text)
    org_type: Mapped[str | None] = mapped_column(Text)  # foundation|multilateral|government|corporate
    focus_sectors: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    ticket_min_usd: Mapped[int | None] = mapped_column()
    ticket_max_usd: Mapped[int | None] = mapped_column()
    website: Mapped[str | None] = mapped_column(Text)
    has_history: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # ── Organizations v2 fields ──────────────────────────────────────────
    access_type: Mapped[str | None] = mapped_column(Text)  # convocatoria|mixto|relacional|invitacion
    strategic_obj: Mapped[str | None] = mapped_column(Text)  # capital|exportacion_modelo|red
    invests_colombia: Mapped[bool] = mapped_column(Boolean, default=False)
    invests_latam: Mapped[bool] = mapped_column(Boolean, default=False)
    aeiotu_role: Mapped[str | None] = mapped_column(Text)  # financiador|aliado|escalador|visibilidad
    general_objective: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ────────────────────────────────────────────────────────
    contacts: Mapped[list['Contact']] = relationship('Contact', back_populates=None)
