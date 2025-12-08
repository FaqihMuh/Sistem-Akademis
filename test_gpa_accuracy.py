"""
Unit tests for IPS and IPK calculation accuracy
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from grades_system.models import Base, Grade
from grades_system.services.gpa_service import calculate_ips, calculate_ipk, get_transcript


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
    
    yield session
    
    session.close()


def test_ips_calculation_single_grade(db_session):
    """Test IPS calculation for a single grade"""
    # Create a grade record
    grade = Grade(
        nim="2023001",
        matakuliah_id=1,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=1
    )
    db_session.add(grade)
    db_session.commit()
    
    # Calculate IPS
    ips = calculate_ips(db_session, "2023001", "2023/2024-1")
    
    # Expected: (3 * 4.0) / 3 = 4.0
    assert ips == 4.0


def test_ips_calculation_multiple_grades(db_session):
    """Test IPS calculation for multiple grades"""
    # Create multiple grades for same student and semester
    grades = [
        Grade(nim="2023001", matakuliah_id=1, semester="2023/2024-1", nilai_huruf="A", nilai_angka=4.0, sks=3, dosen_id=1),
        Grade(nim="2023001", matakuliah_id=2, semester="2023/2024-1", nilai_huruf="B", nilai_angka=3.0, sks=2, dosen_id=1),
        Grade(nim="2023001", matakuliah_id=3, semester="2023/2024-1", nilai_huruf="C", nilai_angka=2.0, sks=4, dosen_id=1),
    ]
    
    for grade in grades:
        db_session.add(grade)
    db_session.commit()
    
    # Calculate IPS
    ips = calculate_ips(db_session, "2023001", "2023/2024-1")
    
    # Expected: (3*4.0 + 2*3.0 + 4*2.0) / (3+2+4) = (12 + 6 + 8) / 9 = 26/9 = 2.89 (rounded to 2.89)
    expected = round((3*4.0 + 2*3.0 + 4*2.0) / (3+2+4), 2)
    assert ips == expected


def test_ips_calculation_with_failing_grade(db_session):
    """Test IPS calculation ignores failing grades (E)"""
    # Create grades including a failing grade
    grades = [
        Grade(nim="2023001", matakuliah_id=1, semester="2023/2024-1", nilai_huruf="A", nilai_angka=4.0, sks=3, dosen_id=1),
        Grade(nim="2023001", matakuliah_id=2, semester="2023/2024-1", nilai_huruf="E", nilai_angka=0.0, sks=2, dosen_id=1),  # Failing grade
    ]
    
    for grade in grades:
        db_session.add(grade)
    db_session.commit()
    
    # Calculate IPS - should only include the A grade
    ips = calculate_ips(db_session, "2023001", "2023/2024-1")
    
    # Expected: (3 * 4.0) / 3 = 4.0 (only counting passing grades >= D)
    assert ips == 4.0


def test_ipk_calculation(db_session):
    """Test IPK calculation for single grade"""
    # Create a grade record
    grade = Grade(
        nim="2023001",
        matakuliah_id=1,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=1
    )
    db_session.add(grade)
    db_session.commit()
    
    # Calculate IPK
    ipk = calculate_ipk(db_session, "2023001")
    
    # Expected: 4.0
    assert ipk == 4.0


def test_ipk_calculation_multiple_semesters(db_session):
    """Test IPK calculation across multiple semesters"""
    # Create grades from multiple semesters
    grades = [
        # Semester 1
        Grade(nim="2023001", matakuliah_id=1, semester="2023/2024-1", nilai_huruf="A", nilai_angka=4.0, sks=3, dosen_id=1),
        Grade(nim="2023001", matakuliah_id=2, semester="2023/2024-1", nilai_huruf="B", nilai_angka=3.0, sks=2, dosen_id=1),
        # Semester 2
        Grade(nim="2023001", matakuliah_id=3, semester="2023/2024-2", nilai_huruf="A", nilai_angka=4.0, sks=4, dosen_id=1),
        Grade(nim="2023001", matakuliah_id=4, semester="2023/2024-2", nilai_huruf="C", nilai_angka=2.0, sks=2, dosen_id=1),
    ]
    
    for grade in grades:
        db_session.add(grade)
    db_session.commit()
    
    # Calculate IPK
    ipk = calculate_ipk(db_session, "2023001")
    
    # Expected: (3*4.0 + 2*3.0 + 4*4.0 + 2*2.0) / (3+2+4+2) = (12 + 6 + 16 + 4) / 11 = 38/11 = 3.45
    expected = round((3*4.0 + 2*3.0 + 4*4.0 + 2*2.0) / (3+2+4+2), 2)
    assert ipk == expected


def test_ipk_calculation_with_course_repeat(db_session):
    """Test IPK calculation when course is repeated (should take highest grade)"""
    # Create grades where the same course is taken twice with different grades
    grades = [
        Grade(nim="2023001", matakuliah_id=1, semester="2023/2024-1", nilai_huruf="C", nilai_angka=2.0, sks=3, dosen_id=1),  # Lower grade first
        Grade(nim="2023001", matakuliah_id=1, semester="2023/2024-2", nilai_huruf="A", nilai_angka=4.0, sks=3, dosen_id=1),  # Higher grade later (should be used)
        Grade(nim="2023001", matakuliah_id=2, semester="2023/2024-1", nilai_huruf="B", nilai_angka=3.0, sks=2, dosen_id=1),
    ]
    
    for grade in grades:
        db_session.add(grade)
    db_session.commit()
    
    # Calculate IPK - should only use the highest grade for matakuliah_id=1
    ipk = calculate_ipk(db_session, "2023001")
    
    # Expected: Only the A (4.0) from the repeated course should be used
    # (3*4.0 + 2*3.0) / (3+2) = (12 + 6) / 5 = 3.6
    expected = round((3*4.0 + 2*3.0) / (3+2), 2)
    assert ipk == expected


def test_ipk_calculation_with_failing_grades(db_session):
    """Test IPK calculation ignores failing grades (E)"""
    # Create grades including a failing grade
    grades = [
        Grade(nim="2023001", matakuliah_id=1, semester="2023/2024-1", nilai_huruf="A", nilai_angka=4.0, sks=3, dosen_id=1),
        Grade(nim="2023001", matakuliah_id=2, semester="2023/2024-1", nilai_huruf="E", nilai_angka=0.0, sks=2, dosen_id=1),  # Failing grade
    ]
    
    for grade in grades:
        db_session.add(grade)
    db_session.commit()
    
    # Calculate IPK - should only include the A grade
    ipk = calculate_ipk(db_session, "2023001")
    
    # Expected: (3 * 4.0) / 3 = 4.0 (only counting passing grades >= D)
    assert ipk == 4.0


