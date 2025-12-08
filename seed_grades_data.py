from sqlalchemy.orm import Session
from pmb_system.database import SessionLocal
# Import all models to ensure they're registered with SQLAlchemy
from pmb_system import models as pmb_models
from krs_system import models as krs_models
from schedule_system import models as schedule_models
from auth_system import models as auth_models
from grades_system import models as grades_models
from pmb_system.models import CalonMahasiswa, ProgramStudi
from schedule_system.models import Dosen
from krs_system.models import Matakuliah
from auth_system.models import User, RoleEnum
from grades_system.models import Grade
from datetime import datetime

def seed_grades_data(db: Session):
    """Seed grades system data for testing"""

    # Check if data already exists to avoid duplicates
    existing_grade = db.query(Grade).first()
    if existing_grade:
        print("Grades data already exists, skipping seed.")
        return

    print("Seeding grades system data...")

    # Create a program study if not exists
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.kode == "TI1").first()
    if not program_studi:
        program_studi = ProgramStudi(
            kode="TI1",
            nama="Teknik Informatika",
            fakultas="Fakultas Teknik"
        )
        db.add(program_studi)
        db.commit()
        db.refresh(program_studi)

    # Create a student if not exists
    mahasiswa = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == "2023001").first()
    if not mahasiswa:
        mahasiswa = CalonMahasiswa(
            nama_lengkap="Budi Santoso",
            email="budi.santoso@example.com",
            phone="081234567890",
            tanggal_lahir=datetime(2005, 5, 15),
            alamat="Jl. Contoh No. 123, Kota",
            program_studi_id=program_studi.id,
            jalur_masuk="SNBT",
            status="APPROVED",
            nim="2023001"
        )
        db.add(mahasiswa)
        db.commit()
        db.refresh(mahasiswa)

    # Create a dosen if not exists
    dosen = db.query(Dosen).filter(Dosen.nip == "123456789").first()
    if not dosen:
        dosen = Dosen(
            nip="123456789",
            nama="Dr. Ahmad Kurniawan, M.Kom",
            email="ahmad.kurniawan@example.com",
            phone="081234567891",
            program_studi="Teknik Informatika",
            kode_dosen="D001"
        )
        db.add(dosen)
        db.commit()
        db.refresh(dosen)

    # Create a user for the dosen if not exists
    dosen_user = db.query(User).filter(User.username == "ahmad.kurniawan").first()
    if not dosen_user:
        from auth_system.services import hash_password
        dosen_user = User(
            username="ahmad.kurniawan",
            password_hash=hash_password("password123"),
            role=RoleEnum.DOSEN.value,
            kode_dosen=dosen.kode_dosen
        )
        db.add(dosen_user)
        db.commit()

    # Create another user for the student if not exists
    student_user = db.query(User).filter(User.username == "budi.santoso").first()
    if not student_user:
        from auth_system.services import hash_password
        student_user = User(
            username="budi.santoso",
            password_hash=hash_password("password123"),
            role=RoleEnum.MAHASISWA.value,
            nim="2023001"
        )
        db.add(student_user)
        db.commit()

    # Create some courses if they don't exist
    matakuliah1 = db.query(Matakuliah).filter(Matakuliah.kode == "TI101").first()
    if not matakuliah1:
        matakuliah1 = Matakuliah(
            kode="TI101",
            nama="Pemrograman Dasar",
            sks=3,
            semester=1,
            hari="Senin",
            jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
            jam_selesai=datetime.strptime("10:00", "%H:%M").time()
        )
        db.add(matakuliah1)
        db.commit()
        db.refresh(matakuliah1)

    matakuliah2 = db.query(Matakuliah).filter(Matakuliah.kode == "TI102").first()
    if not matakuliah2:
        matakuliah2 = Matakuliah(
            kode="TI102",
            nama="Algoritma dan Struktur Data",
            sks=4,
            semester=2,
            hari="Selasa",
            jam_mulai=datetime.strptime("09:00", "%H:%M").time(),
            jam_selesai=datetime.strptime("11:00", "%H:%M").time()
        )
        db.add(matakuliah2)
        db.commit()
        db.refresh(matakuliah2)

    # Now create some grades
    grade1 = Grade(
        nim=mahasiswa.nim,
        matakuliah_id=matakuliah1.id,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=dosen.id,
        presensi=95.0
    )
    db.add(grade1)

    grade2 = Grade(
        nim=mahasiswa.nim,
        matakuliah_id=matakuliah2.id,
        semester="2023/2024-1",
        nilai_huruf="B",
        nilai_angka=3.0,
        sks=4,
        dosen_id=dosen.id,
        presensi=88.5
    )
    db.add(grade2)

    db.commit()
    print("Grades system data seeded successfully!")

def main():
    db = SessionLocal()
    try:
        seed_grades_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()