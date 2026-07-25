"""add document_type

Revision ID: 110b5591f853
Revises: 
Create Date: 2026-07-25 14:40:24.338314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '110b5591f853'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('document_type', sa.String(), nullable=True, server_default='generic'))


def downgrade() -> None:
    op.drop_column('documents', 'document_type')
