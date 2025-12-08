from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GradeBase(BaseModel):
    nim: str
    matakuliah_id: int
    semester: str
    nilai_huruf: str
    sks: int
    dosen_id: int
    presensi: Optional[float] = 100.0


class GradeCreate(GradeBase):
    pass


class GradeUpdate(BaseModel):
    nilai_huruf: Optional[str] = None
    dosen_id: Optional[int] = None
    presensi: Optional[float] = None
    reason: str  # Required for audit trail


class GradeResponse(GradeBase):
    id: int
    nilai_angka: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradeHistoryBase(BaseModel):
    grade_id: int
    old_value: str
    new_value: str
    changed_by: str
    reason: Optional[str] = None


class GradeHistoryCreate(GradeHistoryBase):
    pass


class GradeHistoryResponse(GradeHistoryBase):
    id: int
    changed_at: datetime

    class Config:
        from_attributes = True


# Response for student grades with course information
class StudentGradeResponse(BaseModel):
    id: int
    kode_mk: str
    nama_mk: str
    sks: int
    nilai_huruf: str
    nilai_angka: float
    semester: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Response for course grades with student information
class CourseGradeResponse(BaseModel):
    id: int
    nim: str
    nama_mahasiswa: str
    sks: int
    nilai_huruf: str
    nilai_angka: float
    presensi: float
    created_at: datetime
    
    class Config:
        from_attributes = True