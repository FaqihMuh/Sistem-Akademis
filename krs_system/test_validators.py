"""
Test script for KRS validators
"""
from sqlalchemy import create_engine, Time
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, Prerequisite, KRS, KRSDetail
from krs_system.validators import run_validations, ValidationResult
from pmb_system.database import DATABASE_URL


def test_validators():
    print("Testing KRS validators...")
    
    # Using the same database engine as PMB system
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Create all tables defined in KRS models
    Base.metadata.create_all(bind=engine)
    
    # Test creating a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create test matakuliah
        matakuliah1 = Matakuliah(
            kode="TEST101",
            nama="Struktur Data",
            sks=4,
            semester=3,
            hari="Senin",
            jam_mulai=time(8, 0, 0),
            jam_selesai=time(10, 0, 0)
        )
        
        matakuliah2 = Matakuliah(
            kode="TEST102",
            nama="Algoritma Lanjut",
            sks=3,
            semester=3,
            hari="Senin",
            jam_mulai=time(10, 30, 0),
            jam_selesai=time(12, 30, 0)
        )
        
        # This course will conflict in time with matakuliah1
        matakuliah3 = Matakuliah(
            kode="TEST103",
            nama="Matematika Diskrit",
            sks=3,
            semester=3,
            hari="Senin",  # Same day as matakuliah1
            jam_mulai=time(9, 0, 0),  # Overlapping time
            jam_selesai=time(11, 0, 0)
        )
        
        db.add(matakuliah1)
        db.add(matakuliah2)
        db.add(matakuliah3)
        db.commit()
        db.refresh(matakuliah1)
        db.refresh(matakuliah2)
        db.refresh(matakuliah3)
        
        print("Created test matakuliah")
        
        # Create test KRS
        test_krs = KRS(
            nim="1234567890",
            semester="2023/2024-1",
            status=None,  # We're just testing validation
            dosen_pa_id=1
        )
        
        db.add(test_krs)
        db.commit()
        db.refresh(test_krs)
        
        print("Created test KRS")
        
        # Test 1: Valid KRS (below 24 SKS, no conflicts, no duplicates)
        print("\n--- Test 1: Valid KRS ---")
        krs_detail1 = KRSDetail(
            krs_id=test_krs.id,
            matakuliah_id=matakuliah1.id
        )
        
        krs_detail2 = KRSDetail(
            krs_id=test_krs.id,
            matakuliah_id=matakuliah2.id
        )
        
        db.add(krs_detail1)
        db.add(krs_detail2)
        db.commit()
        
        result = run_validations(test_krs.id, db)
        print(f"Validation result: {result.success}, Message: {result.message}")
        assert result.success == True, "Valid KRS should pass validation"
        print("SUCCESS: Valid KRS passed validation")
        
        # Clean up for next test
        db.delete(krs_detail1)
        db.delete(krs_detail2)
        db.commit()
        
        # Test 2: Too many SKS
        print("\n--- Test 2: Too many SKS (>24) ---")
        # Add many courses to exceed 24 SKS
        for i in range(7):  # 7 courses * 4 SKS = 28 SKS
            matkul = Matakuliah(
                kode=f"IF40{i}",
                nama=f"Mata Kuliah {i}",
                sks=4,
                semester=4,
                hari="Selasa",
                jam_mulai=time(8, 0, 0),
                jam_selesai=time(10, 0, 0)
            )
            db.add(matkul)
            db.commit()
            db.refresh(matkul)
            
            detail = KRSDetail(
                krs_id=test_krs.id,
                matakuliah_id=matkul.id
            )
            
            db.add(detail)
        
        db.commit()
        result = run_validations(test_krs.id, db)
        print(f"Validation result: {result.success}, Message: {result.message}")
        assert result.success == False, "KRS with >24 SKS should fail validation"
        assert "melebihi batas maksimum" in result.message, "Error message should mention SKS limit"
        print("SUCCESS: KRS with too many SKS failed validation as expected")
        
        # Clean up for next test
        # Remove all KRSDetail entries for this KRS
        db.query(KRSDetail).filter(KRSDetail.krs_id == test_krs.id).delete()
        # Remove the extra matakuliah
        for i in range(7):
            matkul = db.query(Matakuliah).filter(Matakuliah.kode == f"IF40{i}").first()
            if matkul:
                db.delete(matkul)
        db.commit()
        
        # Test 3: Schedule conflict
        print("\n--- Test 3: Schedule conflict ---")
        detail1 = KRSDetail(
            krs_id=test_krs.id,
            matakuliah_id=matakuliah1.id  # 8:00-10:00
        )
        
        detail2 = KRSDetail(
            krs_id=test_krs.id,
            matakuliah_id=matakuliah3.id  # 9:00-11:00 (overlaps with matakuliah1)
        )
        
        db.add(detail1)
        db.add(detail2)
        db.commit()
        
        result = run_validations(test_krs.id, db)
        print(f"Validation result: {result.success}, Message: {result.message}")
        assert result.success == False, "KRS with schedule conflicts should fail validation"
        assert "Konflik jadwal" in result.message, "Error message should mention schedule conflict"
        print("SUCCESS: KRS with schedule conflict failed validation as expected")
        
        # Clean up for next test
        db.delete(detail1)
        db.delete(detail2)
        db.commit()
        
        # Test 4: Duplicate course
        print("\n--- Test 4: Duplicate course ---")
        detail1 = KRSDetail(
            krs_id=test_krs.id,
            matakuliah_id=matakuliah1.id
        )
        
        detail2 = KRSDetail(  # Same course as detail1
            krs_id=test_krs.id,
            matakuliah_id=matakuliah1.id
        )
        
        db.add(detail1)
        db.add(detail2)
        db.commit()
        
        result = run_validations(test_krs.id, db)
        print(f"Validation result: {result.success}, Message: {result.message}")
        assert result.success == False, "KRS with duplicate courses should fail validation"
        assert "diambil lebih dari sekali" in result.message, "Error message should mention duplicate"
        print("SUCCESS: KRS with duplicate course failed validation as expected")
        
        # Clean up all test data
        db.query(KRSDetail).filter(KRSDetail.krs_id == test_krs.id).delete()
        db.delete(test_krs)
        db.delete(matakuliah1)
        db.delete(matakuliah2)
        db.delete(matakuliah3)
        db.commit()
        
        print("\nAll validation tests passed successfully!")
        
    except Exception as e:
        print(f"ERROR: Error during validation tests: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_validators()