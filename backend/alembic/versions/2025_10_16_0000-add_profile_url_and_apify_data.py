"""add profile_url and apify_data to linkedin_profiles

Revision ID: 6a8c9d2e3f4b
Revises: 492b8f1635d3
Create Date: 2025-10-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '6a8c9d2e3f4b'
down_revision = '492b8f1635d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add profile_url column to linkedin_profiles table
    op.add_column('linkedin_profiles',
                  sa.Column('profile_url', sa.String(), nullable=True))

    # Add apify_data column to linkedin_profiles table
    op.add_column('linkedin_profiles',
                  sa.Column('apify_data', JSONB(), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('linkedin_profiles', 'apify_data')
    op.drop_column('linkedin_profiles', 'profile_url')
