from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from grades_system.models import Grade, GradeHistory
from grades_system.schemas import GradeCreate, GradeUpdate
from grades_system import audit_service
from krs_system.models import Matakuliah
from pmb_system.models import CalonMahasiswa
from schedule_system.models import Dosen, JadwalMahasiswa


def get_grade_by_id(db: Session, grade_id: int):
    """Get a grade by its ID"""
    return db.query(Grade).filter(Grade.id == grade_id).first()


def get_grades_by_student(db: Session, nim: str):
    """Get all grades for a specific student"""
    return (
        db.query(Grade)
        .join(Matakuliah, Grade.matakuliah_id == Matakuliah.id)
        .filter(Grade.nim == nim)
        .add_entity(Matakuliah.kode)
        .add_entity(Matakuliah.nama)
        .all()
    )


def get_grades_by_course(db: Session, matakuliah_id: int):
    """Get all grades for a specific course"""
    return (
        db.query(Grade)
        .join(CalonMahasiswa, Grade.nim == CalonMahasiswa.nim)
        .filter(Grade.matakuliah_id == matakuliah_id)
        .add_entity(CalonMahasiswa.nama_lengkap)
        .all()
    )


def get_attendance_percentage(db: Session, nim: str, matakuliah_id: int):
    """Get attendance percentage for a student in a specific course based on schedule system"""
    # Get the course schedule for this course
    # This is a simplified version - in a real system, you'd need to map from matakuliah_id to jadwal_kelas_id
    # For now, we'll calculate attendance from the JadwalMahasiswa table
    from schedule_system.models import JadwalKelas

    # Get the matakuliah to get its kode
    matakuliah = db.query(Matakuliah).filter(Matakuliah.id == matakuliah_id).first()
    if not matakuliah:
        return 100.0  # Default to 100% if course not found

    # Get all class schedules for this course (using kode to match)
    jadwal_kelas_list = db.query(JadwalKelas).filter(JadwalKelas.kode_mk == matakuliah.kode).all()

    if not jadwal_kelas_list:
        # If not found by kode, try to find using other connections (simplified approach)
        # For now, we'll just return 100% as default
        return 100.0  # Default to 100% if no schedule found

    total_classes = 0
    attended_classes = 0

    for jadwal_kelas in jadwal_kelas_list:
        # Get student's attendance records for this class schedule
        attendance_records = db.query(JadwalMahasiswa).filter(
            and_(
                JadwalMahasiswa.jadwal_kelas_id == jadwal_kelas.id,
                JadwalMahasiswa.nim == nim
            )
        ).all()

        total_classes += len(attendance_records)
        for record in attendance_records:
            # Assuming any status except "belum_hadir" means attended
            if record.status_kehadiran != "belum_hadir":
                attended_classes += 1

    if total_classes == 0:
        return 100.0  # Default to 100% if no classes found

    attendance_percentage = (attended_classes / total_classes) * 100
    return round(attendance_percentage, 2)


