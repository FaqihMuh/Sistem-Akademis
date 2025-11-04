from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS
from krs_system.krs_logic import add_course
from krs_system.state_manager import KRSStatus
from pmb_system.database import DATABASE_URL

# Create fresh database
engine = create_engine(DATABASE_URL, echo=False)  # Turn off echo for cleaner output
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Create test course
    matakuliah = Matakuliah(
        kode='TEST999',
        nama='Test Course',
        sks=3,
        semester=2,
        hari='Senin',
        jam_mulai=time(8, 0, 0),
        jam_selesai=time(10, 0, 0)
    )
    db.add(matakuliah)
    db.commit()

    print("Course created successfully")
    
    # Test adding course
    result = add_course('1234567890', 'TEST999', '2025/1', db)
    print(f'Add course result: {result}')

    # Check what was created
    krs = db.query(KRS).filter(KRS.nim == '1234567890', KRS.semester == '2025/1').first()
    if krs:
        print(f'KRS found: ID={krs.id}, Status={krs.status}')
        from krs_system.models import KRSDetail
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        print(f'Details count: {len(details)}')
    else:
        print('No KRS found')
finally:
    db.close()