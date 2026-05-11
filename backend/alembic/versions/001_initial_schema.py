"""Schema inicial GrantFlow AI

Revision ID: 001
Revises:
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensiones requeridas
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_cron")

    # ── funders ───────────────────────────────────────────────────────────────
    op.create_table(
        "funders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("country", sa.Text),
        sa.Column("org_type", sa.Text),
        sa.Column("focus_sectors", postgresql.ARRAY(sa.Text)),
        sa.Column("ticket_min_usd", sa.Integer),
        sa.Column("ticket_max_usd", sa.Integer),
        sa.Column("website", sa.Text),
        sa.Column("has_history", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── opportunities ─────────────────────────────────────────────────────────
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "funder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("funders.id", ondelete="SET NULL"),
        ),
        sa.Column("amount_min_cop", sa.BigInteger),
        sa.Column("amount_max_cop", sa.BigInteger),
        sa.Column("deadline", sa.Date),
        # URLs
        sa.Column("url_rfp", sa.Text),
        sa.Column("url_source", sa.Text),
        sa.Column("source_name", sa.Text),
        # Contacto organización
        sa.Column("org_website", sa.Text),
        sa.Column("org_email", sa.Text),
        sa.Column("org_email_verified", sa.Boolean, server_default="false"),
        sa.Column("org_email_verified_at", postgresql.TIMESTAMP(timezone=True)),
        # CEO
        sa.Column("ceo_name", sa.Text),
        sa.Column("ceo_title", sa.Text),
        sa.Column("ceo_email", sa.Text),
        sa.Column("ceo_email_verified", sa.Boolean, server_default="false"),
        sa.Column("ceo_email_verified_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("ceo_linkedin_url", sa.Text),
        sa.Column("ceo_apollo_id", sa.Text),
        # Clasificación
        sa.Column("market_window", sa.Text),
        sa.Column("capital_type", sa.Text),
        sa.Column("score_total", sa.Integer),
        sa.Column("score_details", postgresql.JSONB),
        sa.Column("decision", sa.Text),
        sa.Column("urgency", sa.Text),
        sa.Column("status", sa.Text, server_default="'detected'"),
        # Vector y metadatos
        sa.Column("embedding", Vector(768)),
        sa.Column(
            "detected_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("raw_content", sa.Text),
    )

    # Índices de oportunidades
    op.create_index("idx_opp_decision", "opportunities", ["decision"])
    op.create_index("idx_opp_deadline", "opportunities", ["deadline"])
    op.create_index("idx_opp_window", "opportunities", ["market_window"])
    op.create_index("idx_opp_score", "opportunities", [sa.text("score_total DESC NULLS LAST")])
    op.create_index("idx_opp_status", "opportunities", ["status"])
    op.create_index("idx_opp_source", "opportunities", ["source_name"])
    op.execute(
        "CREATE INDEX idx_opp_embedding ON opportunities "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # ── contacts ──────────────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.Text, nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("email", sa.Text),
        sa.Column("linkedin_url", sa.Text),
        sa.Column(
            "funder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("funders.id", ondelete="SET NULL"),
        ),
        sa.Column("aeiotu_connection", sa.Boolean, server_default="false"),
        sa.Column("source", sa.Text, server_default="'apollo'"),
        sa.Column(
            "fetched_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── score_log ─────────────────────────────────────────────────────────────
    op.create_table(
        "score_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "opportunity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "criterion_1",
            sa.SmallInteger,
            sa.CheckConstraint("criterion_1 BETWEEN 0 AND 2"),
        ),
        sa.Column(
            "criterion_2",
            sa.SmallInteger,
            sa.CheckConstraint("criterion_2 BETWEEN 0 AND 2"),
        ),
        sa.Column(
            "criterion_3",
            sa.SmallInteger,
            sa.CheckConstraint("criterion_3 BETWEEN 0 AND 2"),
        ),
        sa.Column(
            "criterion_4",
            sa.SmallInteger,
            sa.CheckConstraint("criterion_4 BETWEEN 0 AND 2"),
        ),
        sa.Column(
            "criterion_5",
            sa.SmallInteger,
            sa.CheckConstraint("criterion_5 BETWEEN 0 AND 2"),
        ),
        sa.Column("llm_reasoning", sa.Text),
        sa.Column(
            "scored_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("scored_by", sa.Text, server_default="'auto'"),
    )

    op.create_index("idx_score_log_opp", "score_log", ["opportunity_id"])


def downgrade() -> None:
    op.drop_table("score_log")
    op.drop_table("contacts")
    op.execute("DROP INDEX IF EXISTS idx_opp_embedding")
    op.drop_table("opportunities")
    op.drop_table("funders")
    op.execute("DROP EXTENSION IF EXISTS vector")
