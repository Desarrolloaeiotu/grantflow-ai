"""Create scraper_metrics table for success rate monitoring.

Revision ID: 009
Revises: 008
Create Date: 2026-06-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'scraper_metrics',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('scraper_name', sa.String(50), nullable=False),  # 'grantsgov' | 'bid' | 'nacional_colombia' | ...
        sa.Column('run_date', sa.Date(), nullable=False),
        sa.Column('total_normalized', sa.Integer(), nullable=False),  # items after normalize() filter
        sa.Column('total_persisted', sa.Integer(), nullable=False),  # newly inserted into DB
        sa.Column('total_skipped', sa.Integer(), nullable=False),  # duplicates rejected
        sa.Column('errors_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('run_duration_sec', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_scraper_metrics_name_date', 'scraper_name', 'run_date'),
        sa.Index('idx_scraper_metrics_date', 'run_date'),
    )


def downgrade() -> None:
    op.drop_table('scraper_metrics')
