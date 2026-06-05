"""Add v2 fields to funders, opportunities, and contacts tables

Revision ID: 010
Revises: 009
Create Date: 2026-06-03 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to funders table
    op.add_column('funders', sa.Column('access_type', sa.String(), nullable=True))
    op.add_column('funders', sa.Column('strategic_obj', sa.String(), nullable=True))
    op.add_column('funders', sa.Column('invests_colombia', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('funders', sa.Column('invests_latam', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('funders', sa.Column('aeiotu_role', sa.String(), nullable=True))
    op.add_column('funders', sa.Column('general_objective', sa.String(), nullable=True))

    # Add new columns to opportunities table
    op.add_column('opportunities', sa.Column('tender_type', sa.String(), nullable=True))
    op.add_column('opportunities', sa.Column('url_tor', sa.String(), nullable=True))
    op.add_column('opportunities', sa.Column('url_form', sa.String(), nullable=True))
    op.add_column('opportunities', sa.Column('open_date', sa.Date(), nullable=True))

    # Add new columns to contacts table
    op.add_column('contacts', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('contacts', sa.Column('role_category', sa.String(), nullable=True))
    op.add_column('contacts', sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create foreign key for opportunity_id
    op.create_foreign_key(
        'fk_contacts_opportunity_id',
        'contacts', 'opportunities',
        ['opportunity_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove foreign key
    op.drop_constraint('fk_contacts_opportunity_id', 'contacts', type_='foreignkey')

    # Drop columns from contacts table
    op.drop_column('contacts', 'opportunity_id')
    op.drop_column('contacts', 'role_category')
    op.drop_column('contacts', 'last_name')

    # Drop columns from opportunities table
    op.drop_column('opportunities', 'open_date')
    op.drop_column('opportunities', 'url_form')
    op.drop_column('opportunities', 'url_tor')
    op.drop_column('opportunities', 'tender_type')

    # Drop columns from funders table
    op.drop_column('funders', 'general_objective')
    op.drop_column('funders', 'aeiotu_role')
    op.drop_column('funders', 'invests_latam')
    op.drop_column('funders', 'invests_colombia')
    op.drop_column('funders', 'strategic_obj')
    op.drop_column('funders', 'access_type')
