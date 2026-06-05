"""Extend models for GLOBAL module: organizations, contacts, tenders

Revision ID: 011
Revises: 010
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── FUNDERS (Organizations) ──────────────────────────────────────────────
    # Add LinkedIn and grant amount fields in COP
    op.add_column('funders', sa.Column('linkedin_url', sa.String(), nullable=True))
    op.add_column('funders', sa.Column('min_grant_cop', sa.BigInteger(), nullable=True))
    op.add_column('funders', sa.Column('max_grant_cop', sa.BigInteger(), nullable=True))
    op.add_column('funders', sa.Column('last_scraped_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('funders', sa.Column('verified_data', sa.Boolean(), server_default='false', nullable=False))

    # ── CONTACTS (Key contacts) ──────────────────────────────────────────────
    # Add priority scoring and verification tracking
    op.add_column('contacts', sa.Column('priority_score', sa.SmallInteger(), nullable=True))
    op.add_column('contacts', sa.Column('department', sa.String(), nullable=True))
    op.add_column('contacts', sa.Column('last_verified_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('contacts', sa.Column('verified_email_apollo', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('contacts', sa.Column('social_profiles', postgresql.JSONB(), nullable=True))

    # ── OPPORTUNITIES (Tenders) ──────────────────────────────────────────────
    # Add strategic alignment and region targeting for GLOBAL module
    op.add_column('opportunities', sa.Column('sector_alignment', postgresql.JSONB(), nullable=True))
    op.add_column('opportunities', sa.Column('region_target', sa.String(), nullable=True))
    op.add_column('opportunities', sa.Column('funder_strategic_fit', sa.SmallInteger(), nullable=True))
    op.add_column('opportunities', sa.Column('last_scraped_at', postgresql.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    # ── OPPORTUNITIES ────────────────────────────────────────────────────────
    op.drop_column('opportunities', 'last_scraped_at')
    op.drop_column('opportunities', 'funder_strategic_fit')
    op.drop_column('opportunities', 'region_target')
    op.drop_column('opportunities', 'sector_alignment')

    # ── CONTACTS ─────────────────────────────────────────────────────────────
    op.drop_column('contacts', 'social_profiles')
    op.drop_column('contacts', 'verified_email_apollo')
    op.drop_column('contacts', 'last_verified_at')
    op.drop_column('contacts', 'department')
    op.drop_column('contacts', 'priority_score')

    # ── FUNDERS ──────────────────────────────────────────────────────────────
    op.drop_column('funders', 'verified_data')
    op.drop_column('funders', 'last_scraped_at')
    op.drop_column('funders', 'max_grant_cop')
    op.drop_column('funders', 'min_grant_cop')
    op.drop_column('funders', 'linkedin_url')
