from sqlalchemy.orm import Session
from typing import List, Dict, Any
from grades_system.models import Grade
from krs_system.models import Matakuliah
from pmb_system.models import CalonMahasiswa
from sqlalchemy import and_, func


def calculate_ips(db: Session, nim: str, semester: str) -> float:
    """
    Calculate IPS (Index Prestasi Semester) for a student in a specific semester
    Logika:
    • ambil semua grades milik mahasiswa di semester tersebut
    • hanya hitung MK dengan nilai_angka >= 1.0 (nilai D ke atas)
    • IPS = Σ(SKS × nilai_angka) / Σ(SKS)
    • jika tidak ada nilai → return 0.0
    """
    # Get grades for the student in the specified semester with passing grades (>= D)
    grades = db.query(Grade).filter(
        and_(
            Grade.nim == nim,
            Grade.semester == semester,
            Grade.nilai_angka >= 1.0  # Only include grades with D or higher
        )
    ).all()
    
    if not grades:
        return 0.0
    
    total_sks_mutu = 0.0
    total_sks = 0
    
    for grade in grades:
        sks_mutu = grade.sks * grade.nilai_angka
        total_sks_mutu += sks_mutu
        total_sks += grade.sks
    
    if total_sks == 0:
        return 0.0
    
    ips = total_sks_mutu / total_sks
    return round(ips, 2)


def calculate_ipk(db: Session, nim: str) -> float:
    """
    Calculate IPK (Index Prestasi Kumulatif) for a student
    Logika:
    • ambil seluruh grades mahasiswa
    • jika suatu mata kuliah diulang, ambil nilai tertinggi (berdasarkan nilai_angka)
    • hanya hitung MK dengan nilai >= D
    • IPK = Σ(SKS × nilai_angka) / Σ(SKS)
    • jika mahasiswa semester 1 → return 0.0
    """
    # Get all grades for the student with passing grades (>= D)
    all_grades = db.query(Grade).filter(
        and_(
            Grade.nim == nim,
            Grade.nilai_angka >= 1.0  # Only include grades with D or higher
        )
    ).all()
    
    if not all_grades:
        return 0.0
    
    # Group grades by matakuliah_id and select the highest grade for each course
    best_grades = {}
    for grade in all_grades:
        matakuliah_id = grade.matakuliah_id
        if matakuliah_id not in best_grades or grade.nilai_angka > best_grades[matakuliah_id].nilai_angka:
            best_grades[matakuliah_id] = grade
    
    # Calculate IPK using only the best grades for each course
    total_sks_mutu = 0.0
    total_sks = 0
    
    for grade in best_grades.values():
        sks_mutu = grade.sks * grade.nilai_angka
        total_sks_mutu += sks_mutu
        total_sks += grade.sks
    
    if total_sks == 0:
        return 0.0
    
    ipk = total_sks_mutu / total_sks
    return round(ipk, 2)


def get_transcript(db: Session, nim: str) -> Dict[str, Any]:
    """
    Generate academic transcript for a student
    Return structure:
    {
      "biodata": {...},
      "semester_list": [
         {
           "semester": "1",
           "courses": [
               {"kode": "...", "nama": "...", "sks": 3, "nilai_huruf": "A", "nilai_angka": 4.0, "mutu": 12}
           ]
         }
      ],
      "total_sks": int,
      "ipk": float,
      "predikat": "Cum Laude" / "Sangat Memuaskan" / "Memuaskan"
    }
    """
    # Get student information
    student = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == nim).first()
    
    if not student:
        return {
            "biodata": {},
            "semester_list": [],
            "total_sks": 0,
            "ipk": 0.0,
            "predikat": ""
        }
    
    # Get all grades for the student (including all grades, not just passing)
    all_grades = db.query(Grade).filter(Grade.nim == nim).all()
    
    # Get course information for each grade
    course_info = {}
    for grade in all_grades:
        if grade.matakuliah_id not in course_info:
            matakuliah = db.query(Matakuliah).filter(Matakuliah.id == grade.matakuliah_id).first()
            if matakuliah:
                course_info[grade.matakuliah_id] = {
                    "kode": matakuliah.kode,
                    "nama": matakuliah.nama
                }
    
    # Group grades by semester and by course (to handle repeats)
    semester_courses = {}
    all_best_grades = {}  # For IPK calculation - best grade per course
    
    for grade in all_grades:
        semester = grade.semester
        matakuliah_id = grade.matakuliah_id
        
        # Group by semester
        if semester not in semester_courses:
            semester_courses[semester] = []
        
        # For calculating best grades per course
        if matakuliah_id not in all_best_grades or grade.nilai_angka > all_best_grades[matakuliah_id].nilai_angka:
            all_best_grades[matakuliah_id] = grade
        
        # Add course to semester
        course_data = {
            "kode": course_info.get(matakuliah_id, {}).get("kode", ""),
            "nama": course_info.get(matakuliah_id, {}).get("nama", ""),
            "sks": grade.sks,
            "nilai_huruf": grade.nilai_huruf,
            "nilai_angka": grade.nilai_angka,
            "mutu": grade.sks * grade.nilai_angka
        }
        semester_courses[semester].append(course_data)
    
    # Calculate IPK using best grades per course (only passing grades)
    passing_best_grades = {k: v for k, v in all_best_grades.items() if v.nilai_angka >= 1.0}
    
    total_sks_ipk = 0
    total_sks_mutu_ipk = 0.0
    
    for grade in passing_best_grades.values():
        total_sks_mutu_ipk += grade.sks * grade.nilai_angka
        total_sks_ipk += grade.sks
    
    ipk = 0.0
    if total_sks_ipk > 0:
        ipk = total_sks_mutu_ipk / total_sks_ipk
        ipk = round(ipk, 2)
    
    # Calculate total SKS (including failed courses)
    total_sks = sum(grade.sks for grade in all_grades)
    
    # Determine predikat based on IPK
    predikat = ""
    if ipk >= 3.50:
        predikat = "Cum Laude"
    elif ipk >= 3.00:
        predikat = "Sangat Memuaskan"
    elif ipk >= 2.50:
        predikat = "Memuaskan"
    elif ipk >= 2.00:
        predikat = "Cukup"
    else:
        predikat = "Kurang"
    
    # Format semester list
    semester_list = []
    for semester, courses in sorted(semester_courses.items()):
        semester_data = {
            "semester": semester,
            "courses": sorted(courses, key=lambda x: x["kode"])
        }
        semester_list.append(semester_data)
    
    # Sort semesters
    semester_list = sorted(semester_list, key=lambda x: x["semester"])
    
    # Create result
    result = {
        "biodata": {
            "nim": student.nim,
            "nama": student.nama_lengkap,
            "program_studi": student.program_studi.nama if student.program_studi else "",
            "fakultas": student.program_studi.fakultas if student.program_studi else ""
        },
        "semester_list": semester_list,
        "total_sks": total_sks,
        "ipk": ipk,
        "predikat": predikat
    }
    
    return result