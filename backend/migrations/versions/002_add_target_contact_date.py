"""Add target_contact_date to opportunities.

Campo separado del deadline. Sirve para alertas tipo "contactar MEN antes
de febrero" sin contaminar las alertas urgentes de cierre de convocatoria.

Útil principalmente para opps de negociación directa (manual_nacional) donde
no hay convocatoria con cierre fijo, sino una ventana óptima de contacto.

Revision ID: 002
Revises: 001
Create Date: 2026-05-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column("target_contact_date", sa.Date(), nullable=True),
    )
    op.create_index(
        "idx_opp_target_contact_date",
        "opportunities",
        ["target_contact_date"],
    )


def downgrade() -> None:
    op.drop_index("idx_opp_target_contact_date", "opportunities")
    op.drop_column("opportunities", "target_contact_date")
