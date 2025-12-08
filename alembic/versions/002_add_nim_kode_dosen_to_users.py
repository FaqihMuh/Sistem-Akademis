"""Add nim and kode_dosen fields to users table

Revision ID: 002_add_nim_kode_dosen_to_users
Revises: 001_create_schedule_tables
Create Date: 2025-11-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_add_nim_kode_dosen_to_users'
down_revision = '001_create_schedule_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nim column to users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('nim', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('kode_dosen', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove nim and kode_dosen columns from users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('kode_dosen')
        batch_op.drop_column('nim')