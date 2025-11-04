"""
Test for KRS business logic - no explicit transactions in test
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS, KRSDetail
from krs_system.krs_logic import add_course, remove_course, validate_krs, submit_krs, approve_krs
from krs_system.state_manager import KRSStatus
from pmb_system.database import DATABASE_URL
import random
import string


def generate_random_code():
    """Generate a random code for testing"""
    letters = string.ascii_uppercase
    numbers = string.digits
    return "TST" + ''.join(random.choice(numbers) for _ in range(3))


def test_krs_logic_clean():
    print("Testing KRS business logic (clean)...")
    
    # Using the same database engine as PMB system
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Create all tables defined in KRS models
    Base.metadata.create_all(bind=engine)
    
    # Test creating a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Generate unique codes
        kode1 = generate_random_code()
        kode2 = generate_random_code()
        
        # Create test matakuliah - do this outside any conflicting transaction
        matakuliah1 = Matakuliah(
            kode=kode1,
            nama="Pemrograman Web",
            sks=3,
            semester=2,
            hari="Selasa",
            jam_mulai=time(8, 0, 0),
            jam_selesai=time(10, 0, 0)
        )
        
        matakuliah2 = Matakuliah(
            kode=kode2,
            nama="Basis Data",
            sks=4,
            semester=2,
            hari="Rabu",
            jam_mulai=time(10, 0, 0),
            jam_selesai=time(12, 0, 0)
        )
        
        # Add matakuliah first
        db.add(matakuliah1)
        db.add(matakuliah2)
        db.commit()
        db.refresh(matakuliah1)
        db.refresh(matakuliah2)
        
        print(f"Created test matakuliah: {kode1}, {kode2}")
        
        # Test 1: Add course to KRS
        print("\n--- Test 1: Add course to KRS ---")
        nim = "5554443332" + ''.join(random.choice(string.digits) for _ in range(2))  # Random NIM
        semester = "2025/2026-1"
        
        # Close any ongoing transaction before calling functions with transactions
        db.close()
        db = SessionLocal()  # Create a fresh session
        
        success = add_course(nim, kode1, semester, db)
        print(f"Add course result: {success}")
        if not success:
            print("Add course failed - let's debug why")
            # Check if the course exists
            course = db.query(Matakuliah).filter(Matakuliah.kode == kode1).first()
            print(f"Course exists: {course is not None}")
            
            # Check if KRS already exists
            existing_krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
            print(f"Existing KRS: {existing_krs is not None}")
            
            # Check if course is in existing details
            if existing_krs:
                detail = db.query(KRSDetail).filter(
                    KRSDetail.krs_id == existing_krs.id,
                    KRSDetail.matakuliah_id == course.id
                ).first()
                print(f"Course already in KRS details: {detail is not None}")
        
        assert success == True, "Adding course should succeed"
        print("SUCCESS: Course added to KRS")
        
        # Verify the course was added
        # Need to refresh the session to get fresh data after the transaction
        db.close()
        db = SessionLocal()
        
        krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
        assert krs is not None, "KRS should be created"
        assert krs.status == KRSStatus.DRAFT, f"New KRS should be in DRAFT status, but is {krs.status}"
        
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        assert len(details) == 1, f"Should have 1 course in KRS, but has {len(details)}"
        print("SUCCESS: KRS created with correct status and course")
        
        # Test 2: Add another course to the same KRS
        print("\n--- Test 2: Add another course to KRS ---")
        success = add_course(nim, kode2, semester, db)
        print(f"Add second course result: {success}")
        assert success == True, "Adding second course should succeed"
        print("SUCCESS: Second course added to KRS")
        
        # Verify both courses are in KRS
        db.close()
        db = SessionLocal()
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        assert len(details) == 2, f"Should have 2 courses in KRS, but has {len(details)}"
        print("SUCCESS: KRS now has 2 courses")
        
        # Clean up test data
        db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).delete()
        db.delete(krs)
        db.delete(matakuliah1)
        db.delete(matakuliah2)
        db.commit()
        
        print("\nBasic KRS business logic tests passed successfully!")
        
    except Exception as e:
        print(f"ERROR: Error during KRS logic tests: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except:
            pass  # Session might be closed
        raise
    finally:
        try:
            db.close()
        except:
            pass


if __name__ == "__main__":
    test_krs_logic_clean()