"""
Test script untuk menguji endpoint-endpoint tambahan sistem autentikasi
"""
import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import aplikasi utama
from main import app
from pmb_system.database import Base, get_db
from auth_system.models import User, RoleEnum
from auth_system.services import hash_password


# Buat database in-memory untuk testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Buat override dependency untuk testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        # Buat tabel-tabel jika belum ada
        Base.metadata.create_all(bind=engine)
        
        # Buat user admin default untuk testing
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=hash_password("password123"),
                role=RoleEnum.ADMIN
            )
            db.add(admin_user)
            db.commit()
        
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = override_get_db

# Buat test client
client = TestClient(app)


def test_login():
    """Test endpoint login."""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "password123"
    })
    print(f"Login response status: {response.status_code}")
    print(f"Login response body: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"
    token = data["access_token"]
    return token


def test_get_current_user():
    """Test endpoint untuk mendapatkan info pengguna saat ini."""
    token = test_login()
    response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "ADMIN"


def test_register_new_user():
    """Test endpoint untuk mendaftarkan pengguna baru."""
    # Login dulu untuk mendapatkan token
    token = test_login()
    
    # Daftarkan user baru
    response = client.post("/api/auth/register", 
        json={
            "username": "testuser",
            "password": "testpass123",
            "role": "MAHASISWA"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "MAHASISWA"


def test_get_all_users():
    """Test endpoint untuk mendapatkan semua pengguna."""
    token = test_login()
    response = client.get("/api/auth/users", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    # Harus ada setidaknya admin user
    assert len(data["users"]) >= 1


def test_update_user_password():
    """Test endpoint untuk memperbarui password pengguna."""
    token = test_login()
    
    # Buat user untuk testing
    client.post("/api/auth/register", 
        json={
            "username": "updateuser",
            "password": "oldpass123",
            "role": "MAHASISWA"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Ambil user ID dari daftar pengguna
    response = client.get("/api/auth/users", headers={
        "Authorization": f"Bearer {token}"
    })
    users = response.json()["users"]
    update_user = next((u for u in users if u["username"] == "updateuser"), None)
    assert update_user is not None
    
    # Update password user
    response = client.put(
        f"/api/auth/users/{update_user['id']}/password?new_password=newpass123",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_update_current_user_password():
    """Test endpoint untuk memperbarui password pengguna saat ini."""
    token = test_login()
    
    # Coba update password user admin
    response = client.put(
        "/api/auth/me/password",
        params={
            "current_password": "password123",
            "new_password": "newpassword123"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Coba login dengan password baru
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "newpassword123"
    })
    assert response.status_code == 200


if __name__ == "__main__":
    print("Testing auth system endpoints...")
    
    # Jalankan test login
    print("1. Testing login...")
    token = test_login()
    print("   Login successful")
    
    # Jalankan test get_current_user
    print("2. Testing get current user...")
    test_get_current_user()
    print("   Get current user successful")
    
    # Jalankan test register
    print("3. Testing register new user...")
    test_register_new_user()
    print("   Register new user successful")
    
    # Jalankan test get_all_users
    print("4. Testing get all users...")
    test_get_all_users()
    print("   Get all users successful")
    
    # Jalankan test update_user_password
    print("5. Testing update user password...")
    test_update_user_password()
    print("   Update user password successful")
    
    # Jalankan test update_current_user_password
    print("6. Testing update current user password...")
    test_update_current_user_password()
    print("   Update current user password successful")
    
    print("\nAll endpoint tests completed successfully!")