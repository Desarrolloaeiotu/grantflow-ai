"""Create scraper_monitor_log table for structure monitoring.

Revision ID: 007
Revises: 006
Create Date: 2026-06-01 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'scraper_monitor_log',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source_name', sa.String(50), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # 'healthy' | 'degraded' | 'failed'
        sa.Column('results', postgresql.JSONB(), nullable=True),  # {selector_name: {found, expected, status}}
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('alerted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_monitor_source_date', 'source_name', 'checked_at'),
        sa.Index('idx_monitor_status', 'status'),
    )


def downgrade() -> None:
    op.drop_table('scraper_monitor_log')
