"""
Debug script for KRS business logic
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS
from krs_system.krs_logic import add_course, get_or_create_krs
from krs_system.state_manager import KRSStatus
from pmb_system.database import DATABASE_URL


def debug_krs_logic():
    print("Debugging KRS business logic...")
    
    # Using the same database engine as PMB system
    engine = create_engine(DATABASE_URL, echo=True)  # Enable echo to see SQL
    
    # Create all tables defined in KRS models
    Base.metadata.create_all(bind=engine)
    
    # Test creating a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # First, try to delete the test course if it exists to avoid unique constraint errors
        existing_matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == "DBG999X").first()
        if existing_matakuliah:
            db.delete(existing_matakuliah)
            db.commit()
        
        # Create test matakuliah
        matakuliah1 = Matakuliah(
            kode="DBG999X",
            nama="Debug Course",
            sks=3,
            semester=2,
            hari="Selasa",
            jam_mulai=time(8, 0, 0),
            jam_selesai=time(10, 0, 0)
        )
        
        db.add(matakuliah1)
        db.commit()
        db.refresh(matakuliah1)
        
        print("Created test matakuliah")
        
        # Test the get_or_create_krs function directly
        print("\n--- Testing get_or_create_krs ---")
        krs = get_or_create_krs("9876543210", "2023/2024-2", db)
        print(f"KRS ID: {krs.id}, Status: {krs.status}")
        
        # Test add_course
        print("\n--- Testing add_course ---")
        success = add_course("9876543210", "DBG999X", "2023/2024-2", db)
        print(f"Add course result: {success}")
        
        # Check what happened to the KRS
        krs_check = db.query(KRS).filter(KRS.nim == "9876543210", KRS.semester == "2023/2024-2").first()
        if krs_check:
            print(f"Found KRS after add_course: ID={krs_check.id}, Status={krs_check.status}")
            print(f"Created at: {krs_check.created_at}")
            print(f"Updated at: {krs_check.updated_at}")
        else:
            print("No KRS found after add_course")
        
        # Check what happened to the KRS
        krs_check = db.query(KRS).filter(KRS.nim == "9876543210", KRS.semester == "2023/2024-2").first()
        if krs_check:
            print(f"Found KRS after add_course: ID={krs_check.id}, Status={krs_check.status}")
            print(f"Created at: {krs_check.created_at}")
            print(f"Updated at: {krs_check.updated_at}")
            
            # Check if the course was added
            from krs_system.models import KRSDetail
            details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_check.id).all()
            print(f"Number of courses in KRS: {len(details)}")
        else:
            print("No KRS found after add_course")
        
        # Clean up test data
        from krs_system.models import KRSDetail
        krs_for_cleanup = db.query(KRS).filter(KRS.nim == "9876543210", KRS.semester == "2023/2024-2").first()
        if krs_for_cleanup:
            details_to_delete = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_for_cleanup.id).all()
            for detail in details_to_delete:
                db.delete(detail)
            db.delete(krs_for_cleanup)
        
        # Also try to delete the matakuliah if it exists
        matakuliah_to_delete = db.query(Matakuliah).filter(Matakuliah.kode == "DBG999X").first()
        if matakuliah_to_delete:
            db.delete(matakuliah_to_delete)
        db.commit()
        
        print("\nDebug complete!")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    debug_krs_logic()