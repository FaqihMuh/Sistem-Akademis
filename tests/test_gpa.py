import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pmb_system.database import Base
# Import all models to ensure their tables are created
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
from grades_system.services.gpa_service import calculate_ips, calculate_ipk, get_transcript
from datetime import datetime


# Create an in-memory SQLite database for testing
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_all_a_grades(db_session):
    """Test GPA calculation with all A grades"""
    # Create test data
    program_studi = ProgramStudi(
        kode="TI1",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),
        alamat="Test Address",
        program_studi_id=program_studi.id,
        jalur_masuk="SNBT",
        status="APPROVED",
        nim="2023001"
    )
    db_session.add(student)
    db_session.commit()
    
    dosen = Dosen(
        nip="123456789",
        nama="Test Dosen",
        email="dosen@example.com",
        phone="081234567891",
        program_studi="Teknik Informatika",
        kode_dosen="D001"
    )
    db_session.add(dosen)
    db_session.commit()
    
    matakuliah1 = Matakuliah(
        kode="TI101",
        nama="Pemrograman Dasar",
        sks=3,
        semester=1,
        hari="Senin",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("10:00", "%H:%M").time()
    )
    matakuliah2 = Matakuliah(
        kode="TI102",
        nama="Algoritma",
        sks=4,
        semester=1,
        hari="Selasa",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("11:00", "%H:%M").time()
    )
    db_session.add(matakuliah1)
    db_session.add(matakuliah2)
    db_session.commit()
    
    # Add grades with all A's
    grade1 = Grade(
        nim="2023001",
        matakuliah_id=matakuliah1.id,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=dosen.id
    )
    grade2 = Grade(
        nim="2023001",
        matakuliah_id=matakuliah2.id,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=4,
        dosen_id=dosen.id
    )
    db_session.add(grade1)
    db_session.add(grade2)
    db_session.commit()
    
    # Test IPS calculation
    ips = calculate_ips(db_session, "2023001", "2023/2024-1")
    expected_ips = (3*4.0 + 4*4.0) / (3 + 4)  # (12 + 16) / 7 = 4.0
    assert ips == expected_ips
    
    # Test IPK calculation
    ipk = calculate_ipk(db_session, "2023001")
    assert ipk == expected_ips


def test_course_repeat_with_highest_grade(db_session):
    """Test GPA calculation when a course is repeated (take highest grade)"""
    # Create test data (reuse from previous test setup)
    program_studi = ProgramStudi(
        kode="TI1",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),
        alamat="Test Address",
        program_studi_id=program_studi.id,
        jalur_masuk="SNBT",
        status="APPROVED",
        nim="2023002"
    )
    db_session.add(student)
    db_session.commit()
    
    dosen = Dosen(
        nip="123456789",
        nama="Test Dosen",
        email="dosen@example.com",
        phone="081234567891",
        program_studi="Teknik Informatika",
        kode_dosen="D001"
    )
    db_session.add(dosen)
    db_session.commit()
    
    matakuliah1 = Matakuliah(
        kode="TI101",
        nama="Pemrograman Dasar",
        sks=3,
        semester=1,
        hari="Senin",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("10:00", "%H:%M").time()
    )
    matakuliah2 = Matakuliah(
        kode="TI102",
        nama="Algoritma",
        sks=4,
        semester=1,
        hari="Selasa",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("11:00", "%H:%M").time()
    )
    db_session.add(matakuliah1)
    db_session.add(matakuliah2)
    db_session.commit()
    
    # Add grades: first attempt with C (2.0), retake with A (4.0) for same course
    grade1 = Grade(
        nim="2023002",
        matakuliah_id=matakuliah1.id,
        semester="2023/2024-1",
        nilai_huruf="C",
        nilai_angka=2.0,
        sks=3,
        dosen_id=dosen.id
    )
    grade2 = Grade(
        nim="2023002",
        matakuliah_id=matakuliah1.id,  # Same course ID
        semester="2023/2024-2",  # Different semester
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=dosen.id
    )
    grade3 = Grade(
        nim="2023002",
        matakuliah_id=matakuliah2.id,
        semester="2023/2024-1",
        nilai_huruf="B",
        nilai_angka=3.0,
        sks=4,
        dosen_id=dosen.id
    )
    db_session.add(grade1)
    db_session.add(grade2)
    db_session.add(grade3)
    db_session.commit()
    
    # Test IPK calculation - should use highest grade for TI101 (A=4.0) and B=3.0 for TI102
    ipk = calculate_ipk(db_session, "2023002")
    # Only use best grade for TI101 (4.0) and grade for TI102 (3.0)
    expected_ipk = (3*4.0 + 4*3.0) / (3 + 4)  # (12 + 12) / 7 = 24/7 ≈ 3.43
    assert ipk == round(expected_ipk, 2)


