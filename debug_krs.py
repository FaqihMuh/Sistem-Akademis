import sys
sys.path.append('.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah
from krs_system.krs_logic import add_course

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
            print("Course NOT found!")
            return
        
        print("Testing add_course...")
        result = add_course("1234567890", "COMP101", "2023/2024-1", db)
        print(f"add_course result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_test()