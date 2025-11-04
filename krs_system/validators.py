"""
KRS Validation System using Chain of Responsibility Pattern
"""
from abc import ABC, abstractmethod
from typing import NamedTuple
from sqlalchemy.orm import Session
from .models import KRS, KRSDetail, Matakuliah, Prerequisite


class ValidationResult(NamedTuple):
    """
    Result of a validation operation
    """
    success: bool
    message: str


class Validator(ABC):
    """
    Abstract base class for validators in the Chain of Responsibility pattern
    """
    def __init__(self):
        self.next_validator = None
    
    def set_next(self, validator):
        """
        Set the next validator in the chain
        """
        self.next_validator = validator
        return validator
    
    def validate(self, krs_id: int, db: Session) -> ValidationResult:
        """
        Validate the KRS and continue the chain if successful
        """
        result = self._validate(krs_id, db)
        
        if result.success and self.next_validator:
            return self.next_validator.validate(krs_id, db)
        
        return result
    
    @abstractmethod
    def _validate(self, krs_id: int, db: Session) -> ValidationResult:
        """
        Perform the specific validation
        """
        pass


class SKSValidator(Validator):
    """
    Validator to check if total SKS is within limit (≤ 24)
    """
    def _validate(self, krs_id: int, db: Session) -> ValidationResult:
        # Get all courses in the KRS
        krs_details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_id).all()
        
        if not krs_details:
            return ValidationResult(False, "KRS tidak memiliki matakuliah apapun")
        
        # Calculate total SKS
        total_sks = 0
        for detail in krs_details:
            matakuliah = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
            if matakuliah:
                total_sks += matakuliah.sks
        
        if total_sks > 24:
            return ValidationResult(False, f"Jumlah SKS melebihi batas maksimum (total: {total_sks}, maksimal: 24)")
        
        return ValidationResult(True, f"Total SKS valid: {total_sks}")


class PrerequisiteValidator(Validator):
    """
    Validator to check if all course prerequisites are met
    Note: For this implementation, we assume that "completed" means the student has passed
    the prerequisite course in a previous semester. In a real system, this would check
    actual grades from student records.
    """
    def _validate(self, krs_id: int, db: Session) -> ValidationResult:
        # Get all courses in the KRS
        krs_details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_id).all()
        
        for detail in krs_details:
            matakuliah = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
            if not matakuliah:
                continue
            
            # Get prerequisites for this course
            prerequisites = db.query(Prerequisite).filter(Prerequisite.matakuliah_id == matakuliah.id).all()
            
            for prereq in prerequisites:
                # Check if the prerequisite course is already taken in this KRS
                prereq_taken_in_krs = db.query(KRSDetail).filter(
                    KRSDetail.krs_id == krs_id,
                    KRSDetail.matakuliah_id == prereq.prerequisite_id
                ).first()
                
                # In a real system, we'd also check if the student has passed the prerequisite
                # from previous semesters. For now, we'll just check if it's in the same KRS.
                # This would be invalid as you can't require a course that's also in the same KRS.
                if prereq_taken_in_krs:
                    return ValidationResult(False, f"Matakuliah {matakuliah.nama} memiliki prasyarat {prereq.prerequisite_matakuliah.nama} yang juga diambil dalam KRS ini")
        
        return ValidationResult(True, "Semua prasyarat telah dipenuhi")


class ConflictValidator(Validator):
    """
    Validator to check if there are schedule conflicts (same day + overlapping time)
    """
    def _validate(self, krs_id: int, db: Session) -> ValidationResult:
        # Get all courses in the KRS with their details
        krs_details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_id).all()
        
        # Get the course details for each entry and calculate total SKS
        course_schedules = []
        total_sks = 0
        for detail in krs_details:
            matakuliah = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
            if matakuliah:
                course_schedules.append({
                    'id': matakuliah.id,
                    'kode': matakuliah.kode,
                    'nama': matakuliah.nama,
                    'hari': matakuliah.hari,
                    'jam_mulai': matakuliah.jam_mulai,
                    'jam_selesai': matakuliah.jam_selesai
                })
                total_sks += matakuliah.sks
        
        # Check for conflicts
        for i in range(len(course_schedules)):
            for j in range(i + 1, len(course_schedules)):
                course1 = course_schedules[i]
                course2 = course_schedules[j]
                
                # Check if courses are on the same day
                if course1['hari'].lower() == course2['hari'].lower():
                    # Check for time overlap
                    # Conflict exists if: start1 < end2 AND start2 < end1
                    if (course1['jam_mulai'] < course2['jam_selesai'] and 
                        course2['jam_mulai'] < course1['jam_selesai']):
                        return ValidationResult(False, 
                            f"Konflik jadwal antara {course1['kode']} ({course1['nama']}) dan {course2['kode']} ({course2['nama']}) - bentrok pada hari {course1['hari']}")
        
        return ValidationResult(True, f"Total SKS valid: {total_sks}, Tidak ada konflik jadwal")


class DuplicateValidator(Validator):
    """
    Validator to check if the same course is not taken twice in one KRS
    """
    def _validate(self, krs_id: int, db: Session) -> ValidationResult:
        # Get all courses in the KRS
        krs_details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_id).all()
        
        # Track course IDs
        course_ids = set()
        
        for detail in krs_details:
            if detail.matakuliah_id in course_ids:
                # Found duplicate
                matakuliah = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
                course_name = matakuliah.nama if matakuliah else f"ID {detail.matakuliah_id}"
                return ValidationResult(False, f"Matakuliah {course_name} diambil lebih dari sekali dalam KRS")
            
            course_ids.add(detail.matakuliah_id)
        
        return ValidationResult(True, "Tidak ada matakuliah duplikat")


def run_validations(krs_id: int, db: Session) -> ValidationResult:
    """
    Run all validations on a KRS in sequence using Chain of Responsibility pattern.
    Stops at the first validation that fails.
    """
    # Create validators and chain them together
    sks_validator = SKSValidator()
    prereq_validator = PrerequisiteValidator()
    duplicate_validator = DuplicateValidator()
    conflict_validator = ConflictValidator()
    
    # Chain validators in a sequence
    # We order them to check for duplicates first to avoid confusion with conflicts
    # Order: SKS -> Prerequisite -> Duplicate -> Conflict
    sks_validator.set_next(prereq_validator).set_next(duplicate_validator).set_next(conflict_validator)
    
    # Start validation with the first validator in the chain
    return sks_validator.validate(krs_id, db)