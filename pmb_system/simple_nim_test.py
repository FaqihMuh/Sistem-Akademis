"""
Test script for the thread-safe NIM generation function
"""
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add the current directory to the path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum

def test_nim_generation():
    print("Testing NIM generation function...")
    
    # Create in-memory database for testing
    engine = create_engine('sqlite:///./test_nim_generation.db')
    Base.metadata.create_all(bind=engine)
    
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Import the function locally to avoid import errors
    from crud import generate_nim
    
    # Create a program studi
    db = SessionTesting()
    
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    
    # Create a calon mahasiswa
    calon_mahasiswa = CalonMahasiswa(
        nama_lengkap="John Doe",
        email="john.doe.nimtest@example.com",
        phone="081234567890",
        tanggal_lahir=datetime.now(),
        alamat="Jl. Contoh No. 123",
        program_studi_id=program_studi.id,
        jalur_masuk=JalurMasukEnum.SNBP,
        status=StatusEnum.PENDING  # Initially pending
    )
    db.add(calon_mahasiswa)
    db.commit()
    db.refresh(calon_mahasiswa)
    
    # Test NIM generation
    try:
        nim = generate_nim(db, calon_mahasiswa.id)
        print(f"Generated NIM: {nim}")
        
        # Verify format: [Tahun:4][Kode Prodi:3][Running Number:4]
        current_year = str(datetime.now().year)
        expected_prefix = current_year + program_studi.kode
        if nim.startswith(expected_prefix) and len(nim) == 11:  # 4 + 3 + 4
            print("[OK] NIM format is correct")
        else:
            print(f"[ERROR] NIM format is incorrect. Expected to start with {expected_prefix}, length 11, got {len(nim)}")
        
        # Test running number (should be 0001 for the first student)
        expected_running = "0001"
        if nim.endswith(expected_running):
            print("[OK] Running number is correct")
        else:
            print(f"[ERROR] Running number is incorrect. Got: {nim[-4:]}")
        
    except Exception as e:
        print(f"[ERROR] Error generating NIM: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    print("NIM generation test completed.\n")

def test_multiple_students():
    print("Testing multiple students in the same program...")
    
    # Create in-memory database for testing
    engine = create_engine('sqlite:///./test_multiple.db')
    Base.metadata.create_all(bind=engine)
    
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Import the function locally to avoid import errors
    from crud import generate_nim
    
    # Create a program studi
    db = SessionTesting()
    program_studi = ProgramStudi(
        kode="SIF",
        nama="Sistem Informasi",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    
    # Create multiple students and generate NIMs for them
    nims = []
    for i in range(1, 6):
        calon_mahasiswa = CalonMahasiswa(
            nama_lengkap=f"Student {i}",
            email=f"student{i}@example.com",
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat=f"Jl. Student {i} No. {i}",
            program_studi_id=program_studi.id,
            jalur_masuk=JalurMasukEnum.SNBT,
            status=StatusEnum.PENDING
        )
        db.add(calon_mahasiswa)
        db.commit()
        db.refresh(calon_mahasiswa)
        
        # Generate NIM
        nim = generate_nim(db, calon_mahasiswa.id)
        nims.append(nim)
        print(f"Student {i} NIM: {nim}")
    
    # Check if running numbers are sequential
    expected_current_year = str(datetime.now().year)
    expected_prefix = expected_current_year + program_studi.kode
    
    all_correct = True
    for i, nim in enumerate(nims, 1):
        if not nim.startswith(expected_prefix):
            print(f"[ERROR] NIM {nim} doesn't start with expected prefix {expected_prefix}")
            all_correct = False
            continue
            
        # Extract running number
        running_num = nim[-4:]
        expected_running = f"{i:04d}"
        if running_num != expected_running:
            print(f"[ERROR] NIM {nim} has wrong running number, expected {expected_running}, got {running_num}")
            all_correct = False
        else:
            print(f"[OK] NIM {nim} has correct running number {running_num}")
    
    if all_correct:
        print("[OK] All NIMs have correct sequential running numbers")
    else:
        print("[ERROR] Some NIMs have incorrect running numbers")
    
    db.close()
    print("Multiple students test completed.\n")

if __name__ == "__main__":
    test_nim_generation()
    test_multiple_students()
    print("All tests completed!")