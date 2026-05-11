import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScoreLog(Base):
    __tablename__ = "score_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False
    )
    criterion_1: Mapped[int | None] = mapped_column(
        SmallInteger, CheckConstraint("criterion_1 BETWEEN 0 AND 2")
    )
    criterion_2: Mapped[int | None] = mapped_column(
        SmallInteger, CheckConstraint("criterion_2 BETWEEN 0 AND 2")
    )
    criterion_3: Mapped[int | None] = mapped_column(
        SmallInteger, CheckConstraint("criterion_3 BETWEEN 0 AND 2")
    )
    criterion_4: Mapped[int | None] = mapped_column(
        SmallInteger, CheckConstraint("criterion_4 BETWEEN 0 AND 2")
    )
    criterion_5: Mapped[int | None] = mapped_column(
        SmallInteger, CheckConstraint("criterion_5 BETWEEN 0 AND 2")
    )
    llm_reasoning: Mapped[str | None] = mapped_column(Text)
    scored_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    scored_by: Mapped[str] = mapped_column(Text, default="auto")  # auto | email del revisor
