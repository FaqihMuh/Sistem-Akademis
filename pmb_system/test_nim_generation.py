"""
Test script for the thread-safe NIM generation function
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum
from database import SessionLocal
from crud import generate_nim
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

def test_nim_generation():
    print("Testing NIM generation function...")
    
    # Create in-memory database for testing
    engine = create_engine('sqlite:///./test_nim_generation.db', echo=True)
    Base.metadata.create_all(bind=engine)
    
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
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
        email="john.doe@example.com",
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
            print("✅ NIM format is correct")
        else:
            print(f"❌ NIM format is incorrect. Expected to start with {expected_prefix}")
        
        # Test running number (should be 0001 for the first student)
        expected_running = "0001"
        if nim.endswith(expected_running):
            print("✅ Running number is correct")
        else:
            print(f"❌ Running number is incorrect. Got: {nim[-4:]}")
        
    except Exception as e:
        print(f"❌ Error generating NIM: {e}")
    
    db.close()
    print("NIM generation test completed.\n")

def test_thread_safety():
    print("Testing thread safety (this may take a moment)...")
    
    # Create in-memory database for testing
    engine = create_engine('sqlite:///./test_thread_safety.db')
    Base.metadata.create_all(bind=engine)
    
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
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
    db.close()
    
    # Define a function to generate NIM for a new student
    def create_and_generate_nim(student_id):
        db = SessionTesting()
        try:
            # Create a new calon mahasiswa
            calon_mahasiswa = CalonMahasiswa(
                nama_lengkap=f"Student {student_id}",
                email=f"student{student_id}@example.com",
                phone="081234567890",
                tanggal_lahir=datetime.now(),
                alamat=f"Jl. Student {student_id} No. {student_id}",
                program_studi_id=program_studi.id,
                jalur_masuk=JalurMasukEnum.SNBT,
                status=StatusEnum.PENDING
            )
            db.add(calon_mahasiswa)
            db.commit()
            db.refresh(calon_mahasiswa)
            
            # Generate NIM
            nim = generate_nim(db, calon_mahasiswa.id)
            print(f"Thread {threading.current_thread().name}: Generated NIM {nim} for student {student_id}")
            return nim
        except Exception as e:
            print(f"Thread {threading.current_thread().name}: Error - {e}")
            return None
        finally:
            db.close()
    
    # Test with multiple threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_and_generate_nim, i) for i in range(1, 6)]
        nims = [future.result() for future in futures]
    
    print(f"Generated NIMs: {nims}")
    
    # Check if all NIMs are unique (they should be if thread-safe)
    unique_nims = set(nim for nim in nims if nim is not None)
    if len(unique_nims) == len([nim for nim in nims if nim is not None]):
        print("✅ All generated NIMs are unique - thread safety works")
    else:
        print("❌ Some NIMs are duplicated - thread safety issue")
    
    print("Thread safety test completed.\n")

if __name__ == "__main__":
    test_nim_generation()
    test_thread_safety()
    print("All tests completed!")