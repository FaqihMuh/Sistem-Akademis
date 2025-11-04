"""
Debug test for second course issue
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS, KRSDetail
from krs_system.krs_logic_debug import add_course  # Use debug version to see the error
from krs_system.state_manager import KRSStatus
from pmb_system.database import DATABASE_URL
import random
import string


def generate_random_code():
    """Generate a random code for testing"""
    letters = string.ascii_uppercase
    numbers = string.digits
    return "DBG" + ''.join(random.choice(numbers) for _ in range(3))


def test_second_course_issue():
    print("Testing second course issue...")
    
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
        
        # Test 1: Add first course to KRS
        print("\n--- Test 1: Add first course to KRS ---")
        nim = "5554443332" + ''.join(random.choice(string.digits) for _ in range(2))  # Random NIM
        semester = "2025/2026-1"
        
        # Close any ongoing transaction before calling functions with transactions
        db.close()
        db = SessionLocal()  # Create a fresh session
        
        success1 = add_course(nim, kode1, semester, db)
        print(f"First add course result: {success1}")
        assert success1 == True, "Adding first course should succeed"
        print("SUCCESS: First course added to KRS")
        
        # Now test adding the second course
        print("\n--- Testing second course ---")
        db.close()
        db = SessionLocal()
        success2 = add_course(nim, kode2, semester, db)
        print(f"Second add course result: {success2}")
        
        print("\nDebug: Let's see what's in the database now")
        db.close()
        db = SessionLocal()
        krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
        if krs:
            print(f"Found KRS: ID={krs.id}, Status={krs.status}")
            details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
            print(f"Number of courses in KRS: {len(details)}")
            for detail in details:
                mk = db.query(Matakuliah).filter(Matakuliah.id == detail.matakuliah_id).first()
                print(f"  - Course: {mk.kode if mk else 'Unknown'}")
        else:
            print("No KRS found")
        
        if success2:
            print("SUCCESS: Second course added to KRS")
        else:
            print("FAILED: Second course not added to KRS")
        
        # Clean up test data
        if krs:
            db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).delete()
            db.delete(krs)
        db.delete(matakuliah1)
        db.delete(matakuliah2)
        db.commit()
        
        print("\nDebug test completed!")
        
    except Exception as e:
        print(f"ERROR: Error during debug test: {str(e)}")
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
    test_second_course_issue()