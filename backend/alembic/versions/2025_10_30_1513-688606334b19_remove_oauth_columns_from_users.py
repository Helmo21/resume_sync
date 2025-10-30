"""remove_oauth_columns_from_users

Revision ID: 688606334b19
Revises: 29580f8b45a1
Create Date: 2025-10-30 15:13:02.518019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '688606334b19'
down_revision = '29580f8b45a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove OAuth columns from users table
    op.drop_column('users', 'linkedin_id')
    op.drop_column('users', 'linkedin_access_token')
    op.drop_column('users', 'linkedin_refresh_token')


def downgrade() -> None:
    # Re-add OAuth columns if we need to rollback
    op.add_column('users', sa.Column('linkedin_refresh_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('linkedin_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('linkedin_id', sa.String(), nullable=True))
    op.create_index('ix_users_linkedin_id', 'users', ['linkedin_id'], unique=True)
