"""Add KRS schema

Revision ID: 002
Revises: 001_initial_pmb_schema
Create Date: 2025-11-03 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Enum
import enum


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001_initial_pmb_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class KRSStatusEnum(enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REVISION = "REVISION"


def upgrade() -> None:
    # Create matakuliah table
    op.create_table(
        'matakuliah',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kode', sa.String(10), nullable=False),
        sa.Column('nama', sa.String(255), nullable=False),
        sa.Column('sks', sa.Integer(), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('hari', sa.String(20), nullable=False),
        sa.Column('jam_mulai', sa.Time(), nullable=False),
        sa.Column('jam_selesai', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kode')
    )

    # Create prerequisite table
    op.create_table(
        'prerequisite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matakuliah_id', sa.Integer(), nullable=False),
        sa.Column('prerequisite_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['matakuliah_id'], ['matakuliah.id'], ),
        sa.ForeignKeyConstraint(['prerequisite_id'], ['matakuliah.id'], ),
        sa.PrimaryKeyConstraint('id'),
        # Add constraint to prevent self-referencing prerequisites
        sa.CheckConstraint('matakuliah_id != prerequisite_id', name='check_not_self_prerequisite')
    )

    # Create krs table
    op.create_table(
        'krs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nim', sa.String(20), nullable=False),
        sa.Column('semester', sa.String(10), nullable=False),
        sa.Column('status', Enum(KRSStatusEnum, name='krs_status_enum'), nullable=False),
        sa.Column('dosen_pa_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create krs_detail table
    op.create_table(
        'krs_detail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('krs_id', sa.Integer(), nullable=False),
        sa.Column('matakuliah_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['krs_id'], ['krs.id'], ),
        sa.ForeignKeyConstraint(['matakuliah_id'], ['matakuliah.id'], ),
        sa.PrimaryKeyConstraint('id'),
        # Add unique constraint to prevent duplicate courses in the same KRS
        sa.UniqueConstraint('krs_id', 'matakuliah_id', name='unique_krs_matakuliah')
    )


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('krs_detail')
    op.drop_table('krs')
    op.drop_table('prerequisite')
    op.drop_table('matakuliah')
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS krs_status_enum")