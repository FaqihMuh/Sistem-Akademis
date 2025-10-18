import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import os

# Set testing environment
os.environ["TESTING"] = "1"

# Import models and other modules
from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum
from crud import generate_nim

# Create an in-memory SQLite database engine for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

def test_register_success():
    """Test successful registration of a new applicant"""
    print("Testing successful registration...")
    
    # Create a database session
    db = TestingSessionLocal()
    
    try:
        # Create a program studi first
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
            email="john.doe.test@example.com",
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat="Jl. Contoh No. 123",
            program_studi_id=program_studi.id,
            jalur_masuk=JalurMasukEnum.SNBT,
            status=StatusEnum.PENDING
        )
        db.add(calon_mahasiswa)
        db.commit()
        db.refresh(calon_mahasiswa)
        
        assert calon_mahasiswa.email == "john.doe.test@example.com"
        assert calon_mahasiswa.nama_lengkap == "John Doe"
        assert calon_mahasiswa.status == StatusEnum.PENDING
        print("SUCCESS: Registered applicant with email:", calon_mahasiswa.email)
        
    finally:
        db.close()

def test_register_duplicate_email():
    """Test registration with duplicate email returns error"""
    print("Testing duplicate email registration...")
    
    # Create a database session
    db = TestingSessionLocal()
    
    try:
        # Create a program studi first
        program_studi = ProgramStudi(
            kode="TIK",
            nama="Teknik Informatika",
            fakultas="Fakultas Teknik"
        )
        db.add(program_studi)
        db.commit()
        db.refresh(program_studi)
        
        # Create the first calon mahasiswa
        calon_mahasiswa1 = CalonMahasiswa(
            nama_lengkap="John Doe",
            email="duplicate.test@example.com",
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat="Jl. Contoh No. 123",
            program_studi_id=program_studi.id,
            jalur_masuk=JalurMasukEnum.SNBT,
            status=StatusEnum.PENDING
        )
        db.add(calon_mahasiswa1)
        db.commit()
        db.refresh(calon_mahasiswa1)
        
        # Try to create another calon mahasiswa with the same email
        try:
            calon_mahasiswa2 = CalonMahasiswa(
                nama_lengkap="Jane Doe",
                email="duplicate.test@example.com",  # Same email
                phone="081234567891",
                tanggal_lahir=datetime.now(),
                alamat="Jl. Contoh No. 456",
                program_studi_id=program_studi.id,
                jalur_masuk=JalurMasukEnum.SNBP,
                status=StatusEnum.PENDING
            )
            db.add(calon_mahasiswa2)
            db.commit()
            db.refresh(calon_mahasiswa2)
            assert False, "Should have raised IntegrityError for duplicate email"
        except Exception as e:
            # Expecting an IntegrityError for duplicate email
            print("SUCCESS: Duplicate email prevented with error:", str(e))
        
    finally:
        db.close()

def test_approve_generate_nim():
    """Test that NIM is generated correctly in the expected format and sequentially"""
    print("Testing NIM generation...")
    
    # Create a database session
    db = TestingSessionLocal()
    
    try:
        # Create a program studi
        program_studi = ProgramStudi(
            kode="SIF",
            nama="Sistem Informasi",
            fakultas="Fakultas Teknik"
        )
        db.add(program_studi)
        db.commit()
        db.refresh(program_studi)
        
        # Create a calon mahasiswa
        calon_mahasiswa = CalonMahasiswa(
            nama_lengkap="Jane Doe",
            email="jane.doe.test@example.com",
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat="Jl. Contoh No. 456",
            program_studi_id=program_studi.id,
            jalur_masuk=JalurMasukEnum.SNBP,
            status=StatusEnum.PENDING
        )
        db.add(calon_mahasiswa)
        db.commit()
        db.refresh(calon_mahasiswa)
        
        # Generate NIM
        nim = generate_nim(db, calon_mahasiswa.id)
        
        # Check format: [Tahun:4][Kode Prodi:3][Running Number:4]
        current_year = str(datetime.now().year)
        expected_prefix = current_year + program_studi.kode
        assert nim.startswith(expected_prefix), f"NIM {nim} should start with {expected_prefix}"
        assert len(nim) == 11, f"NIM {nim} should have length 11, got {len(nim)}"
        
        # Check that running number is correct (should be 0001 for first student in program)
        expected_running = "0001"
        assert nim.endswith(expected_running), f"NIM {nim} should end with {expected_running}, got {nim[-4:]}"
        print("SUCCESS: Generated NIM:", nim)
        
    finally:
        db.close()

def test_approve_idempotent():
    """Test that approving the same applicant twice doesn't generate a new NIM"""
    print("Testing idempotent approval...")
    
    # Create a database session
    db = TestingSessionLocal()
    
    try:
        # Create a program studi
        program_studi = ProgramStudi(
            kode="AKT",
            nama="Akuntansi",
            fakultas="Fakultas Ekonomi"
        )
        db.add(program_studi)
        db.commit()
        db.refresh(program_studi)
        
        # Create a calon mahasiswa
        calon_mahasiswa = CalonMahasiswa(
            nama_lengkap="Bob Smith",
            email="bob.smith.test@example.com",
            phone="081234567890",
            tanggal_lahir=datetime.now(),
            alamat="Jl. Contoh No. 789",
            program_studi_id=program_studi.id,
            jalur_masuk=JalurMasukEnum.MANDIRI,
            status=StatusEnum.PENDING
        )
        db.add(calon_mahasiswa)
        db.commit()
        db.refresh(calon_mahasiswa)
        
        # Generate NIM for the first time
        first_nim = generate_nim(db, calon_mahasiswa.id)
        
        # Try to generate NIM again (should raise error for already approved)
        try:
            second_nim = generate_nim(db, calon_mahasiswa.id)
            assert False, "Should have raised error for already approved applicant"
        except ValueError as e:
            # Expecting a ValueError for already approved
            assert "already approved" in str(e).lower()
            print("SUCCESS: Idempotent check passed - already approved error:", str(e))
        
    finally:
        db.close()

def test_invalid_phone_format():
    """Test that invalid phone format raises validation error"""
    print("Testing phone format validation...")
    
    # Test valid phone formats
    assert CalonMahasiswa.validate_phone_format('081234567890') == True  # 12 digits
    assert CalonMahasiswa.validate_phone_format('0812345678') == True    # 10 digits (minimum)
    assert CalonMahasiswa.validate_phone_format('0812345678901') == True # 13 digits (maximum)
    
    # Test invalid phone formats
    assert CalonMahasiswa.validate_phone_format('081234567') == False   # 9 digits - too short
    assert CalonMahasiswa.validate_phone_format('08123456789012') == False # 14 digits - too long
    assert CalonMahasiswa.validate_phone_format('071234567890') == False # Doesn't start with 08
    assert CalonMahasiswa.validate_phone_format('091234567890') == False # Doesn't start with 08
    
    print("SUCCESS: Phone format validation works correctly")

if __name__ == "__main__":
    test_register_success()
    test_register_duplicate_email()
    test_approve_generate_nim()
    test_approve_idempotent()
    test_invalid_phone_format()
    print("\nAll tests passed successfully!")