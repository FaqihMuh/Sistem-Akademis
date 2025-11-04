from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS
from krs_system.krs_logic import add_course
from krs_system.state_manager import KRSStatus
from pmb_system.database import DATABASE_URL

# Create fresh database
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Create test courses
    matakuliah1 = Matakuliah(
        kode='TEST991',
        nama='Test Course 1',
        sks=3,
        semester=2,
        hari='Senin',
        jam_mulai=time(8, 0, 0),
        jam_selesai=time(10, 0, 0)
    )
    matakuliah2 = Matakuliah(
        kode='TEST992',
        nama='Test Course 2',
        sks=4,
        semester=2,
        hari='Selasa',
        jam_mulai=time(10, 0, 0),
        jam_selesai=time(12, 0, 0)
    )
    db.add(matakuliah1)
    db.add(matakuliah2)
    db.commit()

    print("Courses created successfully")
    
    # Test adding first course
    result1 = add_course('1234567891', 'TEST991', '2025/1', db)
    print(f'Add first course result: {result1}')

    # Check KRS after first course
    krs = db.query(KRS).filter(KRS.nim == '1234567891', KRS.semester == '2025/1').first()
    if krs:
        print(f'After first add - KRS ID={krs.id}, Status={krs.status}')
        from krs_system.models import KRSDetail
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        print(f'After first add - Details count: {len(details)}')
    
    # Close session and create new one for second operation (to avoid transaction conflicts)
    db.close()
    db = SessionLocal()
    
    # Test adding second course to same KRS
    result2 = add_course('1234567891', 'TEST992', '2025/1', db)  # Same NIM and semester
    print(f'Add second course result: {result2}')

    # Check KRS after second course
    krs = db.query(KRS).filter(KRS.nim == '1234567891', KRS.semester == '2025/1').first()
    if krs:
        print(f'After second add - KRS ID={krs.id}, Status={krs.status}')
        from krs_system.models import KRSDetail
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        print(f'After second add - Details count: {len(details)}')
    else:
        print('No KRS found after second add')
finally:
    db.close()