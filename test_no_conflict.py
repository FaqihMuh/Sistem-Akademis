"""
Test for non-conflicting course additions
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah
from krs_system.krs_logic import add_course
from pmb_system.database import Base as PMBBase
import sys
import os

def setup_test_database():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def create_test_course(db, kode, nama, sks, semester, hari, jam_mulai, jam_selesai):
    """Helper function to create a test course"""
    matakuliah = Matakuliah(
        kode=kode,
        nama=nama,
        sks=sks,
        semester=semester,
        hari=hari,
        jam_mulai=jam_mulai,
        jam_selesai=jam_selesai
    )
    db.add(matakuliah)
    db.commit()
    db.refresh(matakuliah)
    return matakuliah

def test_no_schedule_conflict():
    engine, SessionLocal = setup_test_database()
    db = SessionLocal()
    
    # Create first course
    course1 = create_test_course(
        db, 
        "COMP101", 
        "Introduction to Programming", 
        3, 
        "2023/2024-1",  # Using semester string like in actual usage
        "Senin", 
        time(8, 0), 
        time(10, 0)
    )
    
    # Create second course with same day but non-overlapping time
    course2 = create_test_course(
        db, 
        "MATH101", 
        "Calculus I", 
        4, 
        "2023/2024-1",  # Same semester
        "Senin",  # Same day
        time(10, 30),  # Non-overlapping time (starts after first course ends)
        time(12, 30)
    )
    
    # Create third course with different day (should not conflict)
    course3 = create_test_course(
        db, 
        "PHYS101", 
        "Physics I", 
        3, 
        "2023/2024-1",  # Same semester
        "Selasa",  # Different day
        time(8, 0),  # Same time as first course, but different day
        time(10, 0)
    )
    
    # Add first course to KRS
    try:
        result1 = add_course("1234567890", "COMP101", "2023/2024-1", db)
        print(f"First course addition result: {result1}")
        assert result1 == True, "First course should be added successfully"
    except Exception as e:
        print(f"Error adding first course: {e}")
        result1 = False
    
    # Add second course - should work since no time conflict
    try:
        result2 = add_course("1234567890", "MATH101", "2023/2024-1", db)
        print(f"Second course addition result: {result2}")
        assert result2 == True, "Second course should be added successfully (different time)"
    except Exception as e:
        print(f"Error adding second course: {e}")
        result2 = False
    
    # Add third course - should work since different day
    try:
        result3 = add_course("1234567890", "PHYS101", "2023/2024-1", db)
        print(f"Third course addition result: {result3}")
        assert result3 == True, "Third course should be added successfully (different day)"
    except Exception as e:
        print(f"Error adding third course: {e}")
        result3 = False
    
    # Test case with overlapping times (should fail)
    course4 = create_test_course(
        db, 
        "CHEM101", 
        "Chemistry I", 
        3, 
        "2023/2024-1",  
        "Senin",  # Same day as first course
        time(9, 0),  # Overlapping time with first course
        time(11, 0)
    )
    
    try:
        result4 = add_course("1234567890", "CHEM101", "2023/2024-1", db)
        print(f"Fourth course addition result (should fail): {result4}")
        print("ERROR: Fourth course should have failed due to conflict!")
    except Exception as e:
        print(f"Exception adding fourth course (expected): {e}")
        print("SUCCESS: Fourth course correctly rejected due to time conflict")
    
    # Clean up
    db.close()

if __name__ == "__main__":
    test_no_schedule_conflict()