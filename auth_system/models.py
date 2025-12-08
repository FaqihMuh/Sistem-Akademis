from sqlalchemy import Column, Integer, String, DateTime
from pmb_system.database import Base
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    DOSEN = "DOSEN"
    MAHASISWA = "MAHASISWA"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # ADMIN, DOSEN, MAHASISWA
    nim = Column(String, nullable=True)  # Used only if role = "MAHASISWA"
    kode_dosen = Column(String, nullable=True)  # Used only if role = "DOSEN"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)