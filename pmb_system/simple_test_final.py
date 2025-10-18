"""
Simple test script for PMB API functionality
This focuses on testing the core functionality without complex database setup
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import os

# Set testing environment
os.environ["TESTING"] = "1"

# Import the FastAPI app and models
from main import app
from database import get_db
from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Override the database dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

def test_register_success():
    """Test successful registration of a new applicant"""
    print("Testing successful registration...")
    
    # Create a program studi first
    db = TestingSessionLocal()
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    db.close()
    
    # Registration payload
    payload = {
        "nama_lengkap": "John Doe",
        "email": "john.doe.unique1@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 123",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "SNBT"
    }
    
    response = client.post("/api/pmb/register", json=payload)
    
    assert response.status_code == 200  # 200 because it returns the created object
    data = response.json()
    assert data["email"] == "john.doe.unique1@example.com"
    assert data["nama_lengkap"] == "John Doe"
    assert data["status"] == "pending"
    print("SUCCESS: Registered applicant with email:", data["email"])

def test_register_duplicate_email():
    """Test registration with duplicate email returns 409 conflict"""
    print("Testing duplicate email registration...")
    
    # Create a program studi first
    db = TestingSessionLocal()
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    db.close()
    
    # Create the first applicant
    payload = {
        "nama_lengkap": "John Doe",
        "email": "duplicate.unique@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 123",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "SNBT"
    }
    
    # Register the first applicant
    response1 = client.post("/api/pmb/register", json=payload)
    assert response1.status_code == 200
    
    # Try to register with duplicate email
    response2 = client.post("/api/pmb/register", json=payload)
    
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"]
    print("SUCCESS: Duplicate email properly rejected with 409")

def test_approve_generate_nim():
    """Test that NIM is generated correctly in the expected format and sequentially"""
    print("Testing NIM generation...")
    
    # Create a program studi
    db = TestingSessionLocal()
    program_studi = ProgramStudi(
        kode="SIF",
        nama="Sistem Informasi",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    db.close()
    
    # Register an applicant
    payload = {
        "nama_lengkap": "Jane Doe",
        "email": "jane.doe.unique2@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 456",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "SNBP"
    }
    
    register_response = client.post("/api/pmb/register", json=payload)
    assert register_response.status_code == 200
    applicant_data = register_response.json()
    applicant_id = applicant_data["id"]
    
    # Approve the applicant
    approve_response = client.put(f"/api/pmb/approve/{applicant_id}")
    assert approve_response.status_code == 200
    
    approve_data = approve_response.json()
    nim = approve_data["nim"]
    
    # Check format: [Tahun:4][Kode Prodi:3][Running Number:4]
    current_year = str(datetime.now().year)
    expected_prefix = current_year + program_studi.kode
    assert nim.startswith(expected_prefix), f"NIM {nim} should start with {expected_prefix}"
    assert len(nim) == 11, f"NIM {nim} should have length 11, got {len(nim)}"
    
    # Check that running number is correct (should be 0001 for first student in program)
    expected_running = "0001"
    assert nim.endswith(expected_running), f"NIM {nim} should end with {expected_running}, got {nim[-4:]}"
    print("SUCCESS: Generated NIM:", nim)

def test_approve_idempotent():
    """Test that approving the same applicant twice doesn't generate a new NIM"""
    print("Testing idempotent approval...")
    
    # Create a program studi
    db = TestingSessionLocal()
    program_studi = ProgramStudi(
        kode="AKT",
        nama="Akuntansi",
        fakultas="Fakultas Ekonomi"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    db.close()
    
    # Register an applicant
    payload = {
        "nama_lengkap": "Bob Smith",
        "email": "bob.smith.unique3@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 789",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "Mandiri"
    }
    
    register_response = client.post("/api/pmb/register", json=payload)
    assert register_response.status_code == 200
    applicant_data = register_response.json()
    applicant_id = applicant_data["id"]
    
    # Approve the applicant for the first time
    first_approve_response = client.put(f"/api/pmb/approve/{applicant_id}")
    assert first_approve_response.status_code == 200
    first_nim = first_approve_response.json()["nim"]
    
    # Approve the same applicant again (should fail with 400 since already approved)
    second_approve_response = client.put(f"/api/pmb/approve/{applicant_id}")
    assert second_approve_response.status_code == 400
    assert "already approved" in second_approve_response.json()["detail"]
    print("SUCCESS: Idempotent approval properly rejected with 400")

def test_invalid_phone_format():
    """Test that registration with invalid phone format returns 400 or 422"""
    print("Testing invalid phone format...")
    
    # Create a program studi first
    db = TestingSessionLocal()
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db.add(program_studi)
    db.commit()
    db.refresh(program_studi)
    db.close()
    
    # Invalid phone in payload (doesn't start with 08)
    payload = {
        "nama_lengkap": "Invalid Phone Test",
        "email": "invalid.phone.unique4@example.com",
        "phone": "071234567890",  # Invalid: starts with 07 instead of 08
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 999",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "SNBT"
    }
    
    response = client.post("/api/pmb/register", json=payload)
    
    # The validation might happen at the Pydantic level or during model creation
    # Based on our implementation, it should return 422 (validation error) or 400
    assert response.status_code in [400, 422]
    print("SUCCESS: Invalid phone format properly rejected with", response.status_code)

if __name__ == "__main__":
    test_register_success()
    test_register_duplicate_email()
    test_approve_generate_nim()
    test_approve_idempotent()
    test_invalid_phone_format()
    print("\nAll tests passed successfully!")