"""
Simple test for schedule conflict functionality
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah
from krs_system.krs_logic import add_course, check_schedule_conflict_for_add
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

def test_schedule_conflict():
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
    
    # Create second course with overlapping time on same day
    course2 = create_test_course(
        db, 
        "MATH101", 
        "Calculus I", 
        4, 
        "2023/2024-1",  # Same semester
        "Senin",  # Same day
        time(9, 0),  # Overlaps with first course (9:00-11:00 overlaps with 8:00-10:00)
        time(11, 0)
    )
    
    # Add first course to KRS
    try:
        result1 = add_course("1234567890", "COMP101", "2023/2024-1", db)
        print(f"First course addition result: {result1}")
    except Exception as e:
        print(f"Error adding first course: {e}")
        result1 = False
    
    # Check for conflict manually
    conflict = check_schedule_conflict_for_add(db, "1234567890", course2, "2023/2024-1")
    print(f"Schedule conflict detected: {conflict}")
    
    # Try to add second course - should raise HTTPException
    try:
        result2 = add_course("1234567890", "MATH101", "2023/2024-1", db)
        print(f"Second course addition result: {result2}")
    except Exception as e:
        print(f"Exception adding second course (expected): {e}")

    # Clean up
    db.close()

if __name__ == "__main__":
    test_schedule_conflict()