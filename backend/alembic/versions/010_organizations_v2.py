"""Add organizations v2 columns to funders, contacts, and opportunities.

Revision ID: 010
Revises: 009
Create Date: 2026-06-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Funders: Add organization v2 fields ──────────────────────────────────
    op.add_column('funders', sa.Column('access_type', sa.Text(), nullable=True))
    op.add_column('funders', sa.Column('strategic_obj', sa.Text(), nullable=True))
    op.add_column('funders', sa.Column('invests_colombia', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('funders', sa.Column('invests_latam', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('funders', sa.Column('aeiotu_role', sa.Text(), nullable=True))
    op.add_column('funders', sa.Column('general_objective', sa.Text(), nullable=True))

    # ── Contacts: Add key contact fields ──────────────────────────────────────
    op.add_column('contacts', sa.Column('last_name', sa.Text(), nullable=True))
    op.add_column('contacts', sa.Column('role_category', sa.Text(), nullable=True))
    op.add_column('contacts', sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_contacts_opportunity_id', 'contacts', 'opportunities', ['opportunity_id'], ['id'], ondelete='SET NULL')

    # ── Opportunities: Add tender fields ──────────────────────────────────────
    op.add_column('opportunities', sa.Column('tender_type', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('url_tor', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('url_form', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('open_date', sa.Date(), nullable=True))


def downgrade() -> None:
    # ── Remove opportunities fields ───────────────────────────────────────────
    op.drop_column('opportunities', 'open_date')
    op.drop_column('opportunities', 'url_form')
    op.drop_column('opportunities', 'url_tor')
    op.drop_column('opportunities', 'tender_type')

    # ── Remove contacts fields ───────────────────────────────────────────────
    op.drop_constraint('fk_contacts_opportunity_id', 'contacts', type_='foreignkey')
    op.drop_column('contacts', 'opportunity_id')
    op.drop_column('contacts', 'role_category')
    op.drop_column('contacts', 'last_name')

    # ── Remove funders fields ────────────────────────────────────────────────
    op.drop_column('funders', 'general_objective')
    op.drop_column('funders', 'aeiotu_role')
    op.drop_column('funders', 'invests_latam')
    op.drop_column('funders', 'invests_colombia')
    op.drop_column('funders', 'strategic_obj')
    op.drop_column('funders', 'access_type')
