"""Add kode_dosen field to dosen table for consistency

Revision ID: 003_add_kode_dosen_to_dosen
Revises: 002_add_nim_kode_dosen_to_users
Create Date: 2025-11-29 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_add_kode_dosen_to_dosen'
down_revision = '002_add_nim_kode_dosen_to_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add kode_dosen column to dosen table
    with op.batch_alter_table('dosen') as batch_op:
        batch_op.add_column(sa.Column('kode_dosen', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove kode_dosen column from dosen table
    with op.batch_alter_table('dosen') as batch_op:
        batch_op.drop_column('kode_dosen')