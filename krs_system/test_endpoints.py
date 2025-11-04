"""
Test script for KRS FastAPI endpoints
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time, datetime
from krs_system.models import Base
from krs_system.endpoints import router
from fastapi import FastAPI
from pmb_system.models import CalonMahasiswa
from pmb_system.database import Base as PMBBase

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)

# For testing purposes, set up temporary database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_endpoints.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables including related ones
from pmb_system.models import Base as PMBBase, ProgramStudi  # Import other PMB models needed

# Create all tables
PMBBase.metadata.create_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_krs_endpoints():
    print("Testing KRS endpoints...")
    
    # Create a test student in PMB system
    db = TestingSessionLocal()
    
    # Add a required program studi first
    test_program = db.query(ProgramStudi).filter(ProgramStudi.id == 1).first()
    if not test_program:
        test_program = ProgramStudi(
            kode="IF1",
            nama="Informatika",
            fakultas="Ilmu Komputer"
        )
        db.add(test_program)
        db.commit()
    
    # Add a test student
    test_student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test.student123@example.com",  # Include NIM pattern in email
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),  # Using datetime object
        alamat="Test Address",
        program_studi_id=1,
        jalur_masuk="SNBT",
        status="PENDING"
    )
    
    # Add a test course
    from krs_system.models import Matakuliah
    test_course = Matakuliah(
        kode="TEST101",
        nama="Test Course",
        sks=3,
        semester=1,
        hari="Monday",
        jam_mulai=time(8, 0, 0),
        jam_selesai=time(10, 0, 0)
    )
    
    db.add(test_student)
    db.add(test_course)
    db.commit()
    student_id = test_student.id
    course_id = test_course.id
    
    # Test data
    nim = "123"  # Part of student email
    semester = "2025/2026-1"
    
    print("\n--- Testing ADD course endpoint ---")
    response = client.post(
        f"/api/krs/{nim}/add",
        json={"kode_mk": "TEST101", "semester": semester}
    )
    
    # Close the database session after adding test data
    db.close()
    print(f"ADD response: {response.status_code}, {response.json()}")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    print("\n--- Testing GET KRS endpoint ---")
    response = client.get(f"/api/krs/{nim}")
    print(f"GET response: {response.status_code}")
    if response.status_code == 200:
        print(f"GET response data: {response.json()}")
    else:
        print(f"GET error: {response.text}")
    # Note: GET might return 404 if student is not found with exact NIM match in name/email
    
    print("\n--- Testing SUBMIT KRS endpoint ---")
    response = client.post(
        f"/api/krs/{nim}/submit",
        json={"kode_mk": "TEST101", "semester": semester}
    )
    print(f"SUBMIT response: {response.status_code}, {response.json()}")
    
    print("\n--- Testing APPROVE KRS endpoint ---")
    response = client.post(
        f"/api/krs/{nim}/approve",
        json={"semester": semester, "dosen_pa_id": 1}
    )
    print(f"APPROVE response: {response.status_code}, {response.json()}")
    
    print("\n--- Testing REMOVE course endpoint ---")
    response = client.delete(
        f"/api/krs/{nim}/remove",
        json={"kode_mk": "TEST101", "semester": semester}
    )
    print(f"REMOVE response: {response.status_code}, {response.json()}")
    
    # Clean up
    db = TestingSessionLocal()
    db.query(Matakuliah).filter(Matakuliah.kode == "TEST101").delete()
    db.query(CalonMahasiswa).filter(CalonMahasiswa.id == student_id).delete()
    db.commit()
    db.close()
    
    print("\nEndpoint tests completed!")


if __name__ == "__main__":
    test_krs_endpoints()