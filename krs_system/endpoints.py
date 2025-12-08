"""
KRS FastAPI Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import time
from krs_system.models import KRS, KRSDetail, Matakuliah
from krs_system.krs_logic import (
    add_course as add_course_service,
    remove_course as remove_course_service,
    validate_krs as validate_krs_service,
    submit_krs as submit_krs_service,
    approve_krs as approve_krs_service
)
from krs_system.validators import ValidationResult
from pmb_system.models import CalonMahasiswa, StatusEnum  # Importing PMB model and StatusEnum to validate NIM
from pmb_system.database import get_db  # Use the database session dependency from PMB system


router = APIRouter(tags=["KRS"])


# Pydantic models for request/response
from pydantic import BaseModel
from typing import Optional


class KRSRequest(BaseModel):
    kode_mk: str
    semester: str


class SubmitKRSRequest(BaseModel):
    semester: str  # Need semester to identify the right KRS


class ApproveKRSRequest(BaseModel):
    semester: str  # Need semester to identify the right KRS
    dosen_pa_id: Optional[int] = None


class CourseDetail(BaseModel):
    id: int
    kode: str
    nama: str
    sks: int
    semester: int
    hari: str
    jam_mulai: time
    jam_selesai: time

    class Config:
        from_attributes = True


class KRSDetailResponse(BaseModel):
    id: int
    nim: str
    semester: str
    status: str
    dosen_pa_id: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    courses: List[CourseDetail]

    class Config:
        from_attributes = True


@router.post("/{nim}/add", status_code=status.HTTP_201_CREATED)
def add_course_to_krs_endpoint(
    nim: str,
    request: KRSRequest,
    db: Session = Depends(get_db)
):
    """
    Add a course to student's KRS
    """
    # Validate that the student exists in PMB system with the given NIM
    # The student must have been approved (have a NIM assigned) to access KRS system
    student = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim == nim  # Check directly for the NIM field
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan di sistem PMB"
        )
    
    # Additionally, ensure the student's status is approved (has been assigned NIM)
    if student.status != StatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mahasiswa dengan NIM {nim} belum disetujui atau tidak memiliki status yang valid"
        )
    
    # Validate that the course exists
    course = db.query(Matakuliah).filter(Matakuliah.kode == request.kode_mk).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mata kuliah dengan kode {request.kode_mk} tidak ditemukan"
        )
    
    # Call the business logic function
    success = add_course_service(nim, request.kode_mk, request.semester, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal menambahkan mata kuliah ke KRS"
        )
    
    return {"message": f"Mata kuliah {request.kode_mk} berhasil ditambahkan ke KRS", "success": True}


@router.delete("/{nim}/remove", status_code=status.HTTP_200_OK)
def remove_course_from_krs_endpoint(
    nim: str,
    request: KRSRequest,  # Using the request model that has kode_mk and semester
    db: Session = Depends(get_db)
):
    """
    Remove a course from student's KRS
    """
    # Validate that the student exists in PMB system with the given NIM
    student = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim == nim  # Check directly for the NIM field
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan"
        )
    
    # Additionally, ensure the student's status is approved
    if student.status != StatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mahasiswa dengan NIM {nim} belum disetujui atau tidak memiliki status yang valid"
        )
    
    # Validate that the course exists
    course = db.query(Matakuliah).filter(Matakuliah.kode == request.kode_mk).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mata kuliah dengan kode {request.kode_mk} tidak ditemukan"
        )
    
    # Call the business logic function
    success = remove_course_service(nim, request.kode_mk, request.semester, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal menghapus mata kuliah dari KRS, kemungkinan mata kuliah tidak ada di KRS"
        )
    
    return {"message": f"Mata kuliah {request.kode_mk} berhasil dihapus dari KRS", "success": True}


@router.post("/{nim}/submit", status_code=status.HTTP_200_OK)
def submit_krs_endpoint(
    nim: str,
    request: SubmitKRSRequest,  # Need semester to identify the right KRS
    db: Session = Depends(get_db)
):
    """
    Submit student's KRS for approval
    """
    # Validate that the student exists in PMB system with the given NIM
    student = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim == nim  # Check directly for the NIM field
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan"
        )
    
    # Additionally, ensure the student's status is approved
    if student.status != StatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mahasiswa dengan NIM {nim} belum disetujui atau tidak memiliki status yang valid"
        )
    
    # Call the business logic function
    success = submit_krs_service(nim, request.semester, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal submit KRS, mungkin KRS tidak valid atau tidak dalam status DRAFT"
        )
    
    return {"message": "KRS berhasil disubmit untuk approval", "success": True}


@router.post("/{nim}/approve", status_code=status.HTTP_200_OK)
def approve_krs_endpoint(
    nim: str,
    request: ApproveKRSRequest,
    db: Session = Depends(get_db)
):
    """
    Approve student's KRS
    """
    # Validate that the student exists in PMB system with the given NIM
    student = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim == nim  # Check directly for the NIM field
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mahasiswa dengan NIM {nim} tidak ditemukan"
        )
    
    # Additionally, ensure the student's status is approved
    if student.status != StatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mahasiswa dengan NIM {nim} belum disetujui atau tidak memiliki status yang valid"
        )
    
    # Call the business logic function
    success = approve_krs_service(nim, request.semester, request.dosen_pa_id, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal approve KRS, mungkin KRS tidak dalam status SUBMITTED"
        )
    
    return {"message": "KRS berhasil diapprove", "success": True}


@router.get("/{nim}", response_model=List[KRSDetailResponse])  # Return list since a student can have multiple semesters
def get_krs_detail_endpoint(
    nim: str,
    db: Session = Depends(get_db)
):
    """
    Get student's KRS details and status for all semesters
    """
    # Validate that the student exists in PMB system with the given NIM
    student = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.nim == nim  # Check directly for the NIM field
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
    
    # Get all KRS records for the student across all semesters
    krs_list = db.query(KRS).filter(KRS.nim == nim).all()
    
    if not krs_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tidak ada KRS ditemukan untuk mahasiswa {nim}"
        )
    
    response_list = []
    for krs in krs_list:
        # Get the courses in this KRS
        krs_details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        courses = []
        for detail in krs_details:
            matakuliah = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
            if matakuliah:
                courses.append(matakuliah)
        
        # Create response object for this KRS
        response = KRSDetailResponse(
            id=krs.id,
            nim=krs.nim,
            semester=krs.semester,
            status=krs.status.value if hasattr(krs.status, 'value') else str(krs.status),
            dosen_pa_id=krs.dosen_pa_id,
            created_at=str(krs.created_at) if krs.created_at else None,
            updated_at=str(krs.updated_at) if krs.updated_at else None,
            courses=courses
        )
        response_list.append(response)
    
    return response_list


# @router.get("/course/{matakuliah_id}", response_model=List[dict])
# def get_students_by_course_endpoint(
#     matakuliah_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get all students enrolled in a specific course with approved KRS
#     """
#     # First check if the course exists
#     course = db.query(Matakuliah).filter(Matakuliah.id == matakuliah_id).first()
#     if not course:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Mata kuliah dengan ID {matakuliah_id} tidak ditemukan"
#         )

