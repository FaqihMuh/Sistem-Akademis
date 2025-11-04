"""
Simple test for KRS business logic
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS, KRSDetail
from krs_system.krs_logic import add_course, remove_course, validate_krs, submit_krs, approve_krs
from krs_system.state_manager import transition, KRSStatus
from krs_system.enums import KRSStatusEnum
from pmb_system.database import DATABASE_URL
import random
import string


def generate_random_code():
    """Generate a random code for testing"""
    letters = string.ascii_uppercase
    numbers = string.digits
    return "TST" + ''.join(random.choice(numbers) for _ in range(3))


def test_krs_logic_simple():
    print("Testing KRS business logic (simple)...")
    
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
        
        # Create test matakuliah
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
        success = add_course(nim, kode1, semester, db)
        print(f"Add course result: {success}")
        assert success == True, "Adding course should succeed"
        print("SUCCESS: Course added to KRS")
        
        # Verify the course was added
        krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
        assert krs is not None, "KRS should be created"
        assert krs.status == KRSStatusEnum.DRAFT, f"New KRS should be in DRAFT status, but is {krs.status}"
        
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
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        assert len(details) == 2, f"Should have 2 courses in KRS, but has {len(details)}"
        print("SUCCESS: KRS now has 2 courses")
        
        # Test 3: Try to add duplicate course
        print("\n--- Test 3: Try to add duplicate course ---")
        success = add_course(nim, kode1, semester, db)
        print(f"Add duplicate course result: {success}")
        assert success == False, "Adding duplicate course should fail"
        print("SUCCESS: Duplicate course addition properly rejected")
        
        # Test 4: Validate KRS
        print("\n--- Test 4: Validate KRS ---")
        validation_result = validate_krs(nim, semester, db)
        print(f"Validation result: {validation_result.success}, Message: {validation_result.message}")
        assert validation_result.success == True, "Valid KRS should pass validation"
        print("SUCCESS: KRS validation passed")
        
        # Test 5: Submit KRS (should work since it passes validation)
        print("\n--- Test 5: Submit KRS ---")
        success = submit_krs(nim, semester, db)
        print(f"Submit KRS result: {success}")
        assert success == True, "Submitting valid KRS should succeed"
        
        # Reload KRS to check status
        krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
        assert krs.status == KRSStatusEnum.SUBMITTED, f"Status should be SUBMITTED, but is {krs.status}"
        print("SUCCESS: KRS submitted successfully, status changed to SUBMITTED")
        
        # Test 6: Approve KRS
        print("\n--- Test 6: Approve KRS ---")
        success = approve_krs(nim, semester, 101, db)
        print(f"Approve KRS result: {success}")
        assert success == True, "Approving submitted KRS should succeed"
        
        # Reload KRS to check status and advisor ID
        krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
        assert krs.status == KRSStatusEnum.APPROVED, f"Status should be APPROVED, but is {krs.status}"
        assert krs.dosen_pa_id == 101, f"Advisor ID should be 101, but is {krs.dosen_pa_id}"
        print("SUCCESS: KRS approved successfully, status changed to APPROVED and advisor assigned")
        
        # Clean up test data
        db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).delete()
        db.delete(krs)
        db.delete(matakuliah1)
        db.delete(matakuliah2)
        db.commit()
        
        print("\nAll KRS business logic tests passed successfully!")
        
    except Exception as e:
        print(f"ERROR: Error during KRS logic tests: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_krs_logic_simple()