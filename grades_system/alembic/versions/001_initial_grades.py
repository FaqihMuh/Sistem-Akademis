"""Create grades and grade_history tables

Revision ID: 001_initial_grades
Revises: 
Create Date: 2025-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_grades'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create grades table
    op.create_table(
        'grades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nim', sa.String(length=20), nullable=False),
        sa.Column('matakuliah_id', sa.Integer(), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('nilai_huruf', sa.String(length=2), nullable=False),
        sa.Column('nilai_angka', sa.Float(), nullable=False),
        sa.Column('sks', sa.Integer(), nullable=False),
        sa.Column('dosen_id', sa.Integer(), nullable=False),
        sa.Column('presensi', sa.Float(), server_default='100.0', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dosen_id'], ['dosen.id'], ),
        sa.ForeignKeyConstraint(['matakuliah_id'], ['matakuliah.id'], ),
        sa.ForeignKeyConstraint(['nim'], ['calon_mahasiswa.nim'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grades_id'), 'grades', ['id'], unique=False)

    # Create grade_history table
    op.create_table(
        'grade_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grade_id', sa.Integer(), nullable=False),
        sa.Column('old_value', sa.String(length=50), nullable=False),
        sa.Column('new_value', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.String(length=255), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['grade_id'], ['grades.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grade_history_id'), 'grade_history', ['id'], unique=False)


def downgrade():
    # Drop grade_history table first (due to foreign key constraint)
    op.drop_index(op.f('ix_grade_history_id'), table_name='grade_history')
    op.drop_table('grade_history')

    # Drop grades table
    op.drop_index(op.f('ix_grades_id'), table_name='grades')
    op.drop_table('grades')