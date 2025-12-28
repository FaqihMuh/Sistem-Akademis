from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AttendanceSessionBase(BaseModel):
    schedule_id: int
    session_number: int
    qr_token: str
    is_active: bool = False


class AttendanceSessionCreate(AttendanceSessionBase):
    pass


class AttendanceSessionUpdate(BaseModel):
    is_active: Optional[bool] = None


class AttendanceSession(AttendanceSessionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceRecordBase(BaseModel):
    attendance_session_id: int
    nim: str


class AttendanceRecordCreate(AttendanceRecordBase):
    pass


class AttendanceRecord(AttendanceRecordBase):
    id: int
    scanned_at: datetime

    class Config:
        from_attributes = True


class AttendanceScanRequest(BaseModel):
    qr_token: str
    nim: str