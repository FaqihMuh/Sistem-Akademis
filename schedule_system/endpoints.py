"""
Schedule System FastAPI Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import time, datetime
from schedule_system.models import JadwalKelas, Ruang
from pmb_system.models import CalonMahasiswa, StatusEnum  # Importing PMB model to validate NIM
from krs_system.models import Matakuliah  # Importing KRS model for course validation
from schedule_system.database import get_db  # Use the database session dependency
from schedule_system.services import (
    create_schedule as create_schedule_service,
    update_schedule as update_schedule_service,
    delete_schedule as delete_schedule_service,
    detect_schedule_conflicts,
    check_capacity,
    invalidate_affected_krs
)
from schedule_system.models import JadwalKelas


router = APIRouter(tags=["Schedule"])


# Pydantic models for request/response
from pydantic import BaseModel
from typing import Optional, List


class JadwalKelasCreate(BaseModel):
    kode_mk: str
    dosen_id: int
    ruang_id: int
    semester: str
    hari: str
    jam_mulai: time
    jam_selesai: time
    kapasitas_kelas: int
    kelas: Optional[str] = None


class JadwalKelasUpdate(BaseModel):
    kode_mk: Optional[str] = None
    dosen_id: Optional[int] = None
    ruang_id: Optional[int] = None
    semester: Optional[str] = None
    hari: Optional[str] = None
    jam_mulai: Optional[time] = None
    jam_selesai: Optional[time] = None
    kapasitas_kelas: Optional[int] = None
    kelas: Optional[str] = None


class DosenResponse(BaseModel):
    id: int
    nip: str
    nama: str
    email: str
    phone: Optional[str] = None
    program_studi: Optional[str] = None
    kode_dosen: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RuangResponse(BaseModel):
    id: int
    kode: str
    nama: str
    kapasitas: int
    jenis: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class JadwalKelasResponse(BaseModel):
    id: int
    kode_mk: str
    dosen_id: int
    ruang_id: int
    semester: str
    hari: str
    jam_mulai: time
    jam_selesai: time
    kapasitas_kelas: int
    kelas: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    # Include related objects
    dosen: Optional['DosenResponse'] = None
    ruang: Optional['RuangResponse'] = None

    model_config = {"from_attributes": True}


class JadwalConflictResponse(BaseModel):
    type: str  # "room_conflict" | "lecturer_conflict" | "time_overlap"
    schedule_1: dict
    schedule_2: dict


class RuangResponse(BaseModel):
    id: int
    kode: str
    nama: str
    kapasitas: int
    jenis: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ScheduleSuggestionResponse(BaseModel):
    """Response model for schedule suggestions"""
    hari: str
    jam_mulai: str
    jam_selesai: str
    ruang_id: int
    reason: str


class ScheduleConflictWithError(BaseModel):
    """Response model for schedule conflicts with suggestions"""
    detail: str
    conflicts: Optional[List[dict]] = None
    suggestions: Optional[List[ScheduleSuggestionResponse]] = None


# 1. POST /create
@router.post("/create", response_model=JadwalKelasResponse,
             summary="Create a new schedule",
             description="Create a new class schedule. If the schedule causes conflicts with existing schedules, the system will return conflict details along with up to 3 alternative time slots that would not cause conflicts.")
def create_schedule_endpoint(
    schedule: JadwalKelasCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new schedule
    """
    try:
        created_schedule = create_schedule_service(
            kode_mk=schedule.kode_mk,
            dosen_id=schedule.dosen_id,
            ruang_id=schedule.ruang_id,
            semester=schedule.semester,
            hari=schedule.hari,
            jam_mulai=schedule.jam_mulai,
            jam_selesai=schedule.jam_selesai,
            kapasitas_kelas=schedule.kapasitas_kelas,
            kelas=schedule.kelas,
            db=db
        )
        return created_schedule
    except ValueError as e:
        # Check if this is a structured error containing conflict details and suggestions
        error_str = str(e)
        if "'conflict_details':" in error_str and "'suggestions':" in error_str:
            # Attempt to parse the structured error containing both conflicts and suggestions
            import ast
            try:
                error_data = ast.literal_eval(error_str)
                if isinstance(error_data, dict) and "conflict_details" in error_data:
                    conflict_response = {
                        "detail": "Schedule conflict detected",
                        "conflicts": error_data["conflict_details"],
                        "suggestions": error_data["suggestions"]
                    }
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=conflict_response
                    )
            except (ValueError, SyntaxError):
                # If parsing fails, fall back to simple error
                pass

        # For all other ValueError cases
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 2. PUT /{id}/update
@router.put("/{id}/update", response_model=JadwalKelasResponse,
            summary="Update an existing schedule",
            description="Update an existing class schedule. If the updated schedule causes conflicts with existing schedules, the system will return conflict details along with up to 3 alternative time slots that would not cause conflicts.")
