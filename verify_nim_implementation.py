import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'pmb_system'))

from pmb_system import models, database, crud
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_nim_functionality():
    print("Testing NIM functionality...")
    
    # Create in-memory database
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Create a program studi
        program_studi = models.ProgramStudi(
            kode='001',
            nama='Teknik Informatika',
            fakultas='Fakultas Teknik'
        )
        db.add(program_studi)
        db.commit()
        db.refresh(program_studi)

        # Create a calon mahasiswa
        calon_mahasiswa = models.CalonMahasiswa(
            nama_lengkap='Test Student',
            email='test@example.com',
            phone='081234567890',
            tanggal_lahir=datetime.now(),
            alamat='Test Address',
            program_studi_id=program_studi.id,
            jalur_masuk=models.JalurMasukEnum.SNBT
        )
        db.add(calon_mahasiswa)
        db.commit()
        db.refresh(calon_mahasiswa)
        
        print(f'Initial state - NIM: {calon_mahasiswa.nim}, Status: {calon_mahasiswa.status}')
        
        # Verify NIM is initially NULL
        assert calon_mahasiswa.nim is None, "NIM should be initially NULL"
        assert calon_mahasiswa.status == models.StatusEnum.PENDING, "Status should be PENDING initially"
        
        # Approve the student and generate NIM
        generated_nim = crud.generate_nim(db, calon_mahasiswa.id)
        print(f'Generated NIM: {generated_nim}')
        
        # Refresh the object to get the updated values
        db.refresh(calon_mahasiswa)
        
        print(f'Final state - NIM: {calon_mahasiswa.nim}, Status: {calon_mahasiswa.status}, Approved At: {calon_mahasiswa.approved_at}')
        
        # Check that NIM is now set and status is approved
        assert calon_mahasiswa.nim is not None, "NIM should not be NULL after approval"
        assert calon_mahasiswa.nim == generated_nim, "NIM should match the generated NIM"
        assert calon_mahasiswa.status == models.StatusEnum.APPROVED, "Status should be APPROVED after approval"
        assert calon_mahasiswa.approved_at is not None, "approved_at should be set after approval"
        
        print('All tests passed! The NIM column functionality is working correctly.')
        
        return True
        
    except Exception as e:
        print(f'Test failed with error: {e}')
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_nim_functionality()
    if success:
        print("\n✅ Implementation is working correctly!")
    else:
        print("\n❌ Implementation has issues!")
        sys.exit(1)