import sys
sys.path.append('.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS, KRSDetail
from krs_system.enums import KRSStatusEnum

def debug_add_course_step_by_step(nim, kode_mk, semester, db):
    """Debug version of add_course to see exactly where it fails"""
    from sqlalchemy.exc import IntegrityError
    
    try:
        print(f"Looking for course with kode: {kode_mk}")
        
        # Get the course
        matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == kode_mk).first()
        if not matakuliah:
            print(f"ERROR: Course with kode {kode_mk} not found!")
            course_count = db.query(Matakuliah).count()
            print(f"Total courses in DB: {course_count}")
            all_courses = db.query(Matakuliah).all()
            print(f"All course codes: {[c.kode for c in all_courses]}")
            return False  # Course doesn't exist
        
        print(f"Found course: {matakuliah.nama}")
        
        # Get existing KRS for this student and semester
        existing_krs = db.query(KRS).filter(
            KRS.nim == nim,
            KRS.semester == semester
        ).first()
        
        # If no existing KRS, create a new one in DRAFT status
        if not existing_krs:
            print("Creating new KRS")
            new_krs = KRS(
                nim=nim,
                semester=semester,
                status=KRSStatusEnum.DRAFT  # Use the direct enum import
            )
            db.add(new_krs)
            db.flush()  # Get the ID without committing
            krs = new_krs
            print(f"Created new KRS with ID: {krs.id}")
        else:
            krs = existing_krs
            print(f"Using existing KRS with ID: {krs.id}")
        
        # Check if course is already in KRS
        existing_detail = db.query(KRSDetail).filter(
            KRSDetail.krs_id == krs.id,
            KRSDetail.matakuliah_id == matakuliah.id
        ).first()
        
        if existing_detail:
            print("ERROR: Course already in KRS")
            return False  # Course already in KRS
        
        print("Adding course to KRS")
        # Add the course to KRS
        krs_detail = KRSDetail(
            krs_id=krs.id,
            matakuliah_id=matakuliah.id
        )
        db.add(krs_detail)
        print("Successfully added course to KRS")
        return True
        
    except IntegrityError as e:
        print(f"IntegrityError: {e}")
        return False
    except Exception as e:
        print(f"General exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_test():
    print("Creating in-memory database...")
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Creating test course...")
        # Create a course directly
        course = Matakuliah(
            kode="COMP101",
            nama="Programming I",
            sks=3,
            semester=1,
            hari="Senin",
            jam_mulai=time(8, 0),
            jam_selesai=time(10, 0)
        )
        db.add(course)
        db.commit()
        print("Course created successfully")
        
        # Verify the course exists
        found_course = db.query(Matakuliah).filter(Matakuliah.kode == "COMP101").first()
        if found_course:
            print(f"Course found: {found_course.nama}")
        else:
            print("Course NOT found in verification!")
            return
        
        print("Testing add_course step by step...")
        result = debug_add_course_step_by_step("1234567890", "COMP101", "2023/2024-1", db)
        print(f"debug_add_course result: {result}")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_test()