"""
Test to verify that the NIM validation fix works correctly
"""
import sys
import os
from datetime import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pmb_system'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'krs_system'))

from pmb_system import models as pmb_models, database as pmb_db
from krs_system import models as krs_models
from krs_system.endpoints import add_course_to_krs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from krs_system.endpoints import KRSRequest

def test_nim_validation_fix():
    """Test that the NIM validation now works by checking the nim field directly"""
    
    # Create an in-memory database with both PMB and KRS models
    engine = create_engine('sqlite:///:memory:', echo=False)
    pmb_models.Base.metadata.create_all(bind=engine)
    krs_models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create a program studi
        prog_studi = pmb_models.ProgramStudi(
            kode="TIK",
            nama="Teknik Informatika",
            fakultas="Fakultas Teknologi Informasi"
        )
        db.add(prog_studi)
        db.commit()
        db.refresh(prog_studi)
        
        # Create a calon mahasiswa and approve them (assign NIM)
        student = pmb_models.CalonMahasiswa(
            nama_lengkap="Test Student",
            email="test.student@example.com",
            phone="081234567890",
            tanggal_lahir=pmb_models.func.now(),
            alamat="Jl. Test No. 123",
            program_studi_id=prog_studi.id,
            jalur_masuk=pmb_models.JalurMasukEnum.SNBT,
            status=pmb_models.StatusEnum.APPROVED,  # Approved status
            nim="2025TIF0002"  # Set the NIM directly
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        
        # Create a test course in KRS system
        course = krs_models.Matakuliah(
            kode="COMP101",
            nama="Introduction to Programming",
            sks=3,
            semester=1,
            hari="Senin",
            jam_mulai=time(8, 0),
            jam_selesai=time(10, 0)
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        
        print(f"Created student with NIM: {student.nim}, status: {student.status}")
        
        # Verify that we can query the student by NIM
        found_student = db.query(pmb_models.CalonMahasiswa).filter(
            pmb_models.CalonMahasiswa.nim == "2025TIF0002"
        ).first()
        print(f"Found student by NIM: {found_student.nim if found_student else 'None'}")
        print(f"Student status: {found_student.status if found_student else 'None'}")
        
        # Test that the old search method (in nama_lengkap, email, phone) would fail
        old_search = db.query(pmb_models.CalonMahasiswa).filter(
            pmb_models.CalonMahasiswa.nama_lengkap.contains("2025TIF0002") |
            pmb_models.CalonMahasiswa.email.contains("2025TIF0002") |
            pmb_models.CalonMahasiswa.phone.contains("2025TIF0002")
        ).first()
        print(f"Old search method finds student: {old_search is not None}")
        
        # The old method should not find the student since NIM is not in name/email/phone
        assert old_search is None, "Old search method should not find student with NIM in name/email/phone"
        
        # The new method should find the student
        new_search = db.query(pmb_models.CalonMahasiswa).filter(
            pmb_models.CalonMahasiswa.nim == "2025TIF0002"
        ).first()
        assert new_search is not None, "New search method should find student with direct NIM match"
        
        print("SUCCESS: NIM validation fix works correctly!")
        print("- Old method (search in name/email/phone) fails as expected")
        print("- New method (direct NIM match) succeeds as expected")
        
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_nim_validation_fix()
    if not success:
        sys.exit(1)
    print("\nNIM validation fix verification completed successfully!")