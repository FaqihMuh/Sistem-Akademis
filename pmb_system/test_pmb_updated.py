import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import os

# Set testing environment at the start
os.environ["TESTING"] = "1"

# Import modules after setting environment
import models
from models import Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum

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

# Import app after defining database
from main import app
from database import get_db

@pytest.fixture(scope="function")
def db_session():
    """Create a database session for testing"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Yield the session
    yield session
    
    # Clean up after test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with the database session dependency overridden"""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up the override
    app.dependency_overrides.clear()

def test_register_success(client, db_session):
    """Test successful registration of a new applicant"""
    # Create a program studi first
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    # Registration payload
    payload = {
        "nama_lengkap": "John Doe",
        "email": "john.doe.test@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 123",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "SNBT"
    }
    
    response = client.post("/api/pmb/register", json=payload)
    
    assert response.status_code == 200  # 200 because it returns the created object, not 201
    data = response.json()
    assert data["email"] == "john.doe.test@example.com"
    assert data["nama_lengkap"] == "John Doe"
    assert data["status"] == "pending"


def test_register_duplicate_email(client, db_session):
    """Test registration with duplicate email returns 409 conflict"""
    # Create a program studi first
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    # Create the first applicant
    payload = {
        "nama_lengkap": "John Doe",
        "email": "duplicate.test@example.com",
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


def test_approve_generate_nim(client, db_session):
    """Test that NIM is generated correctly in the expected format and sequentially"""
    # Create a program studi
    program_studi = ProgramStudi(
        kode="SIF",
        nama="Sistem Informasi",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    # Register an applicant
    payload = {
        "nama_lengkap": "Jane Doe",
        "email": "jane.doe.test@example.com",
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


def test_approve_idempotent(client, db_session):
    """Test that approving the same applicant twice doesn't generate a new NIM"""
    # Create a program studi
    program_studi = ProgramStudi(
        kode="AKT",
        nama="Akuntansi",
        fakultas="Fakultas Ekonomi"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    # Register an applicant
    payload = {
        "nama_lengkap": "Bob Smith",
        "email": "bob.smith.test@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2000-01-01T00:00:00",
        "alamat": "Jl. Contoh No. 789",
        "program_studi_id": program_studi.id,
        "jalur_masuk": "MANDIRI"
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


def test_invalid_phone_format(client, db_session):
    """Test that registration with invalid phone format returns 400"""
    # Create a program studi first
    program_studi = ProgramStudi(
        kode="TIK",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    # Invalid phone in payload (doesn't start with 08)
    payload = {
        "nama_lengkap": "Invalid Phone Test",
        "email": "invalid.phone.test@example.com",
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
    if response.status_code == 422:  # Pydantic validation error
        error_detail = str(response.json()).lower()
        assert "phone" in error_detail or "format" in error_detail
    else:  # If it's handled as 400
        error_detail = response.json()["detail"].lower()
        assert "format" in error_detail