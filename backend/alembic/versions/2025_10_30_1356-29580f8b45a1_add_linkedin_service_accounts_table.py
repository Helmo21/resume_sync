"""add_linkedin_service_accounts_table

Revision ID: 29580f8b45a1
Revises: c04023fc6044
Create Date: 2025-10-30 13:56:29.704732

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = '29580f8b45a1'
down_revision = 'c04023fc6044'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create linkedin_service_accounts table
    op.create_table(
        'linkedin_service_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(), nullable=False, comment='Encrypted email'),
        sa.Column('password', sa.String(), nullable=False, comment='Encrypted password'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, default=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('requests_count_today', sa.Integer(), nullable=False, default=0, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )


def downgrade() -> None:
    # Drop linkedin_service_accounts table
    op.drop_table('linkedin_service_accounts')
