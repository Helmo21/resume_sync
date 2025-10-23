"""add linkedin_cookies to users

Revision ID: 492b8f1635d3
Revises: 1edf5be68aad
Create Date: 2025-10-15 13:24:02.988849

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '492b8f1635d3'
down_revision = '1edf5be68aad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('linkedin_cookies', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'linkedin_cookies')
