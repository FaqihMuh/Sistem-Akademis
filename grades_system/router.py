from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from grades_system import crud, schemas, audit_service
from pmb_system.database import get_db
from auth_system.dependencies import get_current_user, role_required
from auth_system.models import User, RoleEnum
from krs_system.models import Matakuliah
from pmb_system.models import CalonMahasiswa
from schedule_system.models import Dosen

router = APIRouter(prefix="/api/grades", tags=["Grades"])


@router.post("/", response_model=schemas.GradeResponse)
def input_grade(
    grade: schemas.GradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Input nilai mahasiswa untuk 1 mata kuliah"""
    # Check if user is DOSEN
    if current_user.role != RoleEnum.DOSEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya dosen yang dapat menginput nilai"
        )
    
    # Validate that the current dosen is teaching this course
    if not crud.validate_dosen_teaching_course(db, int(current_user.kode_dosen), grade.matakuliah_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dosen tidak mengajar mata kuliah ini"
        )
    
    # Check if student exists
    student = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == grade.nim).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mahasiswa tidak ditemukan"
        )
    
    # Check if course exists
    course = db.query(Matakuliah).filter(Matakuliah.id == grade.matakuliah_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mata kuliah tidak ditemukan"
        )
    
    try:
        db_grade = crud.create_grade(db, grade, current_user.username)
        return db_grade
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/student/{nim}", response_model=List[schemas.StudentGradeResponse])
def get_student_grades(
    nim: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil seluruh nilai mahasiswa"""
    # Check if current user is the student or admin/dosen
    if current_user.role == RoleEnum.MAHASISWA:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya bisa melihat nilai sendiri"
            )
    elif current_user.role not in [RoleEnum.ADMIN, RoleEnum.DOSEN]:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki akses untuk melihat nilai mahasiswa ini"
            )
    
    # Get grades with course information
    grades_with_course = crud.get_grades_by_student(db, nim)
    
    # Format response
    result = []
    for grade, kode_mk, nama_mk in grades_with_course:
        result.append(
            schemas.StudentGradeResponse(
                id=grade.id,
                kode_mk=kode_mk,
                nama_mk=nama_mk,
                sks=grade.sks,
                nilai_huruf=grade.nilai_huruf,
                nilai_angka=grade.nilai_angka,
                semester=grade.semester,
                created_at=grade.created_at
            )
        )
    
    return result


@router.get("/course/{matakuliah_id}", response_model=List[schemas.CourseGradeResponse])
def get_course_grades(
    matakuliah_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil nilai semua mahasiswa dalam 1 mata kuliah"""
    # Check if current user is admin, or dosen teaching this course
    if current_user.role == RoleEnum.DOSEN:
        # Verify that the dosen is teaching this course
        if not crud.validate_dosen_teaching_course(db, int(current_user.kode_dosen), matakuliah_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak mengajar mata kuliah ini"
            )
    elif current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki akses untuk melihat nilai mata kuliah ini"
        )
    
    # Get grades with student information
    grades_with_student = crud.get_grades_by_course(db, matakuliah_id)
    
    # Format response
    result = []
    for grade, nama_mahasiswa in grades_with_student:
        result.append(
            schemas.CourseGradeResponse(
                id=grade.id,
                nim=grade.nim,
                nama_mahasiswa=nama_mahasiswa,
                sks=grade.sks,
                nilai_huruf=grade.nilai_huruf,
                nilai_angka=grade.nilai_angka,
                presensi=grade.presensi,
                created_at=grade.created_at
            )
        )
    
    return result


@router.put("/{id}", response_model=schemas.GradeResponse)
def update_grade(
    id: int,
    grade_update: schemas.GradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit nilai dengan audit trail"""
    # Check if user is DOSEN or ADMIN
    if current_user.role not in [RoleEnum.DOSEN, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya dosen atau admin yang dapat mengupdate nilai"
        )
    
    # Get the grade to check if it exists and if the current user can update it
    existing_grade = crud.get_grade_by_id(db, id)
    if not existing_grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nilai tidak ditemukan"
        )
    
    # Check if dosen is teaching this course (if user is a dosen)
    if current_user.role == RoleEnum.DOSEN:
        if not crud.validate_dosen_teaching_course(db, int(current_user.kode_dosen), existing_grade.matakuliah_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak mengajar mata kuliah ini"
            )
    
    try:
        updated_grade = crud.update_grade(db, id, grade_update, current_user.username)
        if not updated_grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gagal mengupdate nilai"
            )
        return updated_grade
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{id}", response_model=schemas.GradeResponse)
def delete_grade(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hapus nilai"""
    # Check if user is ADMIN
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang dapat menghapus nilai"
        )

    deleted_grade = crud.delete_grade(db, id)
    if not deleted_grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nilai tidak ditemukan"
        )

    return deleted_grade


@router.get("/history/{grade_id}", response_model=List[schemas.GradeHistoryResponse])
def get_grade_history(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil histori perubahan nilai untuk grade tertentu"""
    # Check if user has appropriate access
    if current_user.role not in [RoleEnum.DOSEN, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya dosen atau admin yang dapat melihat histori nilai"
        )

    # Verify the grade exists and user has permission to view its history
    grade = crud.get_grade_by_id(db, grade_id)
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nilai tidak ditemukan"
        )

    # Check if dosen is teaching this course (if user is a dosen)
    if current_user.role == RoleEnum.DOSEN:
        if not crud.validate_dosen_teaching_course(db, int(current_user.kode_dosen), grade.matakuliah_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak mengajar mata kuliah ini"
            )

    # Get history records for this grade
    history_records = audit_service.get_grade_history(db, grade_id)
    return history_records