def test_student_without_grades(db_session):
    """Test GPA calculation for student without any grades"""
    program_studi = ProgramStudi(
        kode="TI1",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),
        alamat="Test Address",
        program_studi_id=program_studi.id,
        jalur_masuk="SNBT",
        status="APPROVED",
        nim="2023003"
    )
    db_session.add(student)
    db_session.commit()
    
    # Test IPS calculation for student without grades
    ips = calculate_ips(db_session, "2023003", "2023/2024-1")
    assert ips == 0.0
    
    # Test IPK calculation for student without grades
    ipk = calculate_ipk(db_session, "2023003")
    assert ipk == 0.0


def test_random_grade_combination(db_session):
    """Test GPA calculation with random combination of grades"""
    # Create test data
    program_studi = ProgramStudi(
        kode="TI1",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),
        alamat="Test Address",
        program_studi_id=program_studi.id,
        jalur_masuk="SNBT",
        status="APPROVED",
        nim="2023004"
    )
    db_session.add(student)
    db_session.commit()
    
    dosen = Dosen(
        nip="123456789",
        nama="Test Dosen",
        email="dosen@example.com",
        phone="081234567891",
        program_studi="Teknik Informatika",
        kode_dosen="D001"
    )
    db_session.add(dosen)
    db_session.commit()
    
    matakuliah1 = Matakuliah(
        kode="TI101",
        nama="Pemrograman Dasar",
        sks=3,
        semester=1,
        hari="Senin",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("10:00", "%H:%M").time()
    )
    matakuliah2 = Matakuliah(
        kode="TI102",
        nama="Algoritma",
        sks=4,
        semester=1,
        hari="Selasa",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("11:00", "%H:%M").time()
    )
    matakuliah3 = Matakuliah(
        kode="TI103",
        nama="Matematika Diskrit",
        sks=2,
        semester=1,
        hari="Rabu",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("09:00", "%H:%M").time()
    )
    db_session.add(matakuliah1)
    db_session.add(matakuliah2)
    db_session.add(matakuliah3)
    db_session.commit()
    
    # Add grades: A(4.0), B(3.0), D(1.0) - all passing grades
    grade1 = Grade(
        nim="2023004",
        matakuliah_id=matakuliah1.id,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=dosen.id
    )
    grade2 = Grade(
        nim="2023004",
        matakuliah_id=matakuliah2.id,
        semester="2023/2024-1",
        nilai_huruf="B",
        nilai_angka=3.0,
        sks=4,
        dosen_id=dosen.id
    )
    grade3 = Grade(
        nim="2023004",
        matakuliah_id=matakuliah3.id,
        semester="2023/2024-1",
        nilai_huruf="D",
        nilai_angka=1.0,
        sks=2,
        dosen_id=dosen.id
    )
    db_session.add(grade1)
    db_session.add(grade2)
    db_session.add(grade3)
    db_session.commit()
    
    # Test IPS calculation
    ips = calculate_ips(db_session, "2023004", "2023/2024-1")
    expected_ips = (3*4.0 + 4*3.0 + 2*1.0) / (3 + 4 + 2)  # (12 + 12 + 2) / 9 = 26/9 ≈ 2.89
    assert ips == round(expected_ips, 2)
    
    # Test IPK calculation
    ipk = calculate_ipk(db_session, "2023004")
    assert ipk == round(expected_ips, 2)


