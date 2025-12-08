from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pmb_system.database import Base  # Using the same Base as PMB system
from krs_system.enums import KRSStatusEnum  # Using shared enum


class Matakuliah(Base):
    __tablename__ = 'matakuliah'

    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(10), unique=True, nullable=False)  # Course code
    nama = Column(String(255), nullable=False)  # Course name
    sks = Column(Integer, nullable=False)  # Credit hours
    semester = Column(Integer, nullable=False)  # Semester (1-8 typically)
    hari = Column(String(20), nullable=False)  # Day of week (Senin, Selasa, etc or Monday, Tuesday)
    jam_mulai = Column(Time, nullable=False)  # Start time
    jam_selesai = Column(Time, nullable=False)  # End time
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    krs_details = relationship("KRSDetail", back_populates="matakuliah")
    # jadwal_kelas = relationship("schedule_system.models.JadwalKelas", back_populates="matakuliah")  # Back reference from schedule system
    prerequisites = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.matakuliah_id",
        back_populates="matakuliah"
    )
    prerequisite_for = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.prerequisite_id",
        back_populates="prerequisite_matakuliah"
    )
    # Removed grades relationship to avoid circular import issues during initialization
    # grades = relationship("grades_system.models.Grade", back_populates="matakuliah")


class Prerequisite(Base):
    __tablename__ = 'prerequisite'
    
    id = Column(Integer, primary_key=True, index=True)
    matakuliah_id = Column(Integer, ForeignKey('matakuliah.id'), nullable=False)
    prerequisite_id = Column(Integer, ForeignKey('matakuliah.id'), nullable=False)
    
    # Relationships
    matakuliah = relationship("Matakuliah", foreign_keys=[matakuliah_id], back_populates="prerequisites")
    prerequisite_matakuliah = relationship("Matakuliah", foreign_keys=[prerequisite_id], back_populates="prerequisite_for")
    
    # Ensure a course cannot be a prerequisite of itself
    __table_args__ = (
        # Additional constraint would be added in migration
    )


class KRS(Base):
    __tablename__ = 'krs'
    
    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String(20), nullable=False)  # Student ID
    semester = Column(String(10), nullable=False)  # Academic semester (e.g., "2023/2024-1")
    status = Column(SQLEnum(KRSStatusEnum), default=KRSStatusEnum.DRAFT, nullable=False)
    dosen_pa_id = Column(Integer, nullable=True)  # Advisor ID (nullable) - using integer instead of foreign key to avoid dependency
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    krs_details = relationship("KRSDetail", back_populates="krs", cascade="all, delete-orphan")
    # dosen_pa relationship is commented out to avoid potential import issues
    # dosen_pa = relationship("Dosen", back_populates="krs_list")  # Assuming Dosen model exists


class KRSDetail(Base):
    __tablename__ = 'krs_detail'
    
    id = Column(Integer, primary_key=True, index=True)
    krs_id = Column(Integer, ForeignKey('krs.id'), nullable=False)
    matakuliah_id = Column(Integer, ForeignKey('matakuliah.id'), nullable=False)
    
    # Relationships
    krs = relationship("KRS", back_populates="krs_details")
    matakuliah = relationship("Matakuliah", back_populates="krs_details")
    
    # Ensure no duplicate courses in the same KRS
    __table_args__ = (
        # Additional unique constraint would be added in migration
    )