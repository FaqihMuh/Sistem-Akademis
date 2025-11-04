"""
Test script to verify the database fix works for PMB registration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pmb_system import database, models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def test_database_fix():
    """Test that the database configuration fix works properly"""
    
    print("Testing database configuration fix...")
    
    # Create a test database engine with the new configuration
    engine = database.engine
    models.Base.metadata.create_all(bind=engine)
    
    SessionLocal = database.SessionLocal
    db = SessionLocal()
    
    try:
        # Test creating a program studi to verify DB works
        from pmb_system.models import ProgramStudi, JalurMasukEnum
        
        prog_studi = db.query(ProgramStudi).filter(ProgramStudi.kode == "TST").first()
        if not prog_studi:
            prog_studi = ProgramStudi(
                kode="TST",
                nama="Test Prodi",
                fakultas="Test Fakultas"
            )
            db.add(prog_studi)
            db.commit()
            db.refresh(prog_studi)
        
        print(f"Created/Found program studi: {prog_studi.nama}")
        
        # Test creating a student (simplified version of registration)
        from pmb_system.models import CalonMahasiswa, StatusEnum
        
        # Clean up any existing test data
        existing_student = db.query(CalonMahasiswa).filter(
            CalonMahasiswa.email == "test.register@example.com"
        ).first()
        
        if existing_student:
            db.delete(existing_student)
            db.commit()
        
        # Create new test student (like registration would do)
        test_student = CalonMahasiswa(
            nama_lengkap="Test Registration Student",
            email="test.register@example.com", 
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat="Test Address 123",
            program_studi_id=prog_studi.id,
            jalur_masuk=JalurMasukEnum.SNBT,
            status=StatusEnum.PENDING  # Default status
        )
        
        db.add(test_student)
        db.commit()  # This is where the original error occurred
        db.refresh(test_student)
        
        print(f"Successfully registered student: {test_student.nama_lengkap}")
        print(f"Student email: {test_student.email}")
        print(f"Student status: {test_student.status}")
        
        # Clean up test data
        db.delete(test_student)
        db.commit()
        
        print("SUCCESS: Database fix works correctly!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database_fix()
    if not success:
        sys.exit(1)
    print("\nDatabase fix verification completed successfully!")