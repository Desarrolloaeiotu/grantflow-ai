"""Create endpoint_monitor_log table for API endpoint monitoring.

Revision ID: 008
Revises: 007
Create Date: 2026-06-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'endpoint_monitor_log',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('endpoint_name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # 'healthy' | 'degraded' | 'failed'
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('results', postgresql.JSONB(), nullable=True),  # {parsed_ok, content_type, entry_count}
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('alerted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_endpoint_monitor_date', 'endpoint_name', 'checked_at'),
        sa.Index('idx_endpoint_monitor_status', 'status'),
    )


def downgrade() -> None:
    op.drop_table('endpoint_monitor_log')
