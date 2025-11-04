"""Add NIM column to calon_mahasiswa table

Revision ID: 002_add_nim_column
Revises: 001_initial_pmb_schema
Create Date: 2025-11-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_nim_column'
down_revision = '001_initial_pmb_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nim column to calon_mahasiswa table
    op.add_column('calon_mahasiswa', sa.Column('nim', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove nim column from calon_mahasiswa table
    op.drop_column('calon_mahasiswa', 'nim')
