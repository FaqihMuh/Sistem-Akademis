"""
Comprehensive test for KRS system models and relationships
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, Prerequisite, KRS, KRSDetail, KRSStatusEnum
from pmb_system.database import DATABASE_URL

def test_comprehensive_krs_system():
    print("Testing comprehensive KRS system functionality...")
    
    # Using the same database engine as PMB system
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Create all tables defined in KRS models
    Base.metadata.create_all(bind=engine)
    
    # Test creating a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test 1: Create matakuliah entries
        matakuliah1 = Matakuliah(
            kode="IF201",
            nama="Pengantar Informatika",
            sks=3,
            semester=1,
            hari="Senin",
            jam_mulai=time(8, 0, 0),
            jam_selesai=time(10, 0, 0)
        )
        
        matakuliah2 = Matakuliah(
            kode="IF202",
            nama="Algoritma dan Pemrograman",
            sks=4,
            semester=1,
            hari="Selasa",
            jam_mulai=time(9, 0, 0),
            jam_selesai=time(12, 0, 0)
        )
        
        db.add(matakuliah1)
        db.add(matakuliah2)
        db.commit()
        db.refresh(matakuliah1)
        db.refresh(matakuliah2)
        
        print(f"SUCCESS: Created matakuliah: {matakuliah1.nama} and {matakuliah2.nama}")
        
        # Test 2: Create prerequisite relationship
        prerequisite = Prerequisite(
            matakuliah_id=matakuliah2.id,
            prerequisite_id=matakuliah1.id
        )
        
        db.add(prerequisite)
        db.commit()
        db.refresh(prerequisite)
        
        print(f"SUCCESS: Created prerequisite relationship: {matakuliah2.nama} requires {matakuliah1.nama}")
        
        # Verify the relationships work
        prereq_matakuliah = db.query(Matakuliah).filter(Matakuliah.id == matakuliah2.id).first()
        print(f"SUCCESS: Matakuliah {prereq_matakuliah.nama} has prerequisites: {[p.matakuliah.nama for p in prereq_matakuliah.prerequisites]}")
        
        # Test 3: Create KRS entry
        krs = KRS(
            nim="1234567890",
            semester="2023/2024-1",
            status=KRSStatusEnum.DRAFT,
            dosen_pa_id=1  # Using as integer, not as foreign key
        )
        
        db.add(krs)
        db.commit()
        db.refresh(krs)
        
        print(f"SUCCESS: Created KRS for student {krs.nim} with status {krs.status.value}")
        
        # Test 4: Create KRS Detail entry
        krs_detail = KRSDetail(
            krs_id=krs.id,
            matakuliah_id=matakuliah1.id
        )
        
        db.add(krs_detail)
        db.commit()
        db.refresh(krs_detail)
        
        print(f"SUCCESS: Added matakuliah {matakuliah1.nama} to KRS")
        
        # Test 5: Verify all relationships work in both directions
        # Get KRS and check its details
        retrieved_krs = db.query(KRS).filter(KRS.id == krs.id).first()
        print(f"SUCCESS: KRS has {len(retrieved_krs.krs_details)} course(s)")
        
        # Get matakuliah and check courses that have it as prerequisite
        retrieved_matakuliah = db.query(Matakuliah).filter(Matakuliah.id == matakuliah1.id).first()
        print(f"SUCCESS: Matakuliah {retrieved_matakuliah.nama} is prerequisite for {[p.matakuliah.nama for p in retrieved_matakuliah.prerequisite_for]} course(s)")
        
        # Test 6: Cleanup test data
        db.delete(krs_detail)
        db.delete(krs)
        db.delete(prerequisite)
        db.delete(matakuliah1)
        db.delete(matakuliah2)
        db.commit()
        
        print("SUCCESS: All comprehensive tests passed successfully!")
        
    except Exception as e:
        print(f"ERROR: Error during comprehensive test: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_comprehensive_krs_system()