#     # Find all KRS details that reference this course
#     krs_details = db.query(KRSDetail).filter(KRSDetail.matakuliah_id == matakuliah_id).all()

#     # Get the corresponding KRS records and students
#     students = []
#     for detail in krs_details:
#         krs = db.query(KRS).filter(KRS.id == detail.krs_id).first()
#         if krs:
#             # Only include students with APPROVED KRS status
#             from krs_system.models import KRSStatusEnum
#             if krs.status == KRSStatusEnum.APPROVED or str(krs.status).upper() == "APPROVED":
#                 # Get student info
#                 student = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == krs.nim).first()
#                 if student:
#                     students.append({
#                         "nim": krs.nim,
#                         "mahasiswa": {
#                             "nama_lengkap": student.nama_lengkap
#                         },
#                         "semester": krs.semester,  # Include semester for consistency
#                         "krs_detail_id": detail.id  # Include KRS detail ID
#                     })

#     return students
@router.get("/course/{matakuliah_id}", response_model=List[dict])
def get_students_by_course_endpoint(
    matakuliah_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all students enrolled in a specific course with approved KRS.
    Now includes full matakuliah info (sks, semester, kode_mk, nama_mk).
    """

    # --- CHECK COURSE EXISTS ---
    course = (
        db.query(Matakuliah)
        .filter(Matakuliah.id == matakuliah_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mata kuliah dengan ID {matakuliah_id} tidak ditemukan"
        )

    # --- GET ALL KRS DETAILS BELONGING TO THIS COURSE ---
    krs_details = (
        db.query(KRSDetail)
        .filter(KRSDetail.matakuliah_id == matakuliah_id)
        .all()
    )

    students = []

    for detail in krs_details:
        krs = db.query(KRS).filter(KRS.id == detail.krs_id).first()
        if not krs:
            continue

        # Check approved status
        from krs_system.models import KRSStatusEnum
        if krs.status not in [KRSStatusEnum.APPROVED, "APPROVED"]:
            continue

        # Get student
        student = (
            db.query(CalonMahasiswa)
            .filter(CalonMahasiswa.nim == krs.nim)
            .first()
        )

        if not student:
            continue

        # --- FULL RESPONSE INCLUDING MATAKULIAH INFO ---
        students.append({
            "nim": krs.nim,
            "mahasiswa": {
                "nama_lengkap": student.nama_lengkap
            },
            "semester_mahasiswa": krs.semester,  # tetap disertakan
            "krs_detail_id": detail.id,

            # 🔥 Tambahkan data matakuliah lengkap
            "matakuliah": {
                "id": course.id,
                "kode_mk": course.kode,
                "nama_mk": course.nama,
                "sks": course.sks,
                "semester": course.semester
            }
        })

    return students


@router.get("/kode/{kode_mk}", response_model=dict)
def get_matakuliah_by_kode_endpoint(
    kode_mk: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific matakuliah by its kode
    """
    # Find the course by kode
    course = db.query(Matakuliah).filter(Matakuliah.kode == kode_mk).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mata kuliah dengan kode {kode_mk} tidak ditemukan"
        )

    return {
        "id": course.id,
        "kode": course.kode,
        "nama": course.nama,
        "sks": course.sks,
        "semester": course.semester,
        "created_at": str(course.created_at) if course.created_at else None
    }