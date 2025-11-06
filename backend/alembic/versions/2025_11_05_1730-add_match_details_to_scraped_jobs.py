"""add match_details to scraped_jobs

Revision ID: add_match_details_v2
Revises: 14a2980be7e0
Create Date: 2025-11-05 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_match_details_v2'
down_revision = '14a2980be7e0'
branch_labels = None
depends_on = None


def upgrade():
    """Add match_details JSONB column to scraped_jobs table"""
    # Add match_details column
    op.add_column('scraped_jobs',
        sa.Column('match_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    print("✅ Added match_details column to scraped_jobs table")


def downgrade():
    """Remove match_details column from scraped_jobs table"""
    op.drop_column('scraped_jobs', 'match_details')

    print("✅ Removed match_details column from scraped_jobs table")