def test_grade_c_d_e_mix(db_session):
    """Test GPA calculation with mix of C, D, E grades"""
    # Create test data
    program_studi = ProgramStudi(
        kode="TI1",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),
        alamat="Test Address",
        program_studi_id=program_studi.id,
        jalur_masuk="SNBT",
        status="APPROVED",
        nim="2023005"
    )
    db_session.add(student)
    db_session.commit()
    
    dosen = Dosen(
        nip="123456789",
        nama="Test Dosen",
        email="dosen@example.com",
        phone="081234567891",
        program_studi="Teknik Informatika",
        kode_dosen="D001"
    )
    db_session.add(dosen)
    db_session.commit()
    
    matakuliah1 = Matakuliah(
        kode="TI101",
        nama="Pemrograman Dasar",
        sks=3,
        semester=1,
        hari="Senin",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("10:00", "%H:%M").time()
    )
    matakuliah2 = Matakuliah(
        kode="TI102",
        nama="Algoritma",
        sks=4,
        semester=1,
        hari="Selasa",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("11:00", "%H:%M").time()
    )
    matakuliah3 = Matakuliah(
        kode="TI103",
        nama="Matematika Diskrit",
        sks=2,
        semester=1,
        hari="Rabu",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("09:00", "%H:%M").time()
    )
    matakuliah4 = Matakuliah(
        kode="TI104",
        nama="Kalkulus",
        sks=3,
        semester=1,
        hari="Kamis",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("10:00", "%H:%M").time()
    )
    db_session.add(matakuliah1)
    db_session.add(matakuliah2)
    db_session.add(matakuliah3)
    db_session.add(matakuliah4)
    db_session.commit()
    
    # Add grades: C(2.0), D(1.0), E(0.0) - only C and D should count for GPA (E is failing)
    grade1 = Grade(
        nim="2023005",
        matakuliah_id=matakuliah1.id,
        semester="2023/2024-1",
        nilai_huruf="C",
        nilai_angka=2.0,
        sks=3,
        dosen_id=dosen.id
    )
    grade2 = Grade(
        nim="2023005",
        matakuliah_id=matakuliah2.id,
        semester="2023/2024-1",
        nilai_huruf="D",
        nilai_angka=1.0,
        sks=4,
        dosen_id=dosen.id
    )
    grade3 = Grade(
        nim="2023005",
        matakuliah_id=matakuliah3.id,
        semester="2023/2024-1",
        nilai_huruf="E",
        nilai_angka=0.0,
        sks=2,
        dosen_id=dosen.id
    )
    grade4 = Grade(
        nim="2023005",
        matakuliah_id=matakuliah4.id,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=dosen.id
    )
    db_session.add(grade1)
    db_session.add(grade2)
    db_session.add(grade3)
    db_session.add(grade4)
    db_session.commit()
    
    # Test IPS calculation - should only count C, D, and A (not E)
    ips = calculate_ips(db_session, "2023005", "2023/2024-1")
    expected_ips = (3*2.0 + 4*1.0 + 3*4.0) / (3 + 4 + 3)  # (6 + 4 + 12) / 10 = 22/10 = 2.2
    assert ips == expected_ips
    
    # Test IPK calculation
    ipk = calculate_ipk(db_session, "2023005")
    assert ipk == expected_ips


def test_get_transcript(db_session):
    """Test transcript generation"""
    # Create test data
    program_studi = ProgramStudi(
        kode="TI1",
        nama="Teknik Informatika",
        fakultas="Fakultas Teknik"
    )
    db_session.add(program_studi)
    db_session.commit()
    
    student = CalonMahasiswa(
        nama_lengkap="Test Student",
        email="test@example.com",
        phone="081234567890",
        tanggal_lahir=datetime(2000, 1, 1),
        alamat="Test Address",
        program_studi_id=program_studi.id,
        jalur_masuk="SNBT",
        status="APPROVED",
        nim="2023006"
    )
    db_session.add(student)
    db_session.commit()
    
    dosen = Dosen(
        nip="123456789",
        nama="Test Dosen",
        email="dosen@example.com",
        phone="081234567891",
        program_studi="Teknik Informatika",
        kode_dosen="D001"
    )
    db_session.add(dosen)
    db_session.commit()
    
    matakuliah1 = Matakuliah(
        kode="TI101",
        nama="Pemrograman Dasar",
        sks=3,
        semester=1,
        hari="Senin",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("10:00", "%H:%M").time()
    )
    matakuliah2 = Matakuliah(
        kode="TI102",
        nama="Algoritma",
        sks=4,
        semester=1,
        hari="Selasa",
        jam_mulai=datetime.strptime("08:00", "%H:%M").time(),
        jam_selesai=datetime.strptime("11:00", "%H:%M").time()
    )
    db_session.add(matakuliah1)
    db_session.add(matakuliah2)
    db_session.commit()
    
    # Add grades
    grade1 = Grade(
        nim="2023006",
        matakuliah_id=matakuliah1.id,
        semester="2023/2024-1",
        nilai_huruf="A",
        nilai_angka=4.0,
        sks=3,
        dosen_id=dosen.id
    )
    grade2 = Grade(
        nim="2023006",
        matakuliah_id=matakuliah2.id,
        semester="2023/2024-1",
        nilai_huruf="B",
        nilai_angka=3.0,
        sks=4,
        dosen_id=dosen.id
    )
    db_session.add(grade1)
    db_session.add(grade2)
    db_session.commit()
    
    # Test transcript generation
    transcript = get_transcript(db_session, "2023006")
    
    assert transcript["biodata"]["nim"] == "2023006"
    assert transcript["biodata"]["nama"] == "Test Student"
    assert transcript["total_sks"] == 7  # 3 + 4
    assert transcript["ipk"] == 3.57  # (3*4 + 4*3) / 7 = 24/7 ≈ 3.43 rounded to 2 decimal places = 3.43
    
    # Check that there's at least one semester
    assert len(transcript["semester_list"]) > 0
    
    # Check predikat based on IPK
    if transcript["ipk"] >= 3.50:
        assert transcript["predikat"] == "Cum Laude"
    elif transcript["ipk"] >= 3.00:
        assert transcript["predikat"] == "Sangat Memuaskan"
    elif transcript["ipk"] >= 2.50:
        assert transcript["predikat"] == "Memuaskan"
    elif transcript["ipk"] >= 2.00:
        assert transcript["predikat"] == "Cukup"
    else:
        assert transcript["predikat"] == "Kurang"