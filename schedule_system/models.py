from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Time, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from schedule_system.database import Base  # Using the same Base as the schedule system


class Ruang(Base):
    __tablename__ = 'ruang'
    
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(20), unique=True, nullable=False)  # Room code (e.g., "A101", "LabTI1")
    nama = Column(String(100), nullable=False)  # Room name
    kapasitas = Column(Integer, nullable=False)  # Capacity
    jenis = Column(String(50), nullable=False)  # Type (e.g., "Kelas", "Laboratorium", "Auditorium")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    jadwal_kelas = relationship("JadwalKelas", back_populates="ruang")


class Dosen(Base):
    __tablename__ = 'dosen'
    
    id = Column(Integer, primary_key=True, index=True)
    nip = Column(String(20), unique=True, nullable=False)  # NIP
    nama = Column(String(255), nullable=False)  # Name
    email = Column(String(255), unique=True, nullable=False)  # Email
    phone = Column(String(20), nullable=True)  # Phone number
    program_studi = Column(String(100), nullable=True)  # Department/Study Program
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    jadwal_kelas = relationship("JadwalKelas", back_populates="dosen")


class JadwalKelas(Base):
    __tablename__ = 'jadwal_kelas'
    
    id = Column(Integer, primary_key=True, index=True)
    kode_mk = Column(String(10), nullable=False)  # Course code
    dosen_id = Column(Integer, ForeignKey('dosen.id'), nullable=False)
    ruang_id = Column(Integer, ForeignKey('ruang.id'), nullable=False)
    semester = Column(String(20), nullable=False)  # Academic semester (e.g., "2023/2024-1")
    hari = Column(String(20), nullable=False)  # Day of week (Senin, Selasa, etc)
    jam_mulai = Column(Time, nullable=False)  # Start time
    jam_selesai = Column(Time, nullable=False)  # End time
    kapasitas_kelas = Column(Integer, nullable=False)  # Max number of students for this class
    kelas = Column(String(10), nullable=True)  # Class section (e.g., "A", "B")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    dosen = relationship("Dosen", back_populates="jadwal_kelas")
    ruang = relationship("Ruang", back_populates="jadwal_kelas")
    jadwal_mahasiswa = relationship("JadwalMahasiswa", back_populates="jadwal_kelas", cascade="all, delete-orphan")


class JadwalMahasiswa(Base):
    __tablename__ = 'jadwal_mahasiswa'
    
    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String(20), nullable=False)  # Student ID
    jadwal_kelas_id = Column(Integer, ForeignKey('jadwal_kelas.id'), nullable=False)
    semester = Column(String(20), nullable=False)  # Academic semester (e.g., "2023/2024-1")
    status_kehadiran = Column(String(20), default="belum_hadir")  # Attendance status
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Note: Removed direct relationship to CalonMahasiswa to avoid circular imports in tests
    # Instead, we'll reference students by their NIM only
    jadwal_kelas = relationship("JadwalKelas", back_populates="jadwal_mahasiswa")