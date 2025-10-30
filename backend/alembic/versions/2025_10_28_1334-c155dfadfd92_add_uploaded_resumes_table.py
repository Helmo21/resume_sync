"""add_uploaded_resumes_table

Revision ID: c155dfadfd92
Revises: b9b1f396c058
Create Date: 2025-10-28 13:34:41.193970

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c155dfadfd92'
down_revision = 'b9b1f396c058'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only create uploaded_resumes table (other tables created by initial migration)
    op.create_table('uploaded_resumes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('file_path', sa.Text(), nullable=True),
    sa.Column('parsed_text', sa.Text(), nullable=False),
    sa.Column('analyzed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Only drop uploaded_resumes table
    op.drop_table('uploaded_resumes')
