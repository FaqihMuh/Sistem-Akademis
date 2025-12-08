"""
Test script to verify the new nim and kode_dosen fields work properly
"""
import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_system.models import User, RoleEnum
from auth_system.schemas import UserCreate
from auth_system.services import create_user
from pmb_system.database import SessionLocal, engine
from sqlalchemy.orm import Session


def test_new_fields():
    """Test the new nim and kode_dosen fields."""
    print("Testing new nim and kode_dosen fields...")
    
    # Buat sesi database
    db: Session = SessionLocal()
    
    try:
        # Test 1: Create a student user with NIM
        print("1. Creating student user with NIM...")
        student_data = UserCreate(
            username="student123",
            password="password123",
            role=RoleEnum.MAHASISWA,
            nim="2010230123"
        )
        student_user = create_user(db, student_data)
        print(f"   Created student user: {student_user.username}")
        print(f"   NIM: {student_user.nim}")
        print(f"   Kode Dosen: {student_user.kode_dosen}")  # Should be None
        assert student_user.nim == "2010230123"
        assert student_user.kode_dosen is None
        print("   OK - Student user created correctly")

        # Test 2: Create a lecturer user with kode_dosen
        print("\n2. Creating lecturer user with kode_dosen...")
        lecturer_data = UserCreate(
            username="lecturer001",
            password="password123",
            role=RoleEnum.DOSEN,
            kode_dosen="D001"
        )
        lecturer_user = create_user(db, lecturer_data)
        print(f"   Created lecturer user: {lecturer_user.username}")
        print(f"   Kode Dosen: {lecturer_user.kode_dosen}")
        print(f"   NIM: {lecturer_user.nim}")  # Should be None
        assert lecturer_user.kode_dosen == "D001"
        assert lecturer_user.nim is None
        print("   OK - Lecturer user created correctly")

        # Test 3: Create an admin user (should have both fields as None)
        print("\n3. Creating admin user (no academic fields)...")
        admin_data = UserCreate(
            username="admin_new",
            password="password123",
            role=RoleEnum.ADMIN
        )
        admin_user = create_user(db, admin_data)
        print(f"   Created admin user: {admin_user.username}")
        print(f"   NIM: {admin_user.nim}")  # Should be None
        print(f"   Kode Dosen: {admin_user.kode_dosen}")  # Should be None
        assert admin_user.nim is None
        assert admin_user.kode_dosen is None
        print("   OK - Admin user created correctly")

        # Test 4: Test that existing users still work (backward compatibility)
        print("\n4. Testing backward compatibility...")
        # Get all users to ensure they're still accessible
        all_users = db.query(User).all()
        print(f"   Total users in database: {len(all_users)}")

        # Find our test users
        test_student = db.query(User).filter(User.username == "student123").first()
        assert test_student is not None
        assert test_student.nim == "2010230123"
        assert test_student.kode_dosen is None
        print("   OK - Student user retrieved correctly with academic data")

        test_lecturer = db.query(User).filter(User.username == "lecturer001").first()
        assert test_lecturer is not None
        assert test_lecturer.kode_dosen == "D001"
        assert test_lecturer.nim is None
        print("   OK - Lecturer user retrieved correctly with academic data")

        print("\nAll tests passed! The new fields are working correctly.")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup - delete test users
        db.query(User).filter(User.username.in_(["student123", "lecturer001", "admin_new"])).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_new_fields()