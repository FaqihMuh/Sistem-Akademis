from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from pmb_system.database import Base


class AttendanceSession(Base):
    __tablename__ = "attendance_session"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, nullable=False)  # Foreign key reference as integer without constraint
    session_number = Column(Integer, nullable=False)  # 1 s.d. 16
    qr_token = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AttendanceRecord(Base):
    __tablename__ = "attendance_record"

    id = Column(Integer, primary_key=True, index=True)
    attendance_session_id = Column(Integer, nullable=False)  # Foreign key reference as integer without constraint
    nim = Column(String, nullable=False)  # Changed to not use FK constraint to avoid circular import
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())