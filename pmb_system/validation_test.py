import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import CalonMahasiswa, ProgramStudi, JalurMasukEnum
from datetime import datetime

def test_calon_mahasiswa_validation():
    """Test CalonMahasiswa validation logic"""
    
    # Test email validation
    assert CalonMahasiswa.validate_email_format('valid@email.com') == True
    assert CalonMahasiswa.validate_email_format('user.name@domain.co.id') == True
    assert CalonMahasiswa.validate_email_format('invalid-email') == False
    assert CalonMahasiswa.validate_email_format('@invalid.com') == False
    assert CalonMahasiswa.validate_email_format('invalid@') == False
    assert CalonMahasiswa.validate_email_format('invalid@.com') == False
    
    print("Email validation tests passed!")

    # Test phone validation
    assert CalonMahasiswa.validate_phone_format('081234567890') == True  # 12 digits
    assert CalonMahasiswa.validate_phone_format('08123456789') == True   # 11 digits
    assert CalonMahasiswa.validate_phone_format('0812345678901') == True # 13 digits
    assert CalonMahasiswa.validate_phone_format('0812345678') == True    # 10 digits
    
    # Invalid formats
    assert CalonMahasiswa.validate_phone_format('081234567') == False   # 9 digits - too short
    assert CalonMahasiswa.validate_phone_format('08123456789012') == False # 14 digits - too long
    assert CalonMahasiswa.validate_phone_format('071234567890') == False # Doesn't start with 08
    assert CalonMahasiswa.validate_phone_format('091234567890') == False # Doesn't start with 08
    
    # Test with spaces and hyphens
    assert CalonMahasiswa.validate_phone_format('0812 3456 7890') == True
    assert CalonMahasiswa.validate_phone_format('0812-3456-7890') == True
    assert CalonMahasiswa.validate_phone_format('0812 3456-7890') == True

    print("Phone validation tests passed!")

def test_model_creation_with_valid_data():
    """Test creating models with valid data"""
    
    # Valid data for CalonMahasiswa
    valid_data = {
        'nama_lengkap': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '081234567890',
        'tanggal_lahir': datetime.now(),
        'alamat': 'Jl. Contoh No. 123',
        'program_studi_id': 1,
        'jalur_masuk': JalurMasukEnum.SNBP
    }
    
    # Creating the object should not raise an exception
    try:
        calon_mahasiswa = CalonMahasiswa(**valid_data)
        print("Valid CalonMahasiswa creation passed!")
    except ValueError as e:
        print(f"Unexpected error during valid CalonMahasiswa creation: {e}")
        raise

def test_model_creation_with_invalid_data():
    """Test that creating models with invalid data raises errors"""
    
    # Test invalid email
    invalid_email_data = {
        'nama_lengkap': 'John Doe',
        'email': 'invalid-email',
        'phone': '081234567890',
        'tanggal_lahir': datetime.now(),
        'alamat': 'Jl. Contoh No. 123',
        'program_studi_id': 1,
        'jalur_masuk': JalurMasukEnum.SNBP
    }
    
    try:
        calon_mahasiswa = CalonMahasiswa(**invalid_email_data)
        assert False, "Should have raised ValueError for invalid email"
    except ValueError:
        print("Invalid email validation test passed!")
    
    # Test invalid phone
    invalid_phone_data = {
        'nama_lengkap': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '071234567890',  # Wrong prefix
        'tanggal_lahir': datetime.now(),
        'alamat': 'Jl. Contoh No. 123',
        'program_studi_id': 1,
        'jalur_masuk': JalurMasukEnum.SNBT
    }
    
    try:
        calon_mahasiswa = CalonMahasiswa(**invalid_phone_data)
        assert False, "Should have raised ValueError for invalid phone"
    except ValueError:
        print("Invalid phone validation test passed!")

if __name__ == "__main__":
    test_calon_mahasiswa_validation()
    test_model_creation_with_valid_data()
    test_model_creation_with_invalid_data()
    print("\nAll validation tests passed!")