def update_schedule_endpoint(
    id: int,
    schedule: JadwalKelasUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing schedule
    """
    try:
        updated_schedule = update_schedule_service(
            schedule_id=id,
            kode_mk=schedule.kode_mk,
            dosen_id=schedule.dosen_id,
            ruang_id=schedule.ruang_id,
            semester=schedule.semester,
            hari=schedule.hari,
            jam_mulai=schedule.jam_mulai,
            jam_selesai=schedule.jam_selesai,
            kapasitas_kelas=schedule.kapasitas_kelas,
            kelas=schedule.kelas,
            db=db
        )
        return updated_schedule
    except ValueError as e:
        # Check if this is a structured error containing conflict details and suggestions
        error_str = str(e)
        if "'conflict_details':" in error_str and "'suggestions':" in error_str:
            # Attempt to parse the structured error containing both conflicts and suggestions
            import ast
            try:
                error_data = ast.literal_eval(error_str)
                if isinstance(error_data, dict) and "conflict_details" in error_data:
                    conflict_response = {
                        "detail": "Schedule conflict detected",
                        "conflicts": error_data["conflict_details"],
                        "suggestions": error_data["suggestions"]
                    }
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=conflict_response
                    )
            except (ValueError, SyntaxError):
                # If parsing fails, fall back to simple error
                pass

        # For all other ValueError cases
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 3. DELETE /{id}/delete
@router.delete("/{id}/delete", response_model=dict,
               summary="Delete a schedule",
               description="Delete an existing schedule by its ID.")
def delete_schedule_endpoint(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a schedule
    """
    try:
        success = delete_schedule_service(
            schedule_id=id,
            db=db
        )
        if success:
            return {"message": f"Schedule with ID {id} deleted successfully", "success": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete schedule with ID {id}"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 4. GET /conflicts
@router.get("/conflicts", response_model=List[JadwalConflictResponse],
            summary="Get all schedule conflicts",
            description="Retrieve all existing schedule conflicts in the system including room conflicts, lecturer conflicts, and time overlaps.")
def get_schedule_conflicts(
    db: Session = Depends(get_db)
):
    """
    Get all schedule conflicts
    """
    # Get all schedules to check for conflicts
    all_schedules = db.query(JadwalKelas).all()

    # Convert schedules to the format expected by detect_schedule_conflicts
    schedule_list = []
    for schedule in all_schedules:
        schedule_list.append({
            'id': schedule.id,
            'hari': schedule.hari,
            'jam_mulai': schedule.jam_mulai,
            'jam_selesai': schedule.jam_selesai,
            'ruangan_id': schedule.ruang_id,
            'dosen_id': schedule.dosen_id
        })

    conflicts = detect_schedule_conflicts(schedule_list)

    # Format conflicts for response
    conflict_responses = []
    for conflict in conflicts:
        conflict_responses.append(JadwalConflictResponse(
            type=conflict.type,
            schedule_1=conflict.schedule_1,
            schedule_2=conflict.schedule_2
        ))

    return conflict_responses


# 5. GET /rooms
@router.get("/rooms", response_model=List[RuangResponse],
            summary="Get all rooms",
            description="Retrieve all available rooms in the system including their capacity and type.")
def get_all_rooms(
    db: Session = Depends(get_db)
):
    """
    Get all rooms
    """
    rooms = db.query(Ruang).all()
    return [RuangResponse.from_orm(room) for room in rooms]


# 6. GET /{id}
@router.get("/{id}", response_model=JadwalKelasResponse,
            summary="Get schedule by ID",
            description="Retrieve a specific schedule by its ID.")
def get_schedule_by_id(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Get a schedule by ID
    """
    schedule = db.query(JadwalKelas).filter(JadwalKelas.id == id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID {id} not found"
        )

    return schedule


# 7. POST /suggest
from schedule_system.ai_rescheduler import generate_schedule_alternatives


@router.post("/suggest", response_model=List[ScheduleSuggestionResponse],
             summary="Suggest alternative schedules",
             description="Generate alternative time slots for a potential schedule that would cause conflicts. This endpoint suggests up to 3 alternative time slots that would not cause conflicts based on lecturer availability, room availability, and room capacity.")
def suggest_alternative_schedules(
    schedule: JadwalKelasCreate,
    db: Session = Depends(get_db)
):
    """
    Suggest alternative schedules for a conflicting schedule

    This endpoint generates 3 alternative time slots that would not cause conflicts
    based on lecturer availability, room availability, and room capacity.
    """
    try:
        suggestions = generate_schedule_alternatives(
            kode_mk=schedule.kode_mk,
            dosen_id=schedule.dosen_id,
            ruang_id=schedule.ruang_id,
            hari=schedule.hari,
            jam_mulai=schedule.jam_mulai,
            jam_selesai=schedule.jam_selesai,
            kapasitas_kelas=schedule.kapasitas_kelas,
            semester=schedule.semester,
            db=db
        )
        return suggestions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating suggestions: {str(e)}"
        )


# 8. GET /{id}/suggest
@router.get("/{id}/suggest", response_model=List[ScheduleSuggestionResponse],
            summary="Suggest alternatives for existing schedule",
            description="Generate alternative time slots for an existing schedule that may cause conflicts. This endpoint suggests up to 3 alternative time slots for a specific schedule ID based on lecturer availability, room availability, and room capacity.")
def suggest_alternative_schedules_by_id(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Suggest alternative schedules for an existing schedule that causes conflicts

    This endpoint generates 3 alternative time slots for an existing schedule
    based on lecturer availability, room availability, and room capacity.
    """
    try:
        # Get the existing schedule
        schedule = db.query(JadwalKelas).filter(JadwalKelas.id == id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule with ID {id} not found"
            )

        suggestions = generate_schedule_alternatives(
            kode_mk=schedule.kode_mk,
            dosen_id=schedule.dosen_id,
            ruang_id=schedule.ruang_id,
            hari=schedule.hari,
            jam_mulai=schedule.jam_mulai,
            jam_selesai=schedule.jam_selesai,
            kapasitas_kelas=schedule.kapasitas_kelas,
            semester=schedule.semester,
            db=db
        )
        return suggestions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating suggestions: {str(e)}"
        )


# # 9. GET /student/{nim}
# @router.get("/student/{nim}", response_model=List[JadwalKelasResponse],
#             summary="Get schedule for a specific student",
#             description="Retrieve all class schedules for a specific student by their NIM.")
# def get_student_schedule(
#     nim: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get schedule for a specific student by NIM
#     """
#     # Import the required models
#     from schedule_system.models import JadwalMahasiswa, JadwalKelas
#     from pmb_system.models import CalonMahasiswa, StatusEnum

#     # Validate that the student exists in PMB system with the given NIM
#     student = db.query(CalonMahasiswa).filter(
#         CalonMahasiswa.nim == nim
#     ).first()

#     if not student:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan di sistem PMB"
#         )

#     # Additionally, ensure the student's status is approved
#     if student.status != StatusEnum.APPROVED:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Mahasiswa dengan NIM {nim} belum disetujui atau tidak memiliki status yang valid"
#         )

#     # Get all schedule IDs for this student
#     student_schedule_registrations = db.query(JadwalMahasiswa).filter(JadwalMahasiswa.nim == nim).all()

#     if not student_schedule_registrations:
#         # Return empty list if no schedules registered
#         return []

#     # Get the actual schedules
#     schedule_ids = [reg.jadwal_kelas_id for reg in student_schedule_registrations]
#     schedules = db.query(JadwalKelas).filter(JadwalKelas.id.in_(schedule_ids)).all()

#     return schedules

# 9. GET /student/{nim}
@router.get("/student/{nim}", response_model=List[JadwalKelasResponse],
            summary="Get schedule for a specific student",
            description="Retrieve all class schedules for a specific student by their NIM.")
def get_student_schedule(
    nim: str,
    db: Session = Depends(get_db)
):
    """
    Get schedule for a specific student by NIM
    """
    # Import the required models
    from schedule_system.models import JadwalMahasiswa, JadwalKelas
    from pmb_system.models import CalonMahasiswa, StatusEnum
    from krs_system.models import KRS, KRSDetail, Matakuliah

    # Validate that the student exists in PMB system with the given NIM
    student = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim == nim
    ).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan di sistem PMB"
        )

    # Additionally, ensure the student's status is approved
    if student.status != StatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mahasiswa dengan NIM {nim} belum disetujui atau tidak memiliki status yang valid"
        )

    # Method 1: Try getting from JadwalMahasiswa (student schedule registration)
    student_schedule_registrations = db.query(JadwalMahasiswa).filter(JadwalMahasiswa.nim == nim).all()

    if student_schedule_registrations:
        # If student has registered directly with schedules, use that
        schedule_ids = [reg.jadwal_kelas_id for reg in student_schedule_registrations]
        schedules = db.query(JadwalKelas)\
            .options(joinedload(JadwalKelas.dosen))\
            .options(joinedload(JadwalKelas.ruang))\
            .filter(JadwalKelas.id.in_(schedule_ids)).all()
        return schedules
    else:
        # Method 2: If not in JadwalMahasiswa, get from KRS system
        krs = db.query(KRS).filter(KRS.nim == nim).first()

        if not krs:
            return []

        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()

        if not details:
            return []

        matakuliah_ids = [d.matakuliah_id for d in details]

        matakuliah = db.query(Matakuliah).filter(Matakuliah.id.in_(matakuliah_ids)).all()
        kode_list = [m.kode for m in matakuliah]

        schedules = db.query(JadwalKelas)\
            .options(joinedload(JadwalKelas.dosen))\
            .options(joinedload(JadwalKelas.ruang))\
            .filter(JadwalKelas.kode_mk.in_(kode_list)).all()

        return schedules



