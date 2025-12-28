from sqlalchemy.orm import Session
from sqlalchemy import and_
from attendance_system.models import AttendanceSession, AttendanceRecord
from attendance_system.schemas import AttendanceSessionCreate, AttendanceSessionUpdate, AttendanceRecordCreate
from typing import Optional
import uuid
import secrets
import string


def generate_qr_token():
    """Generate a secure random QR token"""
    return secrets.token_urlsafe(32)


def create_or_update_attendance_session(db: Session, schedule_id: int, session_number: int):
    """Create or update an attendance session"""
    # Validate session number is between 1 and 16
    if not 1 <= session_number <= 16:
        raise ValueError("Session number must be between 1 and 16")

    # Check if attendance session already exists for this schedule and session number
    existing_session = db.query(AttendanceSession).filter(
        AttendanceSession.schedule_id == schedule_id,
        AttendanceSession.session_number == session_number
    ).first()

    if existing_session:
        # Update existing session
        existing_session.qr_token = generate_qr_token()
        existing_session.is_active = True
        db.commit()
        db.refresh(existing_session)
        return existing_session
    else:
        # Create new session
        qr_token = generate_qr_token()
        db_attendance_session = AttendanceSession(
            schedule_id=schedule_id,
            session_number=session_number,
            qr_token=qr_token,
            is_active=True
        )
        db.add(db_attendance_session)
        db.commit()
        db.refresh(db_attendance_session)
        return db_attendance_session


def get_attendance_session_by_qr_token(db: Session, qr_token: str):
    """Get attendance session by QR token"""
    return db.query(AttendanceSession).filter(
        AttendanceSession.qr_token == qr_token,
        AttendanceSession.is_active == True
    ).first()


def get_attendance_session(db: Session, session_id: int):
    return db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()


def update_attendance_session(db: Session, session_id: int, attendance_session_update: AttendanceSessionUpdate):
    db_session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if db_session:
        if attendance_session_update.is_active is not None:
            db_session.is_active = attendance_session_update.is_active
        db.commit()
        db.refresh(db_session)
    return db_session


def delete_attendance_session(db: Session, session_id: int):
    db_session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session


def create_attendance_record(db: Session, attendance_record: AttendanceRecordCreate):
    # Check if attendance record already exists for this session and student
    existing_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.attendance_session_id == attendance_record.attendance_session_id,
        AttendanceRecord.nim == attendance_record.nim
    ).first()

    if existing_record:
        raise ValueError("Student has already attended this session")

    db_attendance_record = AttendanceRecord(
        attendance_session_id=attendance_record.attendance_session_id,
        nim=attendance_record.nim
    )
    db.add(db_attendance_record)
    db.commit()
    db.refresh(db_attendance_record)
    return db_attendance_record


def get_attendance_record(db: Session, record_id: int):
    return db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()


def get_attendance_record_by_session_and_nim(db: Session, session_id: int, nim: str):
    return db.query(AttendanceRecord).filter(
        AttendanceRecord.attendance_session_id == session_id,
        AttendanceRecord.nim == nim
    ).first()


def record_attendance_from_qr(db: Session, qr_token: str, nim: str):
    """Record attendance using QR token"""
    # Find active attendance session with the QR token
    attendance_session = get_attendance_session_by_qr_token(db, qr_token)

    if not attendance_session:
        raise ValueError("Invalid or inactive QR token")

    # Check if student has already attended this session
    existing_record = get_attendance_record_by_session_and_nim(
        db,
        attendance_session.id,
        nim
    )

    if existing_record:
        raise ValueError("Student has already attended this session")

    # Create attendance record
    attendance_record = AttendanceRecord(
        attendance_session_id=attendance_session.id,
        nim=nim
    )
    db.add(attendance_record)
    db.commit()
    db.refresh(attendance_record)

    return attendance_record, attendance_session