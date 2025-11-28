"""Create jadwal_kelas, dosen, and ruang tables

Revision ID: 001_create_schedule_tables
Revises: 
Create Date: 2024-12-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime, Time
from sqlalchemy.sql import func


# revision identifiers
revision = '001_create_schedule_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dosen table
    op.create_table('dosen',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nip', sa.String(20), nullable=False),
        sa.Column('nama', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('program_studi', sa.String(100), nullable=True),
        sa.Column('created_at', DateTime, server_default=func.now()),
        sa.Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nip'),
        sa.UniqueConstraint('email')
    )

    # Create ruang table
    op.create_table('ruang',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kode', sa.String(20), nullable=False),
        sa.Column('nama', sa.String(100), nullable=False),
        sa.Column('kapasitas', sa.Integer(), nullable=False),
        sa.Column('jenis', sa.String(50), nullable=False),
        sa.Column('created_at', DateTime, server_default=func.now()),
        sa.Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kode')
    )

    # Create jadwal_kelas table
    op.create_table('jadwal_kelas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kode_mk', sa.String(10), nullable=False),
        sa.Column('dosen_id', sa.Integer(), nullable=False),
        sa.Column('ruang_id', sa.Integer(), nullable=False),
        sa.Column('semester', sa.String(20), nullable=False),
        sa.Column('hari', sa.String(20), nullable=False),
        sa.Column('jam_mulai', Time, nullable=False),
        sa.Column('jam_selesai', Time, nullable=False),
        sa.Column('kapasitas_kelas', sa.Integer(), nullable=False),
        sa.Column('kelas', sa.String(10), nullable=True),
        sa.Column('created_at', DateTime, server_default=func.now()),
        sa.Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dosen_id'], ['dosen.id'], ),
        sa.ForeignKeyConstraint(['ruang_id'], ['ruang.id'], )
    )

    # Create jadwal_mahasiswa table 
    op.create_table('jadwal_mahasiswa',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nim', sa.String(20), nullable=False),
        sa.Column('jadwal_kelas_id', sa.Integer(), nullable=False),
        sa.Column('semester', sa.String(20), nullable=False),
        sa.Column('status_kehadiran', sa.String(20), server_default='belum_hadir'),
        sa.Column('created_at', DateTime, server_default=func.now()),
        sa.Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['jadwal_kelas_id'], ['jadwal_kelas.id'], )
    )

    # Create indexes for better performance
    op.create_index('idx_jadwal_kelas_hari', 'jadwal_kelas', ['hari'])
    op.create_index('idx_jadwal_kelas_semester', 'jadwal_kelas', ['semester'])
    op.create_index('idx_jadwal_kelas_dosen_id', 'jadwal_kelas', ['dosen_id'])
    op.create_index('idx_jadwal_kelas_ruang_id', 'jadwal_kelas', ['ruang_id'])
    op.create_index('idx_jadwal_kelas_kode_mk', 'jadwal_kelas', ['kode_mk'])
    op.create_index('idx_jadwal_mahasiswa_nim', 'jadwal_mahasiswa', ['nim'])
    op.create_index('idx_jadwal_mahasiswa_kelas_id', 'jadwal_mahasiswa', ['jadwal_kelas_id'])


def downgrade() -> None:
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table('jadwal_mahasiswa')
    op.drop_table('jadwal_kelas')
    op.drop_table('ruang')
    op.drop_table('dosen')