def create_grade(db: Session, grade: GradeCreate, current_user: str):
    """Create a new grade record"""
    # Validate nilai_huruf
    if grade.nilai_huruf.upper() not in ['A', 'B', 'C', 'D', 'E']:
        raise ValueError("Nilai huruf harus A, B, C, D, atau E")

    # Calculate nilai_angka based on nilai_huruf
    nilai_angka_map = {
        'A': 4.0,
        'B': 3.0,
        'C': 2.0,
        'D': 1.0,
        'E': 0.0
    }
    nilai_angka = nilai_angka_map.get(grade.nilai_huruf.upper(), 0.0)

    # Check attendance requirement (>= 75%)
    # For now, use the provided presensi, but in the future, calculate from attendance records
    calculated_attendance = get_attendance_percentage(db, grade.nim, grade.matakuliah_id)

    # Use the minimum of provided presensi and calculated attendance
    final_presensi = min(grade.presensi, calculated_attendance) if calculated_attendance < 100.0 else grade.presensi

    if final_presensi < 75.0:
        raise ValueError("Presensi kurang dari 75%, tidak dapat memberikan nilai")

    # Check if dosen is teaching this course
    # For now, we'll implement this validation in the endpoint as it requires additional logic

    # Check if grade already exists for this student and course
    existing_grade = db.query(Grade).filter(
        and_(
            Grade.nim == grade.nim,
            Grade.matakuliah_id == grade.matakuliah_id
        )
    ).first()

    if existing_grade:
        # Update existing grade instead of creating a new one
        # For grade creation, we use a default reason since there's no explicit reason provided
        return update_grade(db, existing_grade.id, GradeUpdate(nilai_huruf=grade.nilai_huruf, presensi=final_presensi, reason="Update nilai dari input baru"), current_user)

    # Create new grade record
    db_grade = Grade(
        nim=grade.nim,
        matakuliah_id=grade.matakuliah_id,
        semester=grade.semester,
        nilai_huruf=grade.nilai_huruf.upper(),
        nilai_angka=nilai_angka,
        sks=grade.sks,
        dosen_id=grade.dosen_id,
        presensi=final_presensi
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade


def update_grade(db: Session, grade_id: int, grade_update: GradeUpdate, current_user: str):
    """Update an existing grade and create history record"""
    db_grade = get_grade_by_id(db, grade_id)
    if not db_grade:
        return None

    # Save old values for history
    old_nilai_huruf = db_grade.nilai_huruf
    old_nilai_angka = db_grade.nilai_angka

    # Validate the audit data before making changes
    audit_service.validate_grade_audit_data(
        old_nilai_huruf=old_nilai_huruf,
        old_nilai_angka=old_nilai_angka,
        new_nilai_huruf=grade_update.nilai_huruf if grade_update.nilai_huruf else old_nilai_huruf,
        new_nilai_angka=0.0,  # We'll get the real value after update
        changed_by=current_user,
        reason=grade_update.reason
    )

    # Update fields if provided
    if grade_update.nilai_huruf:
        if grade_update.nilai_huruf.upper() not in ['A', 'B', 'C', 'D', 'E']:
            raise ValueError("Nilai huruf harus A, B, C, D, atau E")

        # Calculate new nilai_angka
        nilai_angka_map = {
            'A': 4.0,
            'B': 3.0,
            'C': 2.0,
            'D': 1.0,
            'E': 0.0
        }
        db_grade.nilai_angka = nilai_angka_map.get(grade_update.nilai_huruf.upper(), 0.0)
        db_grade.nilai_huruf = grade_update.nilai_huruf.upper()

    if grade_update.dosen_id is not None:
        db_grade.dosen_id = grade_update.dosen_id

    if grade_update.presensi is not None:
        if grade_update.presensi < 75.0:
            raise ValueError("Presensi kurang dari 75%, tidak dapat memberikan nilai")
        # Recalculate attendance if needed
        calculated_attendance = get_attendance_percentage(db, db_grade.nim, db_grade.matakuliah_id)
        final_presensi = min(grade_update.presensi, calculated_attendance) if calculated_attendance < 100.0 else grade_update.presensi
        db_grade.presensi = final_presensi

    # Get the new nilai_angka after all updates are done
    new_nilai_angka = db_grade.nilai_angka

    # Create history record using the audit service
    audit_service.create_grade_history(
        db=db,
        grade_id=db_grade.id,
        old_nilai_huruf=old_nilai_huruf,
        old_nilai_angka=old_nilai_angka,
        new_nilai_huruf=db_grade.nilai_huruf,
        new_nilai_angka=new_nilai_angka,
        changed_by=current_user,
        reason=grade_update.reason
    )

    db.commit()
    db.refresh(db_grade)
    return db_grade


def delete_grade(db: Session, grade_id: int):
    """Delete a grade record"""
    db_grade = get_grade_by_id(db, grade_id)
    if not db_grade:
        return None
    
    db.delete(db_grade)
    db.commit()
    return db_grade


def get_grade_by_student_and_course(db: Session, nim: str, matakuliah_id: int):
    """Get a specific grade for a student in a course"""
    return db.query(Grade).filter(
        and_(
            Grade.nim == nim,
            Grade.matakuliah_id == matakuliah_id
        )
    ).first()


def validate_dosen_teaching_course(db: Session, dosen_id: int, matakuliah_id: int):
    """Validate if the dosen is teaching the specified course"""
    # Check the schedule system to verify if the dosen is assigned to teach this course
    # The dosen_id parameter in this function is actually the kode_dosen from the users table
    # We need to find the corresponding dosen record and then check the schedule
    from schedule_system.models import JadwalKelas, Dosen

    # Convert dosen_id to string to match kode_dosen (which is typically stored as string)
    try:
        kode_dosen = str(dosen_id)
    except (ValueError, TypeError):
        return False

    # Find the dosen record by kode_dosen
    dosen_record = db.query(Dosen).filter(Dosen.kode_dosen == kode_dosen).first()
    if not dosen_record:
        # If no dosen found by kode_dosen, check if the dosen_id might already be the actual id
        # Let's try to find by ID as well
        dosen_record = db.query(Dosen).filter(Dosen.id == int(dosen_id)).first()
        if not dosen_record:
            return False  # Dosen doesn't exist

    # Get the course's kode to match with schedule
    from krs_system.models import Matakuliah
    matakuliah = db.query(Matakuliah).filter(Matakuliah.id == matakuliah_id).first()
    if not matakuliah:
        return False  # Course doesn't exist

    # Check if there's a class schedule where this dosen (by their ID) teaches this course
    schedule_check = db.query(JadwalKelas).filter(
        JadwalKelas.kode_mk == matakuliah.kode,
        JadwalKelas.dosen_id == dosen_record.id  # Use the dosen's actual ID, not kode_dosen
    ).first()

    return schedule_check is not None


def get_dosen_by_id(db: Session, dosen_id: int):
    """Get dosen by ID"""
    from schedule_system.models import Dosen
    return db.query(Dosen).filter(Dosen.id == dosen_id).first()


def get_matakuliah_by_id(db: Session, matakuliah_id: int):
    """Get matakuliah by ID"""
    from krs_system.models import Matakuliah
    return db.query(Matakuliah).filter(Matakuliah.id == matakuliah_id).first()


def get_mahasiswa_by_nim(db: Session, nim: str):
    """Get mahasiswa by NIM"""
    from pmb_system.models import CalonMahasiswa
    return db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == nim).first()