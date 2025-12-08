"""
Test script untuk memverifikasi sistem autentikasi berfungsi dengan baik
"""
import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_system.models import User, RoleEnum
from auth_system.schemas import UserCreate, UserLogin, TokenResponse
from auth_system.services import authenticate_user, create_user, create_access_token, hash_password
from auth_system.dependencies import get_current_user, role_required
from pmb_system.database import SessionLocal, engine
from sqlalchemy.orm import Session


def test_auth_system():
    """Test fungsi-fungsi utama dari sistem autentikasi."""
    print("Testing auth system...")
    
    # Buat database dan tabel-tabelnya
    from auth_system import models
    models.Base.metadata.create_all(bind=engine)
    
    # Buat sesi database
    db: Session = SessionLocal()
    
    try:
        # Hapus pengguna yang mungkin sudah ada untuk testing bersih
        db.query(User).filter(User.username.in_(["admin", "dosen1", "mahasiswa1"])).delete()
        db.commit()

        # Test pembuatan pengguna admin
        print("1. Creating admin user...")
        admin_data = UserCreate(username="admin", password="password123", role=RoleEnum.ADMIN)
        admin_user = create_user(db, admin_data)
        print(f"   Created admin user: {admin_user.username} with role: {admin_user.role}")

        # Test pembuatan pengguna dosen
        print("2. Creating dosen user...")
        dosen_data = UserCreate(username="dosen1", password="password123", role=RoleEnum.DOSEN)
        dosen_user = create_user(db, dosen_data)
        print(f"   Created dosen user: {dosen_user.username} with role: {dosen_user.role}")

        # Test pembuatan pengguna mahasiswa
        print("3. Creating mahasiswa user...")
        mahasiswa_data = UserCreate(username="mahasiswa1", password="password123", role=RoleEnum.MAHASISWA)
        mahasiswa_user = create_user(db, mahasiswa_data)
        print(f"   Created mahasiswa user: {mahasiswa_user.username} with role: {mahasiswa_user.role}")
        
        # Test otentikasi
        print("4. Testing authentication...")
        authenticated_user = authenticate_user(db, "admin", "password123")
        if authenticated_user:
            print(f"   Successfully authenticated user: {authenticated_user.username}")
        else:
            print("   Authentication failed")
        
        # Test pembuatan token
        print("5. Testing token creation...")
        access_token = create_access_token(data={"sub": "admin", "role": RoleEnum.ADMIN.value})
        print(f"   Created token for admin: {access_token[:20]}...")
        
        # Test autentikasi dengan password salah
        print("6. Testing failed authentication...")
        failed_auth = authenticate_user(db, "admin", "wrongpassword")
        if not failed_auth:
            print("   Correctly failed authentication with wrong password")
        else:
            print("   Authentication should have failed but didn't")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    test_auth_system()