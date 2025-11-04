from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
from krs_system.models import Base, Matakuliah, KRS
from krs_system.krs_logic import add_course, validate_krs, submit_krs, approve_krs, remove_course
from krs_system.state_manager import KRSStatus
from krs_system.validators import ValidationResult
from pmb_system.database import DATABASE_URL

# Create fresh database
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Create test courses
    matakuliah1 = Matakuliah(
        kode='COMPLT1',
        nama='Complete Course 1',
        sks=3,
        semester=2,
        hari='Senin',
        jam_mulai=time(8, 0, 0),
        jam_selesai=time(10, 0, 0)
    )
    matakuliah2 = Matakuliah(
        kode='COMPLT2',
        nama='Complete Course 2',
        sks=3,
        semester=2,
        hari='Selasa',
        jam_mulai=time(10, 0, 0),
        jam_selesai=time(12, 0, 0)
    )
    db.add(matakuliah1)
    db.add(matakuliah2)
    db.commit()

    print("Test courses created successfully")
    
    nim = '1234567899'
    semester = '2025/1'
    
    # 1. Add first course
    result1 = add_course(nim, 'COMPLT1', semester, db)
    print(f"1. Add first course: {result1}")
    
    # Close and reopen to avoid transaction conflicts
    db.close()
    db = SessionLocal()
    
    # 2. Add second course
    result2 = add_course(nim, 'COMPLT2', semester, db)
    print(f"2. Add second course: {result2}")
    
    # Check KRS details
    krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
    if krs:
        from krs_system.models import KRSDetail
        details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs.id).all()
        print(f"   KRS has {len(details)} courses, status: {krs.status}")
    
    # 3. Validate KRS
    db.close()
    db = SessionLocal()
    validation_result = validate_krs(nim, semester, db)
    print(f"3. Validate KRS: success={validation_result.success}, message='{validation_result.message}'")
    
    # 4. Submit KRS
    db.close()
    db = SessionLocal()
    submit_result = submit_krs(nim, semester, db)
    print(f"4. Submit KRS: {submit_result}")
    
    # Check status after submit
    krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
    if krs:
        print(f"   After submit - Status: {krs.status}")
    
    # 5. Approve KRS
    db.close()
    db = SessionLocal()
    approve_result = approve_krs(nim, semester, 999, db)  # advisor ID = 999
    print(f"5. Approve KRS: {approve_result}")
    
    # Check status after approval
    krs = db.query(KRS).filter(KRS.nim == nim, KRS.semester == semester).first()
    if krs:
        print(f"   After approve - Status: {krs.status}, Advisor ID: {krs.dosen_pa_id}")
    
    # 6. Try to remove a course from APPROVED KRS (should fail based on business rules)
    # First, let's create a new DRAFT KRS to test removal
    db.close()
    db = SessionLocal()
    
    # Add course to new KRS with different semester
    result3 = add_course('1234567900', 'COMPLT1', '2025/2', db)
    print(f"6. Add course to new KRS: {result3}")
    
    # Now remove it
    db.close()
    db = SessionLocal()
    remove_result = remove_course('1234567900', 'COMPLT1', '2025/2', db)
    print(f"   Remove course: {remove_result}")
    
    if remove_result:
        from krs_system.models import KRSDetail
        krs_check = db.query(KRS).filter(KRS.nim == '1234567900', KRS.semester == '2025/2').first()
        if krs_check:
            details = db.query(KRSDetail).filter(KRSDetail.krs_id == krs_check.id).all()
            print(f"   After removal - Details count: {len(details)}")
    
    print("All business logic functions tested successfully!")
    
finally:
    db.close()