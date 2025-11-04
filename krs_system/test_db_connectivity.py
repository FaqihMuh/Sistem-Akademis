"""
Test script to verify KRS models and database connectivity
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from krs_system.models import Base, Matakuliah, Prerequisite, KRS, KRSDetail
from pmb_system.database import DATABASE_URL  # Using the same database URL as PMB

def test_database_connectivity():
    print("Testing KRS database connectivity...")
    
    # Using the same database engine as PMB system
    engine = create_engine(DATABASE_URL, echo=True)
    
    # Create all tables defined in KRS models
    # NOTE: This will only create tables that don't already exist
    Base.metadata.create_all(bind=engine)
    
    print("KRS tables created successfully!")
    
    # Test creating a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test creating a sample matakuliah
        from datetime import time
        matakuliah = Matakuliah(
            kode="IF101",
            nama="Pengantar Informatika",
            sks=3,
            semester=1,
            hari="Senin",
            jam_mulai=time(8, 0, 0),  # Use Python time object
            jam_selesai=time(10, 0, 0)  # Use Python time object
        )
        
        db.add(matakuliah)
        db.commit()
        db.refresh(matakuliah)
        
        print(f"Successfully created matakuliah: {matakuliah.nama}")
        
        # Test querying
        found_matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == "IF101").first()
        if found_matakuliah:
            print(f"Successfully retrieved matakuliah: {found_matakuliah.nama}")
        
        # Clean up test data
        db.delete(matakuliah)
        db.commit()
        
        print("Database connectivity test completed successfully!")
        
    except Exception as e:
        print(f"Error during database test: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database_connectivity()