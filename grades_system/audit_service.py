"""
Service module for handling audit trail logic for grades
"""
from sqlalchemy.orm import Session
from grades_system.models import Grade, GradeHistory
from grades_system.schemas import GradeHistoryCreate


def create_grade_history(
    db: Session,
    grade_id: int,
    old_nilai_huruf: str,
    old_nilai_angka: float,
    new_nilai_huruf: str,
    new_nilai_angka: float,
    changed_by: str,
    reason: str
):
    """
    Create a new audit trail entry for grade changes
    
    Args:
        db: Database session
        grade_id: ID of the grade being changed
        old_nilai_huruf: Previous letter grade
        old_nilai_angka: Previous numeric grade
        new_nilai_huruf: New letter grade
        new_nilai_angka: New numeric grade
        changed_by: Username of person making the change
        reason: Reason for the change
    
    Returns:
        GradeHistory: Created history record
    """
    old_value = f"{old_nilai_huruf}({old_nilai_angka})"
    new_value = f"{new_nilai_huruf}({new_nilai_angka})"
    
    history = GradeHistory(
        grade_id=grade_id,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
        reason=reason
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return history


def get_grade_history(db: Session, grade_id: int):
    """
    Get all history records for a specific grade
    
    Args:
        db: Database session
        grade_id: ID of the grade to get history for
    
    Returns:
        List[GradeHistory]: List of history records, ordered by changed_at descending
    """
    return (
        db.query(GradeHistory)
        .filter(GradeHistory.grade_id == grade_id)
        .order_by(GradeHistory.changed_at.desc())
        .all()
    )


def validate_grade_audit_data(
    old_nilai_huruf: str,
    old_nilai_angka: float,
    new_nilai_huruf: str,
    new_nilai_angka: float,
    changed_by: str,
    reason: str = None
) -> bool:
    """
    Validate audit trail data

    Args:
        old_nilai_huruf: Previous letter grade
        old_nilai_angka: Previous numeric grade
        new_nilai_huruf: New letter grade
        new_nilai_angka: New numeric grade
        changed_by: Username of person making the change
        reason: Reason for the change

    Returns:
        bool: True if data is valid, raises ValueError if invalid
    """
    if not reason or not reason.strip():
        raise ValueError("Reason is required for grade changes")

    if not changed_by or not changed_by.strip():
        raise ValueError("Changed by user is required")

    if old_nilai_huruf.upper() not in ['A', 'B', 'C', 'D', 'E']:
        raise ValueError("Old nilai_huruf must be A, B, C, D, or E")

    if new_nilai_huruf.upper() not in ['A', 'B', 'C', 'D', 'E']:
        raise ValueError("New nilai_huruf must be A, B, C, D, or E")

    if old_nilai_angka < 0.0 or old_nilai_angka > 4.0:
        raise ValueError("Old nilai_angka must be between 0.0 and 4.0")

    if new_nilai_angka < 0.0 or new_nilai_angka > 4.0:
        raise ValueError("New nilai_angka must be between 0.0 and 4.0")

    return True