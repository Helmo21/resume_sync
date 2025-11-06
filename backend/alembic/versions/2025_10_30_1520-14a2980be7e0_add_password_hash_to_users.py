"""add_password_hash_to_users

Revision ID: 14a2980be7e0
Revises: 688606334b19
Create Date: 2025-10-30 15:20:49.559689

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14a2980be7e0'
down_revision = '688606334b19'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash column for email/password authentication
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove password_hash column
    op.drop_column('users', 'password_hash')
