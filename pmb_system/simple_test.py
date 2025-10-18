from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum
from datetime import datetime

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pmb.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def test_program_studi_model():
    """Test ProgramStudi model creation"""
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    
    assert program_studi.kode == "TIK"
    assert program_studi.nama == "Teknik Informatika"
    assert program_studi.fakultas == "Fakultas Teknik"
    
    # Test kode length validation
    try:
        invalid_program_studi = ProgramStudi(
            kode="T",  # Too short
            nama="Teknik Informatika",
            fakultas="Fakultas Teknik"
        )
        assert False, "Should raise validation error for invalid kode length"
    except ValueError:
        pass  # Expected

    print("Program Studi model test passed!")


def test_calon_mahasiswa_model():
    """Test CalonMahasiswa model creation and validation"""
    # Valid data
    valid_data = {
        'nama_lengkap': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '081234567890',
        'tanggal_lahir': datetime.now(),
        'alamat': 'Jl. Contoh No. 123',
        'program_studi_id': 1,
        'jalur_masuk': JalurMasukEnum.SNBP
    }
    
    calon_mahasiswa = CalonMahasiswa(**valid_data)
    
    assert calon_mahasiswa.nama_lengkap == 'John Doe'
    assert calon_mahasiswa.email == 'john.doe@example.com'
    assert calon_mahasiswa.phone == '081234567890'
    
    # Test email validation
    assert CalonMahasiswa.validate_email_format('valid@email.com') == True
    assert CalonMahasiswa.validate_email_format('invalid-email') == False
    assert CalonMahasiswa.validate_email_format('@invalid.com') == False
    
    # Test phone validation
    assert CalonMahasiswa.validate_phone_format('081234567890') == True  # 12 digits
    assert CalonMahasiswa.validate_phone_format('0812345678') == True    # 10 digits (minimum)
    assert CalonMahasiswa.validate_phone_format('0812345678901') == True # 13 digits (maximum)
    assert CalonMahasiswa.validate_phone_format('08123456789012') == False # 14 digits - too long
    assert CalonMahasiswa.validate_phone_format('071234567890') == False # Doesn't start with 08
    assert CalonMahasiswa.validate_phone_format('181234567890') == False # Doesn't start with 08

    print("Calon Mahasiswa model test passed!")


def test_phone_format_validation():
    """Test Indonesian phone number format validation specifically"""
    # Valid formats
    assert CalonMahasiswa.validate_phone_format('081234567890') == True  # 12 digits
    assert CalonMahasiswa.validate_phone_format('08123456789') == True   # 11 digits
    assert CalonMahasiswa.validate_phone_format('0812345678901') == True # 13 digits (maximum)
    assert CalonMahasiswa.validate_phone_format('0812345678') == True    # 10 digits (minimum)
    
    # Invalid formats
    assert CalonMahasiswa.validate_phone_format('081234567') == False   # 9 digits - too short
    assert CalonMahasiswa.validate_phone_format('08123456789012') == False # 14 digits - too long
    assert CalonMahasiswa.validate_phone_format('071234567890') == False # Doesn't start with 08
    assert CalonMahasiswa.validate_phone_format('091234567890') == False # Doesn't start with 08
    
    # Test with spaces and hyphens
    assert CalonMahasiswa.validate_phone_format('0812 3456 7890') == True
    assert CalonMahasiswa.validate_phone_format('0812-3456-7890') == True
    assert CalonMahasiswa.validate_phone_format('0812 3456-7890') == True

    print("Phone format validation test passed!")


if __name__ == "__main__":
    test_program_studi_model()
    test_calon_mahasiswa_model()
    test_phone_format_validation()
    print("All tests passed!")