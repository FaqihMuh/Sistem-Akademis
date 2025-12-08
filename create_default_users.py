"""
Script untuk membuat pengguna admin default
"""
import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pmb_system.database import SessionLocal, engine
from auth_system.models import User, Base
from auth_system.services import hash_password


def create_admin_user():
    """Buat pengguna admin default jika belum ada."""
    # Buat tabel jika belum ada
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Cek apakah pengguna admin sudah ada
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # Buat pengguna admin default
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="ADMIN"
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
            print(f"Username: admin")
            print(f"Password: admin123")
        else:
            print("Admin user already exists")
            
        # Buat juga pengguna dosen dan mahasiswa untuk testing
        dosen_user = db.query(User).filter(User.username == "dosen").first()
        if not dosen_user:
            dosen_user = User(
                username="dosen",
                password_hash=hash_password("dosen123"),
                role="DOSEN"
            )
            db.add(dosen_user)
            db.commit()
            print("Dosen user created successfully!")
            print(f"Username: dosen")
            print(f"Password: dosen123")
        
        mahasiswa_user = db.query(User).filter(User.username == "mahasiswa").first()
        if not mahasiswa_user:
            mahasiswa_user = User(
                username="mahasiswa",
                password_hash=hash_password("mahasiswa123"),
                role="MAHASISWA"
            )
            db.add(mahasiswa_user)
            db.commit()
            print("Mahasiswa user created successfully!")
            print(f"Username: mahasiswa")
            print(f"Password: mahasiswa123")
            
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()