"""
Test script for the thread-safe NIM generation function - simulating real-world usage
"""
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum

def test_real_world_scenario():
    print("Testing real-world NIM generation scenario...")
    
    # Create in-memory database for testing
    engine = create_engine('sqlite:///./test_real_world.db')
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
    
    # Create multiple students first, but don't approve them yet
    students = []
    for i in range(1, 6):
        calon_mahasiswa = CalonMahasiswa(
            nama_lengkap=f"Student {i}",
            email=f"student{i}.real@example.com",
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
        students.append(calon_mahasiswa)
    
    # Now approve them one by one (simulating real usage)
    nims = []
    for i, student in enumerate(students, 1):
        # Create a fresh session for each approval to simulate separate API calls
        fresh_db = SessionTesting()
        try:
            # Generate NIM and approve the student (as done in the actual API)
            nim = generate_nim(fresh_db, student.id)
            
            # Update status and approved_at (as done in main.py)
            from models import CalonMahasiswa, StatusEnum
            mahasiswa = fresh_db.query(CalonMahasiswa).filter(CalonMahasiswa.id == student.id).first()
            if mahasiswa:
                mahasiswa.status = StatusEnum.APPROVED
                mahasiswa.approved_at = datetime.now()
                fresh_db.commit()
                fresh_db.refresh(mahasiswa)
            
            nims.append(nim)
            print(f"Student {i} NIM: {nim}")
        finally:
            fresh_db.close()
    
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
        print("[OK] All NIMs have correct sequential running numbers in real-world scenario")
    else:
        print("[ERROR] Some NIMs have incorrect running numbers in real-world scenario")
    
    db.close()
    print("Real-world scenario test completed.\n")

def test_format():
    print("Testing NIM format requirements...")
    
    # Create in-memory database for testing
    engine = create_engine('sqlite:///./test_format.db')
    Base.metadata.create_all(bind=engine)
    
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Import the function locally to avoid import errors
    from crud import generate_nim
    
    db = SessionTesting()
    
    # Create a program studi with 3-character code
    program_studi = ProgramStudi(
        kode="TIK",  # 3 characters as required
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    
    # Create a calon mahasiswa
    calon_mahasiswa = CalonMahasiswa(
        nama_lengkap="Format Test",
        email="format.test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime.now(),
        alamat="Jl. Format Test No. 1",
        program_studi_id=program_studi.id,
        jalur_masuk=JalurMasukEnum.SNBP,
        status=StatusEnum.PENDING
    )
    db.add(calon_mahasiswa)
    db.commit()
    db.refresh(calon_mahasiswa)
    
    # Test NIM generation
    try:
        nim = generate_nim(db, calon_mahasiswa.id)
        print(f"Generated NIM: {nim}")
        
        # Check format: [Tahun:4][Kode Prodi:3][Running Number:4]
        current_year = str(datetime.now().year)
        expected_length = 4 + 3 + 4  # 11 characters total
        
        if len(nim) == expected_length:
            print(f"[OK] NIM has correct length of {expected_length} characters")
        else:
            print(f"[ERROR] NIM has incorrect length {len(nim)}, expected {expected_length}")
        
        # Check year part
        if nim.startswith(current_year):
            print(f"[OK] NIM starts with correct year {current_year}")
        else:
            print(f"[ERROR] NIM doesn't start with current year {current_year}, got {nim[:4]}")
        
        # Check program code part
        expected_code = program_studi.kode
        if nim[4:7] == expected_code:
            print(f"[OK] NIM has correct program code {expected_code} at position 4-6")
        else:
            print(f"[ERROR] NIM has incorrect program code, expected {expected_code}, got {nim[4:7]}")
        
        # Check running number part
        running_number = nim[7:]  # Last 4 characters
        if len(running_number) == 4 and running_number.isdigit():
            print(f"[OK] NIM has correct running number format {running_number}")
        else:
            print(f"[ERROR] NIM has incorrect running number format {running_number}")
            
        # Example check
        example_nim1 = f"{current_year}0010001"  # For a program with code "001"
        example_nim2 = f"{current_year}0020001"  # For a program with code "002"
        print(f"\nExample formats:")
        print(f"  For program code '001': {example_nim1}")
        print(f"  For program code '002': {example_nim2}")
        print(f"  Our generated: {nim}")
        
    except Exception as e:
        print(f"[ERROR] Error generating NIM: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    print("Format test completed.\n")

if __name__ == "__main__":
    test_format()
    test_real_world_scenario()
    print("All tests completed!")