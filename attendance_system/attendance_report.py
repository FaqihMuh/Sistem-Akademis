from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from pmb_system.database import get_db
from typing import List, Dict, Any
import csv
import io
from fastapi.responses import StreamingResponse
from datetime import datetime
from pydantic import BaseModel

from attendance_system.models import AttendanceSession, AttendanceRecord
from schedule_system.models import JadwalKelas, JadwalMahasiswa, Dosen
from pmb_system.models import CalonMahasiswa
from krs_system.models import Matakuliah, KRS, KRSDetail


router = APIRouter(prefix="/api/attendance", tags=["attendance-report"])


class AttendanceReportStudent(BaseModel):
    nim: str
    nama: str
    hadir: int
    total_sesi: int
    persentase: float
    status: str


class AttendanceReportResponse(BaseModel):
    schedule_id: int
    course_code: str
    course_name: str
    lecturer_name: str
    total_students: int
    students: List[AttendanceReportStudent]


class EarlyWarningInsight(BaseModel):
    schedule_id: int
    class_attendance_avg: float
    insights: List[str]
    student_warnings: List[Dict[str, Any]]


@router.get("/report/schedule/{schedule_id}")
def get_attendance_report_by_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attendance report for a specific schedule
    Returns:
    - List of students with attendance details
    - Total sessions
    - Attendance percentage
    - Status (AMAN/PERINGATAN/KRITIS)
    """
    try:
        # Get schedule details
        schedule = db.query(JadwalKelas).filter(JadwalKelas.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Get course details
        course = db.query(Matakuliah).filter(Matakuliah.kode == schedule.kode_mk).first()
        course_name = course.nama if course else "Unknown Course"

        # Get all attendance sessions for this schedule
        attendance_sessions = db.query(AttendanceSession).filter(
            AttendanceSession.schedule_id == schedule_id
        ).all()

        total_sessions = len(attendance_sessions)

        if total_sessions == 0:
            # If no sessions exist, return empty report
            return {
                "success": True,
                "data": {
                    "schedule_id": schedule_id,
                    "course_code": schedule.kode_mk,
                    "course_name": course_name,
                    "lecturer_name": db.query(Dosen).filter(Dosen.id == schedule.dosen_id).first().nama if schedule.dosen_id else "Unknown",
                    "total_students": 0,
                    "total_sessions": 0,
                    "students": []
                }
            }
        
        # Get all students registered for this course by finding KRS entries
        # First, get the matakuliah_id for this schedule
        matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == schedule.kode_mk).first()

        if not matakuliah:
            # If no course found, return empty report
            lecturer = db.query(Dosen).filter(Dosen.id == schedule.dosen_id).first()
            lecturer_name = lecturer.nama if lecturer else "Unknown Lecturer"

            return {
                "success": True,
                "data": {
                    "schedule_id": schedule_id,
                    "course_code": schedule.kode_mk,
                    "course_name": course_name,
                    "lecturer_name": lecturer_name,
                    "total_students": 0,
                    "total_sessions": 0,
                    "students": []
                }
            }

        # Find all KRS details that contain this matakuliah and get the associated students
        krs_details_with_students = db.query(KRS.nim).join(
            KRSDetail, KRS.id == KRSDetail.krs_id
        ).filter(
            KRSDetail.matakuliah_id == matakuliah.id
        ).distinct().all()

        # Extract unique NIMs from the query result
        student_nims = [result.nim for result in krs_details_with_students]

        students_data = []

        for nim in student_nims:
            # Count how many sessions this student attended for this schedule
            attended_sessions = db.query(AttendanceRecord).join(
                AttendanceSession, AttendanceRecord.attendance_session_id == AttendanceSession.id
            ).filter(
                AttendanceSession.schedule_id == schedule_id,
                AttendanceRecord.nim == nim
            ).count()

            # Calculate percentage
            if total_sessions > 0:
                percentage = round((attended_sessions / total_sessions) * 100, 2)
            else:
                percentage = 0.0

            # Determine status based on percentage
            if percentage >= 75:
                status = "AMAN"
            elif percentage >= 50:
                status = "PERINGATAN"
            else:
                status = "KRITIS"

            # Get student name
            student = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == nim).first()
            student_name = student.nama_lengkap if student else f"Student {nim}"

            students_data.append({
                "nim": nim,
                "nama": student_name,
                "hadir": attended_sessions,
                "total_sesi": total_sessions,
                "persentase": percentage,
                "status": status
            })

        # Get lecturer name
        lecturer = db.query(Dosen).filter(Dosen.id == schedule.dosen_id).first()
        lecturer_name = lecturer.nama if lecturer else "Unknown Lecturer"

        return {
            "success": True,
            "data": {
                "schedule_id": schedule_id,
                "course_code": schedule.kode_mk,
                "course_name": course_name,
                "lecturer_name": lecturer_name,
                "total_students": len(students_data),
                "total_sessions": total_sessions,
                "students": students_data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/report/schedule/{schedule_id}/export/csv")
def export_attendance_report_csv(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    Export attendance report to CSV format
    """
    try:
        # Get the attendance report data
        report_response = get_attendance_report_by_schedule(schedule_id, db)
        report_data = report_response["data"]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["NIM", "Nama", "Hadir", "Total Sesi", "Persentase"])
        
        # Write data rows
        for student in report_data["students"]:
            writer.writerow([
                student["nim"],
                student["nama"],
                student["hadir"],
                student["total_sesi"],
                f"{student['persentase']}%"
            ])
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Create streaming response
        response = StreamingResponse(io.StringIO(csv_content), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=attendance_report_schedule_{schedule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/insights/schedule/{schedule_id}")
def get_early_warning_insights(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    Get early warning insights for a specific schedule
    Returns:
    - Class average attendance
    - General insights about the class
    - Individual student warnings
    """
    try:
        # Get schedule details
        schedule = db.query(JadwalKelas).filter(JadwalKelas.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Get course details
        course = db.query(Matakuliah).filter(Matakuliah.kode == schedule.kode_mk).first()
        course_name = course.nama if course else "Unknown Course"

        # Get all attendance sessions for this schedule
        attendance_sessions = db.query(AttendanceSession).filter(
            AttendanceSession.schedule_id == schedule_id
        ).all()

        total_sessions = len(attendance_sessions)

        if total_sessions == 0:
            return {
                "success": True,
                "data": {
                    "schedule_id": schedule_id,
                    "class_attendance_avg": 0.0,
                    "insights": [f"Belum ada sesi presensi yang dibuat untuk jadwal {course_name}."],
                    "student_warnings": []
                }
            }
        
        # Get all students registered for this course by finding KRS entries
        # First, get the matakuliah_id for this schedule
        matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == schedule.kode_mk).first()

        if not matakuliah:
            return {
                "success": True,
                "data": {
                    "schedule_id": schedule_id,
                    "class_attendance_avg": 0.0,
                    "insights": [f"Tidak ada mata kuliah ditemukan untuk jadwal ini ({course_name})."],
                    "student_warnings": []
                }
            }

        # Find all KRS details that contain this matakuliah and get the associated students
        krs_details_with_students = db.query(KRS.nim).join(
            KRSDetail, KRS.id == KRSDetail.krs_id
        ).filter(
            KRSDetail.matakuliah_id == matakuliah.id
        ).distinct().all()

        # Extract unique NIMs from the query result
        student_nims = [result.nim for result in krs_details_with_students]

        if not student_nims:
            return {
                "success": True,
                "data": {
                    "schedule_id": schedule_id,
                    "class_attendance_avg": 0.0,
                    "insights": ["Tidak ada mahasiswa terdaftar untuk mata kuliah ini."],
                    "student_warnings": []
                }
            }

        total_attendance_percentages = 0
        student_warnings = []

        for nim in student_nims:
            # Count how many sessions this student attended
            attended_sessions = db.query(AttendanceRecord).join(
                AttendanceSession, AttendanceRecord.attendance_session_id == AttendanceSession.id
            ).filter(
                AttendanceSession.schedule_id == schedule_id,
                AttendanceRecord.nim == nim
            ).count()

            # Calculate percentage
            if total_sessions > 0:
                percentage = round((attended_sessions / total_sessions) * 100, 2)
            else:
                percentage = 0.0

            total_attendance_percentages += percentage

            # Determine if student needs warning
            if percentage < 75:
                student = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == nim).first()
                student_name = student.nama_lengkap if student else "Unknown Student"

                if percentage < 50:
                    warning_message = f"Mahasiswa {student_name} ({nim}) sering tidak hadir, disarankan konseling akademik."
                    warning_level = "KRITIS"
                elif percentage < 75:
                    warning_message = f"Mahasiswa {student_name} ({nim}) mulai sering absen, disarankan pemantauan."
                    warning_level = "PERINGATAN"

                student_warnings.append({
                    "nim": nim,
                    "nama": student_name,
                    "persentase": percentage,
                    "warning_message": warning_message,
                    "warning_level": warning_level
                })

        # Calculate class average
        class_attendance_avg = round(total_attendance_percentages / len(student_nims), 2) if student_nims else 0.0
        
        # Generate class-level insights
        insights = []
        
        if class_attendance_avg < 60:
            insights.append("Tingkat kehadiran kelas rendah, pertimbangkan evaluasi metode pengajaran atau reschedule.")
        elif class_attendance_avg < 75:
            insights.append("Tingkat kehadiran kelas perlu ditingkatkan.")
        else:
            insights.append("Tingkat kehadiran kelas baik.")
        
        # Add insight about number of students with warnings
        warning_count = len([w for w in student_warnings if w["warning_level"] in ["PERINGATAN", "KRITIS"]])
        if warning_count > 0:
            insights.append(f"Terdapat {warning_count} mahasiswa yang memerlukan perhatian khusus terkait kehadiran.")
        
        return {
            "success": True,
            "data": {
                "schedule_id": schedule_id,
                "class_attendance_avg": class_attendance_avg,
                "insights": insights,
                "student_warnings": student_warnings
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")