from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pmb_system.database import Base


class Grade(Base):
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String(20), nullable=False)  # FK to mahasiswa (without constraint to avoid circular refs for now)
    matakuliah_id = Column(Integer, nullable=False)  # FK to matakuliah (without constraint to avoid circular refs for now)
    semester = Column(String(20), nullable=False)  # Semester string
    nilai_huruf = Column(String(2), nullable=False)  # A/B/C/D/E
    nilai_angka = Column(Float, nullable=False)  # 4.0/3.0/2.0/1.0/0.0
    sks = Column(Integer, nullable=False)  # SKS from matakuliah
    dosen_id = Column(Integer, nullable=False)  # FK to dosen (without constraint to avoid circular refs for now)
    presensi = Column(Float, default=100.0)  # Placeholder for attendance percentage
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships - removed back_populates to avoid circular import issues during initialization
    # These can be added back later if needed after model refactoring
    # mahasiswa = relationship("pmb_system.models.CalonMahasiswa", back_populates="grades")
    # matakuliah = relationship("krs_system.models.Matakuliah", back_populates="grades")
    # dosen = relationship("schedule_system.models.Dosen", back_populates="grades")
    history = relationship("GradeHistory", back_populates="grade")


class GradeHistory(Base):
    __tablename__ = 'grade_history'

    id = Column(Integer, primary_key=True, index=True)
    grade_id = Column(Integer, ForeignKey('grades.id'), nullable=False)  # FK to grades.id
    old_value = Column(String(50), nullable=False)  # Previous value (huruf/angka)
    new_value = Column(String(50), nullable=False)  # New value (huruf/angka)
    changed_by = Column(String(255), nullable=False)  # Username of the person who changed
    changed_at = Column(DateTime, default=func.now())  # Timestamp
    reason = Column(Text, nullable=True)  # Reason for the change

    # Relationships
    grade = relationship("Grade", back_populates="history")


# Add back-populates relationships to existing models
# This would need to be done in the actual models to avoid circular imports
# For now, we'll define them here as additional relationships
def add_grade_relationships():
    """
    Helper function to add grade relationships to existing models
    This should be called after all models are defined to avoid circular imports
    """
    # Add these relationships to existing models after they are fully loaded
    pass