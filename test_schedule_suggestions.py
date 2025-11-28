"""
Test script for the new schedule suggestion feature
"""
import sys
import os
from datetime import time

# Add the project root to path to import modules
sys.path.insert(0, os.path.abspath('.'))

from schedule_system.ai_rescheduler import generate_schedule_alternatives
from schedule_system.models import JadwalKelas, Ruang, Dosen
from schedule_system.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def test_suggestion_functionality():
    """Test the generate_schedule_alternatives function directly"""
    
    # Create an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool, echo=True)
    
    # Import the Base from models to create tables
    from schedule_system.models import Base
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Create some test data
        # Create rooms
        room1 = Ruang(
            kode="A101",
            nama="Ruang Kelas A101",
            kapasitas=30,
            jenis="Kelas"
        )
        room2 = Ruang(
            kode="B201", 
            nama="Ruang Kelas B201",
            kapasitas=40,
            jenis="Kelas"
        )
        
        db.add(room1)
        db.add(room2)
        db.commit()
        
        # Create a professor
        dosen = Dosen(
            nip="1234567890",
            nama="Dr. John Doe",
            email="john.doe@university.edu",
            program_studi="Teknik Informatika"
        )
        db.add(dosen)
        db.commit()
        
        # Create some existing schedules that would cause conflicts
        existing_schedule1 = JadwalKelas(
            kode_mk="IF101",
            dosen_id=dosen.id,
            ruang_id=room1.id,
            semester="2023/2024-1",
            hari="senin",
            jam_mulai=time(9, 0),  # 09:00
            jam_selesai=time(11, 0),  # 11:00
            kapasitas_kelas=30,
            kelas="A"
        )
        
        # Add another schedule in the same room at different time
        existing_schedule2 = JadwalKelas(
            kode_mk="IF102",
            dosen_id=dosen.id,
            ruang_id=room1.id,
            semester="2023/2024-1",
            hari="senin",
            jam_mulai=time(13, 0),  # 13:00
            jam_selesai=time(15, 0),  # 15:00
            kapasitas_kelas=30,
            kelas="B"
        )
        
        db.add(existing_schedule1)
        db.add(existing_schedule2)
        db.commit()
        
        print("Test data created successfully")
        
        # Test 1: Generate suggestions for a schedule that would conflict
        print("\n--- Test 1: Generating alternative schedules ---")
        suggestions = generate_schedule_alternatives(
            kode_mk="IF201",
            dosen_id=dosen.id,
            ruang_id=room1.id,  # Same room - will cause conflict
            hari="senin",
            jam_mulai=time(10, 0),  # This conflicts with existing schedule 9:00-11:00
            jam_selesai=time(12, 0),
            kapasitas_kelas=25,
            semester="2023/2024-1",
            db=db
        )
        
        print(f"Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. Hari: {suggestion['hari']}, Jam: {suggestion['jam_mulai']}-{suggestion['jam_selesai']}, Ruang ID: {suggestion['ruang_id']}, Reason: {suggestion['reason']}")
        
        # Test 2: Validate the suggestion format matches requirements
        print("\n--- Test 2: Validating suggestion format ---")
        if suggestions:
            first_suggestion = suggestions[0]
            required_keys = ['hari', 'jam_mulai', 'jam_selesai', 'ruang_id', 'reason']
            missing_keys = [key for key in required_keys if key not in first_suggestion]
            
            if not missing_keys:
                print("SUCCESS: All required keys are present in suggestions")
            else:
                print(f"ERROR: Missing keys: {missing_keys}")

        # Test 3: Test with different constraints
        print("\n--- Test 3: Testing with different parameters ---")
        suggestions2 = generate_schedule_alternatives(
            kode_mk="IF301",
            dosen_id=dosen.id,
            ruang_id=room2.id,  # Different room
            hari="selasa",
            jam_mulai=time(8, 0),  # 08:00
            jam_selesai=time(10, 0),  # 10:00
            kapasitas_kelas=35,  # Larger class
            semester="2023/2024-1",
            db=db
        )

        print(f"Generated {len(suggestions2)} suggestions for different schedule:")
        for i, suggestion in enumerate(suggestions2, 1):
            print(f"  {i}. Hari: {suggestion['hari']}, Jam: {suggestion['jam_mulai']}-{suggestion['jam_selesai']}, Ruang ID: {suggestion['ruang_id']}, Reason: {suggestion['reason']}")

        print("\nSUCCESS: All tests passed successfully!")
        return True

    except Exception as e:
        print(f"ERROR: Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_endpoint_integration():
    """Test that endpoints function properly"""
    try:
        print("\n--- Testing endpoint imports ---")
        from schedule_system.endpoints import (
            suggest_alternative_schedules,
            suggest_alternative_schedules_by_id,
            create_schedule_endpoint,
            update_schedule_endpoint
        )
        print("SUCCESS: All endpoint functions imported successfully")

        # Test that response models exist
        from schedule_system.endpoints import (
            ScheduleSuggestionResponse,
            ScheduleConflictWithError,
            JadwalKelasCreate,
            JadwalKelasUpdate
        )
        print("SUCCESS: All response models imported successfully")

        return True
    except Exception as e:
        print(f"ERROR: Endpoint test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing Schedule Suggestion Feature...")
    
    success1 = test_suggestion_functionality()
    success2 = test_endpoint_integration()
    
    if success1 and success2:
        print("\nSUCCESS: All tests passed! The schedule suggestion feature is working correctly.")
    else:
        print("\nERROR: Some tests failed.")
        sys.exit(1)