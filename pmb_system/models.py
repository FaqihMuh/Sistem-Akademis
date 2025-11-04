from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint
import re
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class StatusEnum(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class JalurMasukEnum(PyEnum):
    SNBP = "SNBP"
    SNBT = "SNBT"
    MANDIRI = "Mandiri"

class ProgramStudi(Base):
    __tablename__ = 'program_studi'
    
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(3), nullable=False)  # 3 character code
    nama = Column(String(255), nullable=False)
    fakultas = Column(String(255), nullable=False)
    
    # Relationship to calon_mahasiswa
    calon_mahasiswa = relationship("CalonMahasiswa", back_populates="program_studi")
    
    # Check constraint for kode length
    __table_args__ = (
        CheckConstraint("LENGTH(kode) = 3", name="check_kode_length"),
    )
    
    def __init__(self, **kwargs):
        # Validate kode length
        kode = kwargs.get('kode')
        if kode and len(kode) != 3:
            raise ValueError("Kode must be exactly 3 characters")
        super().__init__(**kwargs)

class CalonMahasiswa(Base):
    __tablename__ = 'calon_mahasiswa'
    
    id = Column(Integer, primary_key=True, index=True)
    nama_lengkap = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)  # Unique constraint
    phone = Column(String(15), nullable=False)  # Phone number
    tanggal_lahir = Column(DateTime, nullable=False)
    alamat = Column(String(500), nullable=False)
    program_studi_id = Column(Integer, ForeignKey('program_studi.id'), nullable=False)
    jalur_masuk = Column(Enum(JalurMasukEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    approved_at = Column(DateTime, nullable=True)
    nim = Column(String(255), nullable=True)  # NIM column, default is NULL
    
    # Relationship to program_studi
    program_studi = relationship("ProgramStudi", back_populates="calon_mahasiswa")
    
    # Application-level validation only (database constraints vary by DB engine)
    # For PostgreSQL, use the migration file to add constraints
    # __table_args__ = (
    #     # For compatibility across different DB engines, we'll add constraints via migrations
    # )
    
    def __init__(self, **kwargs):
        # Validate email format
        email = kwargs.get('email')
        if email and not self.validate_email_format(email):
            raise ValueError("Email format is not valid")
        
        # Validate phone format
        phone = kwargs.get('phone')
        if phone and not self.validate_phone_format(phone):
            raise ValueError("Phone format is not valid for Indonesian numbers (08... with 10-13 digits)")
        
        super().__init__(**kwargs)
    
    @validates('kode')
    def validate_kode_length(self, key, kode):
        """Validate that kode is exactly 3 characters"""
        if kode and len(kode) != 3:
            raise ValueError("Kode must be exactly 3 characters")
        return kode
    
    @staticmethod
    def validate_email_format(email):
        """Validate email format"""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone_format(phone):
        """Validate Indonesian phone format (08... with 10-13 digits)"""
        # Remove any spaces or hyphens for validation
        clean_phone = phone.replace(" ", "").replace("-", "")
        pattern = r'^08\d{8,11}$'  # 08 followed by 8-11 digits (total 10-13)
        return re.match(pattern, clean_phone) is not None