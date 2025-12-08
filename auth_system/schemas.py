from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    DOSEN = "DOSEN"
    MAHASISWA = "MAHASISWA"


class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum  # ADMIN, DOSEN, MAHASISWA
    nim: Optional[str] = None  # Used only if role = "MAHASISWA"
    kode_dosen: Optional[str] = None  # Used only if role = "DOSEN"


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: RoleEnum
    nim: Optional[str] = None  # Provided if user is MAHASISWA
    kode_dosen: Optional[str] = None  # Provided if user is DOSEN


class MeResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum  # ADMIN, DOSEN, MAHASISWA
    nim: Optional[str] = None  # Provided if user is MAHASISWA
    kode_dosen: Optional[str] = None  # Provided if user is DOSEN
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None