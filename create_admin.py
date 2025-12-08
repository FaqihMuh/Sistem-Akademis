from database import SessionLocal
from auth_system.models import User
from auth_system.services import get_password_hash

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

    hashed = get_password_hash(password)
    admin = User(
        username=username,
        password_hash=hashed,
        role=role
    )

    db.add(admin)
    db.commit()
    print("Admin user created successfully!")

create_admin()
