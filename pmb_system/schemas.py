from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re
from enum import Enum

class JalurMasuk(str, Enum):
    SNBP = "SNBP"
    SNBT = "SNBT"
    MANDIRI = "Mandiri"

class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CalonMahasiswaBase(BaseModel):
    nama_lengkap: str
    email: EmailStr
    phone: str
    tanggal_lahir: datetime
    alamat: str
    program_studi_id: int
    jalur_masuk: JalurMasuk

    @field_validator('phone')
    @classmethod
    def validate_indonesian_phone(cls, v):
        # Validate Indonesian phone format (08... with 10-13 digits)
        clean_phone = v.replace(" ", "").replace("-", "")
        pattern = r'^08\d{8,11}$'  # 08 followed by 8-11 digits (total 10-13)
        if not re.match(pattern, clean_phone):
            raise ValueError('Phone number must start with 08 and have 10-13 digits total')
        return clean_phone

class CalonMahasiswaCreate(CalonMahasiswaBase):
    pass

class CalonMahasiswaResponse(CalonMahasiswaBase):
    id: int
    status: Status
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProgramStudiBase(BaseModel):
    kode: str
    nama: str
    fakultas: str

    @field_validator('kode')
    @classmethod
    def validate_kode_length(cls, v):
        if len(v) != 3:
            raise ValueError('Kode must be exactly 3 characters')
        return v

class ProgramStudiCreate(ProgramStudiBase):
    pass

class ProgramStudiResponse(ProgramStudiBase):
    id: int

    class Config:
        from_attributes = True