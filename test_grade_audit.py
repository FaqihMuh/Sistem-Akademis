"""
Unit tests for grade audit trail functionality
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from grades_system.models import Base, Grade, GradeHistory
from grades_system import crud, audit_service
from grades_system.schemas import GradeUpdate


# Create an in-memory SQLite database for testing
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Create a test grade
    test_grade = Grade(
        nim="2023001",
        matakuliah_id=1,
        semester="2023/2024-1",
        nilai_huruf="B",
        nilai_angka=3.0,
        sks=3,
        dosen_id=1,
        presensi=90.0
    )
    session.add(test_grade)
    session.commit()
    session.refresh(test_grade)
    
    yield session
    
    session.close()


def test_create_grade_history(db_session):
    """Test creating a grade history record"""
    # Create a grade history record
    history = audit_service.create_grade_history(
        db=db_session,
        grade_id=1,
        old_nilai_huruf="C",
        old_nilai_angka=2.0,
        new_nilai_huruf="A",
        new_nilai_angka=4.0,
        changed_by="dosen1",
        reason="Koreksi nilai"
    )
    
    # Check that the history was created
    assert history is not None
    assert history.grade_id == 1
    assert history.old_value == "C(2.0)"
    assert history.new_value == "A(4.0)"
    assert history.changed_by == "dosen1"
    assert history.reason == "Koreksi nilai"
    
    # Verify it was saved to the database
    saved_history = db_session.query(GradeHistory).first()
    assert saved_history is not None
    assert saved_history.grade_id == 1
    assert saved_history.old_value == "C(2.0)"
    assert saved_history.new_value == "A(4.0)"
    assert saved_history.changed_by == "dosen1"
    assert saved_history.reason == "Koreksi nilai"


def test_get_grade_history(db_session):
    """Test getting grade history records"""
    # Create multiple history records for the same grade
    audit_service.create_grade_history(
        db=db_session,
        grade_id=1,
        old_nilai_huruf="C",
        old_nilai_angka=2.0,
        new_nilai_huruf="B",
        new_nilai_angka=3.0,
        changed_by="dosen1",
        reason="Koreksi nilai"
    )

    audit_service.create_grade_history(
        db=db_session,
        grade_id=1,
        old_nilai_huruf="B",
        old_nilai_angka=3.0,
        new_nilai_huruf="A",
        new_nilai_angka=4.0,
        changed_by="dosen2",
        reason="Permintaan mahasiswa"
    )

    # Get history records
    history_records = audit_service.get_grade_history(db_session, 1)

    # Should have 2 records
    assert len(history_records) == 2

    # Check that both records are properly retrieved
    reasons = [record.reason for record in history_records]
    assert "Koreksi nilai" in reasons
    assert "Permintaan mahasiswa" in reasons

    # Check that both values are in the records
    old_values = [record.old_value for record in history_records]
    new_values = [record.new_value for record in history_records]
    assert "C(2.0)" in old_values
    assert "B(3.0)" in new_values
    assert "B(3.0)" in old_values  # From the second record
    assert "A(4.0)" in new_values


def test_validate_grade_audit_data_success():
    """Test validation of grade audit data - success case"""
    is_valid = audit_service.validate_grade_audit_data(
        old_nilai_huruf="B",
        old_nilai_angka=3.0,
        new_nilai_huruf="A",
        new_nilai_angka=4.0,
        changed_by="dosen1",
        reason="Koreksi nilai"
    )
    
    assert is_valid is True


def test_validate_grade_audit_data_missing_reason():
    """Test validation of grade audit data - missing reason"""
    with pytest.raises(ValueError, match="Reason is required for grade changes"):
        audit_service.validate_grade_audit_data(
            old_nilai_huruf="B",
            old_nilai_angka=3.0,
            new_nilai_huruf="A",
            new_nilai_angka=4.0,
            changed_by="dosen1",
            reason=""
        )


def test_validate_grade_audit_data_missing_changed_by():
    """Test validation of grade audit data - missing changed_by"""
    with pytest.raises(ValueError, match="Changed by user is required"):
        audit_service.validate_grade_audit_data(
            old_nilai_huruf="B",
            old_nilai_angka=3.0,
            new_nilai_huruf="A",
            new_nilai_angka=4.0,
            changed_by="",
            reason="Koreksi nilai"
        )


def test_validate_grade_audit_data_invalid_nilai_huruf():
    """Test validation of grade audit data - invalid nilai_huruf"""
    with pytest.raises(ValueError, match="Old nilai_huruf must be A, B, C, D, or E"):
        audit_service.validate_grade_audit_data(
            old_nilai_huruf="F",  # Invalid grade
            old_nilai_angka=3.0,
            new_nilai_huruf="A",
            new_nilai_angka=4.0,
            changed_by="dosen1",
            reason="Koreksi nilai"
        )


def test_update_grade_creates_history(db_session):
    """Test that updating a grade creates a history record"""
    # Update the grade using CRUD function
    grade_update = GradeUpdate(
        nilai_huruf="A",
        presensi=95.0,
        reason="Koreksi nilai"
    )
    
    updated_grade = crud.update_grade(db_session, 1, grade_update, "dosen1")
    
    # Check that grade was updated
    assert updated_grade is not None
    assert updated_grade.nilai_huruf == "A"
    assert updated_grade.nilai_angka == 4.0
    
    # Check that history record was created
    history_records = db_session.query(GradeHistory).all()
    assert len(history_records) == 1
    assert history_records[0].grade_id == 1
    assert history_records[0].old_value == "B(3.0)"  # Original value
    assert history_records[0].new_value == "A(4.0)"  # New value
    assert history_records[0].changed_by == "dosen1"
    assert history_records[0].reason == "Koreksi nilai"


def test_update_grade_multiple_times_creates_multiple_history_entries(db_session):
    """Test that multiple updates create multiple history entries"""
    # First update
    grade_update1 = GradeUpdate(
        nilai_huruf="A",
        presensi=95.0,
        reason="Koreksi nilai pertama"
    )
    crud.update_grade(db_session, 1, grade_update1, "dosen1")

    # Second update
    grade_update2 = GradeUpdate(
        nilai_huruf="B",
        presensi=85.0,
        reason="Koreksi nilai kedua"
    )
    crud.update_grade(db_session, 1, grade_update2, "dosen2")

    # Third update
    grade_update3 = GradeUpdate(
        nilai_huruf="A",
        presensi=98.0,
        reason="Koreksi nilai ketiga"
    )
    crud.update_grade(db_session, 1, grade_update3, "dosen1")

    # Check that 3 history records were created
    history_records = db_session.query(GradeHistory).all()
    assert len(history_records) == 3

    # Verify that all three updates created history records with expected reasons
    history_records = audit_service.get_grade_history(db_session, 1)
    assert len(history_records) == 3

    # Check that all expected reasons are present
    reasons = [record.reason for record in history_records]
    assert reasons.count("Koreksi nilai pertama") == 1
    assert reasons.count("Koreksi nilai kedua") == 1
    assert reasons.count("Koreksi nilai ketiga") == 1


def test_reason_required_in_grade_update():
    """Test that reason is validated in audit service"""
    # Test that audit_service.validate_grade_audit_data requires reason
    with pytest.raises(ValueError, match="Reason is required for grade changes"):
        audit_service.validate_grade_audit_data(
            old_nilai_huruf="B",
            old_nilai_angka=3.0,
            new_nilai_huruf="A",
            new_nilai_angka=4.0,
            changed_by="dosen1",
            reason=""  # Empty reason should fail
        )

    with pytest.raises(ValueError, match="Reason is required for grade changes"):
        audit_service.validate_grade_audit_data(
            old_nilai_huruf="B",
            old_nilai_angka=3.0,
            new_nilai_huruf="A",
            new_nilai_angka=4.0,
            changed_by="dosen1",
            reason=None  # No reason should fail
        )