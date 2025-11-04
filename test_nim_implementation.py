"""
Test to verify the new NIM column functionality
"""
import sys
import os

# Add the PMB system directory to Python path
pmb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pmb_system')
sys.path.insert(0, pmb_dir)

from models import CalonMahasiswa, ProgramStudi, StatusEnum, JalurMasukEnum
from database import engine, Base, SessionLocal
import crud
from sqlalchemy.orm import Session
from datetime import datetime

def test_nim_column():
    """Test that the NIM column works properly"""
    # Create in-memory database for testing
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    try:
        # Create a program studi
        program_studi = ProgramStudi(
            kode="001",
            nama="Teknik Informatika",
            fakultas="Fakultas Teknik"
        )
        db.add(program_studi)
        db.commit()
        db.refresh(program_studi)
        
        # Create a calon mahasiswa
        calon_mahasiswa = CalonMahasiswa(
            nama_lengkap="Test Student",
            email="test@example.com",
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat="Test Address",
            program_studi_id=program_studi.id,
            jalur_masuk=JalurMasukEnum.SNBT
        )
        db.add(calon_mahasiswa)
        db.commit()
        db.refresh(calon_mahasiswa)
        
        # Verify that the NIM is initially NULL
        assert calon_mahasiswa.nim is None, "NIM should be initially NULL"
        assert calon_mahasiswa.status == StatusEnum.PENDING, "Status should be PENDING initially"
        
        print("✓ NIM is initially NULL when status is PENDING")
        
        # Approve the student and generate NIM
        generated_nim = crud.generate_nim(db, calon_mahasiswa.id)
        
        # Refresh the object to get the updated values
        db.refresh(calon_mahasiswa)
        
        # Check that NIM is now set and status is approved
        assert calon_mahasiswa.nim is not None, "NIM should not be NULL after approval"
        assert calon_mahasiswa.nim == generated_nim, "NIM should match the generated NIM"
        assert calon_mahasiswa.status == StatusEnum.APPROVED, "Status should be APPROVED after approval"
        assert calon_mahasiswa.approved_at is not None, "approved_at should be set after approval"
        
        print("✓ NIM is properly set when status changes to APPROVED")
        print(f"✓ Generated NIM: {calon_mahasiswa.nim}")
        
        # Verify NIM format: [Tahun:4][Kode Prodi:3][Running Number:4]
        current_year = str(datetime.now().year)
        expected_prefix = current_year + program_studi.kode
        assert calon_mahasiswa.nim.startswith(expected_prefix), f"NIM should start with {expected_prefix}"
        assert len(calon_mahasiswa.nim) == 11, "NIM should have 11 characters (4 year + 3 kode + 4 running number)"
        
        print("✓ NIM format is correct: [Year][Program Code][Running Number]")
        
        print("\nAll tests passed! The NIM column functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_nim_column()
    if not success:
        sys.exit(1)