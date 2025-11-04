"""
Debug version of KRS business logic
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
from typing import Optional
import datetime
from fastapi import HTTPException
from krs_system.models import KRS, KRSDetail, Matakuliah, KRSStatusEnum
from krs_system.state_manager import transition
from krs_system.validators import run_validations, ValidationResult


def check_schedule_conflict_for_add(db: Session, nim: str, new_matakuliah: Matakuliah, semester: str) -> bool:
    """
    Check if there is a schedule conflict between the new course and existing courses
    in the same semester for the given student.
    
    Args:
        db: Database session
        nim: Student ID
        new_matakuliah: The new Matakuliah object to check against existing courses
        semester: Academic semester to check for conflicts
        
    Returns:
        bool: True if there is a conflict, False otherwise
    """
    from datetime import datetime as dt
    
    # Get the student's existing KRS for the same semester
    existing_krs = db.query(KRS).filter(
        KRS.nim == nim,
        KRS.semester == semester  # Using the semester parameter from the request
    ).first()
    
    # If no existing KRS, there's no conflict
    if not existing_krs:
        return False
    
    # Get all existing courses in this KRS
    existing_krs_details = db.query(KRSDetail).filter(KRSDetail.krs_id == existing_krs.id).all()
    
    # If no existing courses, there's no conflict
    if not existing_krs_details:
        return False
    
    # Get detailed info for each existing course to check for conflicts
    for detail in existing_krs_details:
        existing_matakuliah = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
        
        if not existing_matakuliah:
            continue  # Skip if the matakuliah doesn't exist (shouldn't happen but just in case)
        
        # Compare the days (case-insensitive)
        new_hari = new_matakuliah.hari.lower().strip()
        existing_hari = existing_matakuliah.hari.lower().strip()
        
        # If days are different, no conflict possible
        if new_hari != existing_hari:
            continue
        
        # Parse the time strings to time objects for accurate comparison
        new_start = dt.strptime(str(new_matakuliah.jam_mulai), "%H:%M:%S").time()
        new_end = dt.strptime(str(new_matakuliah.jam_selesai), "%H:%M:%S").time()
        existing_start = dt.strptime(str(existing_matakuliah.jam_mulai), "%H:%M:%S").time()
        existing_end = dt.strptime(str(existing_matakuliah.jam_selesai), "%H:%M:%S").time()
        
        # Check if times overlap: start1 < end2 and start2 < end1
        if new_start < existing_end and existing_start < new_end:
            return True  # Conflict found
    
    return False  # No conflict found


def add_course(nim: str, kode_mk: str, semester: str, db: Session) -> bool:
    """
    Add a course to the student's KRS for the given semester.
    
    Args:
        nim: Student ID
        kode_mk: Course code
        semester: Academic semester
        db: Database session
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"DEBUG: Starting add_course for NIM: {nim}, Kode: {kode_mk}, Semester: {semester}")
        
        with db.begin():
            # Get the course
            matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == kode_mk).first()
            if not matakuliah:
                print(f"DEBUG: Course with kode {kode_mk} not found")
                return False  # Course doesn't exist
            
            print(f"DEBUG: Found matakuliah with ID: {matakuliah.id}")
            
            # Get existing KRS for this student and semester
            existing_krs = db.query(KRS).filter(
                KRS.nim == nim,
                KRS.semester == semester
            ).first()
            
            print(f"DEBUG: Found existing KRS: {existing_krs is not None}")
            
            # If no existing KRS, create a new one in DRAFT status
            if not existing_krs:
                print(f"DEBUG: Creating new KRS with status {KRSStatusEnum.DRAFT}")
                new_krs = KRS(
                    nim=nim,
                    semester=semester,
                    status=KRSStatusEnum.DRAFT  # Use the enum from models
                )
                db.add(new_krs)
                db.flush()  # Get the ID without committing
                print(f"DEBUG: New KRS created with ID: {new_krs.id}")
                krs = new_krs
            else:
                krs = existing_krs
                print(f"DEBUG: Using existing KRS with ID: {krs.id}")
            
            # Check if course is already in KRS
            existing_detail = db.query(KRSDetail).filter(
                KRSDetail.krs_id == krs.id,
                KRSDetail.matakuliah_id == matakuliah.id
            ).first()
            
            if existing_detail:
                print(f"DEBUG: Course already exists in KRS")
                return False  # Course already in KRS
                
            print(f"DEBUG: Course not in KRS, adding new detail")
            
            # Check for schedule conflicts before adding the course
            if check_schedule_conflict_for_add(db, nim, matakuliah, semester):
                print(f"DEBUG: Schedule conflict detected, rejecting course addition")
                raise HTTPException(status_code=400, detail=f"Jadwal bentrok dengan mata kuliah {matakuliah.nama}")
            
            # Add the course to KRS
            krs_detail = KRSDetail(
                krs_id=krs.id,
                matakuliah_id=matakuliah.id
            )
            db.add(krs_detail)
            print(f"DEBUG: Course detail added, committing transaction")
            return True
            
    except IntegrityError as e:
        print(f"DEBUG: IntegrityError occurred: {e}")
        return False  # The transaction is automatically rolled back
    except HTTPException:
        # Re-raise HTTP exceptions (like schedule conflict)
        print(f"DEBUG: HTTPException occurred (re-raising)")
        raise
    except Exception as e:
        print(f"DEBUG: Other exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False  # The transaction is automatically rolled back


def remove_course(nim: str, kode_mk: str, semester: str, db: Session) -> bool:
    """
    Remove a course from the student's KRS for the given semester.
    
    Args:
        nim: Student ID
        kode_mk: Course code
        semester: Academic semester
        db: Database session
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with db.begin():
            # Get the course
            matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == kode_mk).first()
            if not matakuliah:
                return False  # Course doesn't exist
            
            # Get the KRS
            krs = db.query(KRS).filter(
                KRS.nim == nim,
                KRS.semester == semester
            ).first()
            
            if not krs:
                return False  # KRS doesn't exist
            
            # Remove the course from KRS
            krs_detail = db.query(KRSDetail).filter(
                KRSDetail.krs_id == krs.id,
                KRSDetail.matakuliah_id == matakuliah.id
            ).first()
            
            if not krs_detail:
                return False  # Course not in KRS
            
            db.delete(krs_detail)
            return True
            
    except Exception:
        return False  # The transaction is automatically rolled back


def validate_krs(nim: str, semester: str, db: Session) -> ValidationResult:
    """
    Validate the student's KRS for the given semester.
    
    Args:
        nim: Student ID
        semester: Academic semester
        db: Database session
        
    Returns:
        ValidationResult: Result of the validation
    """
    # Get the KRS
    krs = db.query(KRS).filter(
        KRS.nim == nim,
        KRS.semester == semester
    ).first()
    
    if not krs:
        return ValidationResult(False, "KRS tidak ditemukan")
    
    # Run all validations
    return run_validations(krs.id, db)


def submit_krs(nim: str, semester: str, db: Session) -> bool:
    """
    Submit the student's KRS for the given semester for approval.
    
    Args:
        nim: Student ID
        semester: Academic semester
        db: Database session
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with db.begin():
            # Get the KRS
            krs = db.query(KRS).filter(
                KRS.nim == nim,
                KRS.semester == semester
            ).first()
            
            if not krs:
                return False  # KRS doesn't exist
            
            # Check if KRS is in DRAFT status
            if krs.status != KRSStatusEnum.DRAFT:  # Use the enum from models
                return False  # Only DRAFT KRS can be submitted
            
            # Validate the KRS first
            validation_result = validate_krs(nim, semester, db)
            if not validation_result.success:
                return False  # Validation failed
            
            # Transition the status using state manager
            new_status = transition(krs.status, "submit")
            krs.status = new_status
            krs.updated_at = datetime.datetime.now()
            
            return True
            
    except ValueError:  # This is raised by the transition function for invalid transitions
        return False  # The transaction is automatically rolled back
    except Exception:
        return False  # The transaction is automatically rolled back


def approve_krs(nim: str, semester: str, dosen_pa_id: Optional[int], db: Session) -> bool:
    """
    Approve the student's KRS for the given semester.
    
    Args:
        nim: Student ID
        semester: Academic semester
        dosen_pa_id: Advisor ID
        db: Database session
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with db.begin():
            # Get the KRS
            krs = db.query(KRS).filter(
                KRS.nim == nim,
                KRS.semester == semester
            ).first()
            
            if not krs:
                return False  # KRS doesn't exist
            
            # Check if KRS is in SUBMITTED status
            if krs.status != KRSStatusEnum.SUBMITTED:  # Use the enum from models
                return False  # Only SUBMITTED KRS can be approved
            
            # Transition the status using state manager
            new_status = transition(krs.status, "approve")
            krs.status = new_status
            krs.dosen_pa_id = dosen_pa_id  # Update advisor ID
            krs.updated_at = datetime.datetime.now()
            
            return True
            
    except ValueError:  # This is raised by the transition function for invalid transitions
        return False  # The transaction is automatically rolled back
    except Exception:
        return False  # The transaction is automatically rolled back