# 10. GET /lecturer/{kode_dosen}
@router.get("/lecturer/{kode_dosen}", response_model=List[JadwalKelasResponse],
            summary="Get schedule for a specific lecturer",
            description="Retrieve all class schedules for a specific lecturer by their kode_dosen.")
def get_lecturer_schedule(
    kode_dosen: str,
    db: Session = Depends(get_db)
):
    """
    Get schedule for a specific lecturer by kode_dosen
    """
    # Find the lecturer by kode_dosen
    from schedule_system.models import Dosen, JadwalKelas

    # Try to find the lecturer by kode_dosen first
    schedule_dosen = db.query(Dosen).filter(
        Dosen.kode_dosen == kode_dosen
    ).first()

    if not schedule_dosen:
        # If not found by kode_dosen, try to find by nip
        schedule_dosen = db.query(Dosen).filter(
            Dosen.nip == kode_dosen
        ).first()

        if not schedule_dosen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dosen dengan kode_dosen/NIP {kode_dosen} tidak ditemukan di sistem jadwal"
            )

    # Get all schedules for this lecturer with relationships loaded
    schedules = db.query(JadwalKelas)\
        .options(joinedload(JadwalKelas.dosen))\
        .options(joinedload(JadwalKelas.ruang))\
        .filter(JadwalKelas.dosen_id == schedule_dosen.id).all()

    return schedules