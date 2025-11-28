"""
Test script to verify datetime field fix in schedule schemas
"""
import sqlite3
from datetime import datetime, time
from schedule_system.models import JadwalKelas, Dosen, Ruang
from pmb_system.database import SessionLocal
from schedule_system.endpoints import JadwalKelasResponse


def test_schema_validation():
    # Create a test schedule object similar to what would come from the database
    test_schedule = JadwalKelas(
        id=1,
        kode_mk="CS101",
        dosen_id=1,
        ruang_id=1,
        semester="2024/2025-1",
        hari="senin",
        jam_mulai=time(8, 0),
        jam_selesai=time(10, 0),
        kapasitas_kelas=30,
        kelas="A",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Convert to Pydantic response model
    try:
        response = JadwalKelasResponse.from_orm(test_schedule)
        print(f"SUCCESS: Schema validation successful!")
        print(f"Schedule ID: {response.id}")
        print(f"Created at: {response.created_at}")
        print(f"Updated at: {response.updated_at}")
        print(f"Created at type: {type(response.created_at)}")
        print(f"Updated at type: {type(response.updated_at)}")
        print(f"Created at ISO format: {response.created_at.isoformat() if response.created_at else None}")
        print(f"Updated at ISO format: {response.updated_at.isoformat() if response.updated_at else None}")
        return True
    except Exception as e:
        print(f"ERROR: Schema validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_schema_validation()
    if success:
        print("\nSUCCESS: All datetime field fixes are working correctly!")
    else:
        print("\nERROR: There are still issues with datetime field handling")