"""Initial migration for PMB system

Revision ID: 001_initial_pmb_schema
Revises: 
Create Date: 2025-10-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_pmb_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create program_studi table
    op.create_table('program_studi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kode', sa.String(length=3), nullable=False),
        sa.Column('nama', sa.String(length=255), nullable=False),
        sa.Column('fakultas', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("LENGTH(kode) = 3", name="check_kode_length")
    )

    # Create calon_mahasiswa table
    op.create_table('calon_mahasiswa',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nama_lengkap', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=15), nullable=False),
        sa.Column('tanggal_lahir', sa.DateTime(), nullable=False),
        sa.Column('alamat', sa.String(length=500), nullable=False),
        sa.Column('program_studi_id', sa.Integer(), nullable=False),
        sa.Column('jalur_masuk', postgresql.ENUM('SNBP', 'SNBT', 'MANDIRI', name='jalurmasukenum'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='statusenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['program_studi_id'], ['program_studi.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes
    op.create_index(op.f('ix_calon_mahasiswa_id'), 'calon_mahasiswa', ['id'], unique=False)
    op.create_index(op.f('ix_program_studi_id'), 'program_studi', ['id'], unique=False)
    
    # Add check constraints for PostgreSQL (after table creation)
    # Email format validation
    op.execute("ALTER TABLE calon_mahasiswa ADD CONSTRAINT check_valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,});")
    
    # Phone format validation for Indonesian numbers
    op.execute("ALTER TABLE calon_mahasiswa ADD CONSTRAINT check_indonesian_phone_format CHECK (phone ~ '^08[0-9]{8,11});")


def downgrade() -> None:
    # Drop check constraints for PostgreSQL
    op.execute("ALTER TABLE calon_mahasiswa DROP CONSTRAINT IF EXISTS check_valid_email;")
    op.execute("ALTER TABLE calon_mahasiswa DROP CONSTRAINT IF EXISTS check_indonesian_phone_format;")
    
    # Drop indexes
    op.drop_index(op.f('ix_program_studi_id'), table_name='program_studi')
    op.drop_index(op.f('ix_calon_mahasiswa_id'), table_name='calon_mahasiswa')
    
    # Drop tables
    op.drop_table('calon_mahasiswa')
    op.drop_table('program_studi')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS jalurmasukenum;")
    op.execute("DROP TYPE IF EXISTS statusenum;")