from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pmb_system.database import get_db
from attendance_system.schemas import AttendanceSessionCreate
from attendance_system.services import create_or_update_attendance_session, record_attendance_from_qr
from attendance_system.models import AttendanceSession
from typing import Dict, Any, List
from pydantic import BaseModel
from .schemas import AttendanceScanRequest

class AttendanceSessionGenerateRequest(BaseModel):
    schedule_id: int
    session_number: int


router = APIRouter(prefix="/api/attendance", tags=["attendance"])



@router.post("/session/generate")
def generate_attendance_session(
    payload: AttendanceSessionGenerateRequest,
    db: Session = Depends(get_db)
):
    try:
        if not 1 <= payload.session_number <= 16:
            raise HTTPException(
                status_code=400,
                detail="Session number must be between 1 and 16"
            )

        attendance_session = create_or_update_attendance_session(
            db,
            payload.schedule_id,
            payload.session_number
        )

        return {
            "success": True,
            "message": "Attendance session generated successfully",
            "data": {
                "id": attendance_session.id,
                "schedule_id": attendance_session.schedule_id,
                "session_number": attendance_session.session_number,
                "qr_token": attendance_session.qr_token,
                "is_active": attendance_session.is_active,
                "created_at": attendance_session.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/schedule/{schedule_id}")
def get_attendance_sessions_by_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attendance sessions for a specific schedule
    """
    try:
        attendance_sessions = db.query(AttendanceSession).filter(
            AttendanceSession.schedule_id == schedule_id
        ).all()

        return {
            "success": True,
            "data": [
                {
                    "id": session.id,
                    "schedule_id": session.schedule_id,
                    "session_number": session.session_number,
                    "qr_token": session.qr_token,
                    "is_active": session.is_active,
                    "created_at": session.created_at
                }
                for session in attendance_sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# @router.post("/scan")
# def scan_attendance(
#     qr_token: str,
#     nim: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Scan QR code for attendance
#     - For students to record their attendance using QR token
#     - Prevents duplicate attendance
#     """
#     try:
#         attendance_record, attendance_session = record_attendance_from_qr(db, qr_token, nim)

#         return {
#             "success": True,
#             "message": "Attendance recorded successfully",
#             "data": {
#                 "attendance_record_id": attendance_record.id,
#                 "attendance_session_id": attendance_session.id,
#                 "schedule_id": attendance_session.schedule_id,
#                 "session_number": attendance_session.session_number,
#                 "nim": attendance_record.nim,
#                 "scanned_at": attendance_record.scanned_at
#             }
#         }
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/scan")
def scan_attendance(
    payload: AttendanceScanRequest,
    db: Session = Depends(get_db)
):
    try:
        attendance_record, attendance_session = record_attendance_from_qr(
            db,
            payload.qr_token,
            payload.nim
        )

        return {
            "success": True,
            "message": "Attendance recorded successfully",
            "data": {
                "attendance_record_id": attendance_record.id,
                "attendance_session_id": attendance_session.id,
                "schedule_id": attendance_session.schedule_id,
                "session_number": attendance_session.session_number,
                "nim": attendance_record.nim,
                "scanned_at": attendance_record.scanned_at
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )