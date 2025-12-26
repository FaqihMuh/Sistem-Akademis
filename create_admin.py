import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pmb_system.database import SessionLocal
from auth_system.models import User
from auth_system.services import hash_password

db = SessionLocal()

def create_admin():
    username = "admin"
    password = "admin123"
    role = "ADMIN"

    # Cek apakah admin sudah ada
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print("Admin already exists.")
        return

    hashed = hash_password(password)  # Changed from get_password_hash to hash_password
    admin = User(
        username=username,
        password_hash=hashed,
        role=role
    )

    db.add(admin)
    db.commit()
    print("Admin user created successfully!")

if __name__ == "__main__":
    create_admin()
