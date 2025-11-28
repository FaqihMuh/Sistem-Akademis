from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import time
from schedule_system.models import JadwalKelas, JadwalMahasiswa, Ruang
from krs_system.models import KRSDetail, KRS
from pmb_system.models import CalonMahasiswa
from dataclasses import dataclass
from typing import NamedTuple
import bisect
from schedule_system.observer.subject import ScheduleSubject
from schedule_system.observer.observers import StudentObserver, LecturerObserver, AdminObserver


# Initialize the subject and observers
schedule_subject = ScheduleSubject()
schedule_subject.attach(StudentObserver())
schedule_subject.attach(LecturerObserver())
schedule_subject.attach(AdminObserver())


class ConflictResult(NamedTuple):
    type: str  # "room_conflict" | "lecturer_conflict" | "time_overlap"
    schedule_1: Dict[str, Any]
    schedule_2: Dict[str, Any]


def _check_time_overlap(time1_start: time, time1_end: time, time2_start: time, time2_end: time) -> bool:
    """
    Check if two time intervals overlap
    """
    return time1_start < time2_end and time2_start < time1_end


def detect_schedule_conflicts(jadwal_list: List[Dict[str, Any]]) -> List[ConflictResult]:
    """
    Detect conflicts in a list of schedules based on 3 dimensions using optimized interval checking:
    1. Room conflicts (same room, same day, overlapping time)
    2. Lecturer conflicts (same lecturer, same day, overlapping time)
    3. Time overlaps only (same day, overlapping time, regardless of room/lecturer)
    
    Args:
        jadwal_list: List of schedules with format:
                     {id, hari, jam_mulai, jam_selesai, ruangan_id, dosen_id}
    
    Returns:
        List of ConflictResult containing type and the conflicting schedule pairs
    """
    conflicts = []
    
    # Group schedules by day for processing
    day_groups = {}
    for schedule in jadwal_list:
        day = schedule['hari']
        if day not in day_groups:
            day_groups[day] = []
        day_groups[day].append(schedule)
    
    # For each day, check for conflicts using interval tree optimization
    for day, schedules in day_groups.items():
        # Sort schedules by start time for optimized checking
        sorted_schedules = sorted(schedules, key=lambda s: s['jam_mulai'])
        
        # Check each schedule against others for potential conflicts
        for i in range(len(sorted_schedules)):
            schedule1 = sorted_schedules[i]
            
            # Only check with schedules that start before schedule1 ends
            # This optimizes the check since schedules are sorted by start time
            for j in range(i + 1, len(sorted_schedules)):
                schedule2 = sorted_schedules[j]
                
                # If schedule2 starts after schedule1 ends, no more overlaps possible
                if schedule2['jam_mulai'] >= schedule1['jam_selesai']:
                    break
                
                # Check if times overlap (we already know they do based on the break condition above)
                time_overlap = _check_time_overlap(
                    schedule1['jam_mulai'], 
                    schedule1['jam_selesai'],
                    schedule2['jam_mulai'], 
                    schedule2['jam_selesai']
                )
                
                if not time_overlap:
                    continue
                
                # Check for room conflict: same room, same day, overlapping time
                if schedule1['ruangan_id'] == schedule2['ruangan_id']:
                    conflicts.append(ConflictResult(
                        type="room_conflict",
                        schedule_1=schedule1,
                        schedule_2=schedule2
                    ))
                
                # Check for lecturer conflict: same lecturer, same day, overlapping time
                if schedule1['dosen_id'] == schedule2['dosen_id']:
                    conflicts.append(ConflictResult(
                        type="lecturer_conflict",
                        schedule_1=schedule1,
                        schedule_2=schedule2
                    ))
                
                # Time overlap only - if not already covered by room or lecturer conflict
                if schedule1['ruangan_id'] != schedule2['ruangan_id'] and schedule1['dosen_id'] != schedule2['dosen_id']:
                    conflicts.append(ConflictResult(
                        type="time_overlap",
                        schedule_1=schedule1,
                        schedule_2=schedule2
                    ))
    
    return conflicts


def create_schedule(
    kode_mk: str,
    dosen_id: int,
    ruang_id: int,
    semester: str,
    hari: str,
    jam_mulai: time,
    jam_selesai: time,
    kapasitas_kelas: int,
    kelas: str = None,
    db: Session = None
) -> JadwalKelas:
    """
    Create a new schedule with transaction support
    """
    try:
        with db.begin():
            # Check for schedule conflicts before creating
            # Get all existing schedules for the same day to check for conflicts
            existing_schedules = db.query(JadwalKelas).filter(
                JadwalKelas.hari == hari
            ).all()

            # Create a temporary schedule object to check conflicts
            temp_schedule = {
                'id': -1,  # Placeholder ID
                'hari': hari,
                'jam_mulai': jam_mulai,
                'jam_selesai': jam_selesai,
                'ruangan_id': ruang_id,
                'dosen_id': dosen_id
            }

            # Convert existing schedules to the same format for conflict detection
            existing_schedule_dicts = []
            for existing in existing_schedules:
                existing_schedule_dicts.append({
                    'id': existing.id,
                    'hari': existing.hari,
                    'jam_mulai': existing.jam_mulai,
                    'jam_selesai': existing.jam_selesai,
                    'ruangan_id': existing.ruang_id,
                    'dosen_id': existing.dosen_id
                })

            # Check for conflicts
            all_schedules = existing_schedule_dicts + [temp_schedule]
            conflicts = detect_schedule_conflicts(all_schedules)

            # Filter conflicts that involve our new schedule (has id == -1)
            schedule_conflicts = [c for c in conflicts if c.schedule_1['id'] == -1 or c.schedule_2['id'] == -1]

            if schedule_conflicts:
                # Get the conflicting schedule details for error message
                conflict_details = []
                for conflict in schedule_conflicts:
                    conflicting_schedule = conflict.schedule_2 if conflict.schedule_1['id'] == -1 else conflict.schedule_1
                    conflict_details.append({
                        'type': conflict.type,
                        'conflicting_id': conflicting_schedule['id'],
                        'conflicting_details': {
                            'kode_mk': conflicting_schedule.get('kode_mk', ''),
                            'hari': conflicting_schedule.get('hari', ''),
                            'jam_mulai': str(conflicting_schedule.get('jam_mulai', '')),
                            'jam_selesai': str(conflicting_schedule.get('jam_selesai', '')),
                            'ruangan_id': conflicting_schedule.get('ruangan_id', ''),
                            'dosen_id': conflicting_schedule.get('dosen_id', '')
                        }
                    })

                # Generate suggestions for the conflicting schedule
                from schedule_system.ai_rescheduler import generate_schedule_alternatives
                suggestions = generate_schedule_alternatives(
                    kode_mk=kode_mk,
                    dosen_id=dosen_id,
                    ruang_id=ruang_id,
                    hari=hari,
                    jam_mulai=jam_mulai,
                    jam_selesai=jam_selesai,
                    kapasitas_kelas=kapasitas_kelas,
                    semester=semester,
                    db=db
                )

                # Create a structured error for conflicts with suggestions
                error_result = {
                    "conflict_details": conflict_details,
                    "suggestions": suggestions
                }
                raise ValueError(str(error_result))

            # Create the new schedule if no conflicts
            db_schedule = JadwalKelas(
                kode_mk=kode_mk,
                dosen_id=dosen_id,
                ruang_id=ruang_id,
                semester=semester,
                hari=hari,
                jam_mulai=jam_mulai,
                jam_selesai=jam_selesai,
                kapasitas_kelas=kapasitas_kelas,
                kelas=kelas
            )

            db.add(db_schedule)
            db.flush()  # Get the ID without committing

            # Prepare schedule data for notification
            schedule_data = {
                'id': db_schedule.id,
                'kode_mk': db_schedule.kode_mk,
                'dosen_id': db_schedule.dosen_id,
                'ruang_id': db_schedule.ruang_id,
                'semester': db_schedule.semester,
                'hari': db_schedule.hari,
                'jam_mulai': db_schedule.jam_mulai,
                'jam_selesai': db_schedule.jam_selesai,
                'kapasitas_kelas': db_schedule.kapasitas_kelas,
                'kelas': db_schedule.kelas
            }

            # Notify observers about the new schedule
            schedule_subject.notify("SCHEDULE_CREATED", schedule_data)

            return db_schedule
    except Exception as e:
        # If beginning transaction fails because one is already active, continue without a new transaction
        if "A transaction is already begun" in str(e):
            # Check for schedule conflicts before creating
            # Get all existing schedules for the same day to check for conflicts
            existing_schedules = db.query(JadwalKelas).filter(
                JadwalKelas.hari == hari
            ).all()

            # Create a temporary schedule object to check conflicts
            temp_schedule = {
                'id': -1,  # Placeholder ID
                'hari': hari,
                'jam_mulai': jam_mulai,
                'jam_selesai': jam_selesai,
                'ruangan_id': ruang_id,
                'dosen_id': dosen_id
            }

            # Convert existing schedules to the same format for conflict detection
            existing_schedule_dicts = []
            for existing in existing_schedules:
                existing_schedule_dicts.append({
                    'id': existing.id,
                    'hari': existing.hari,
                    'jam_mulai': existing.jam_mulai,
                    'jam_selesai': existing.jam_selesai,
                    'ruangan_id': existing.ruang_id,
                    'dosen_id': existing.dosen_id
                })

            # Check for conflicts
            all_schedules = existing_schedule_dicts + [temp_schedule]
            conflicts = detect_schedule_conflicts(all_schedules)

            # Filter conflicts that involve our new schedule (has id == -1)
            schedule_conflicts = [c for c in conflicts if c.schedule_1['id'] == -1 or c.schedule_2['id'] == -1]

            if schedule_conflicts:
                # Get the conflicting schedule details for error message
                conflict_details = []
                for conflict in schedule_conflicts:
                    conflicting_schedule = conflict.schedule_2 if conflict.schedule_1['id'] == -1 else conflict.schedule_1
                    conflict_details.append({
                        'type': conflict.type,
                        'conflicting_id': conflicting_schedule['id'],
                        'conflicting_details': {
                            'kode_mk': conflicting_schedule.get('kode_mk', ''),
                            'hari': conflicting_schedule.get('hari', ''),
                            'jam_mulai': str(conflicting_schedule.get('jam_mulai', '')),
                            'jam_selesai': str(conflicting_schedule.get('jam_selesai', '')),
                            'ruangan_id': conflicting_schedule.get('ruangan_id', ''),
                            'dosen_id': conflicting_schedule.get('dosen_id', '')
                        }
                    })

                # Generate suggestions for the conflicting schedule
                from schedule_system.ai_rescheduler import generate_schedule_alternatives
                suggestions = generate_schedule_alternatives(
                    kode_mk=kode_mk,
                    dosen_id=dosen_id,
                    ruang_id=ruang_id,
                    hari=hari,
                    jam_mulai=jam_mulai,
                    jam_selesai=jam_selesai,
                    kapasitas_kelas=kapasitas_kelas,
                    semester=semester,
                    db=db
                )

                # Create a structured error for conflicts with suggestions
                error_result = {
                    "conflict_details": conflict_details,
                    "suggestions": suggestions
                }
                raise ValueError(str(error_result))

            # Create the new schedule if no conflicts
            db_schedule = JadwalKelas(
                kode_mk=kode_mk,
                dosen_id=dosen_id,
                ruang_id=ruang_id,
                semester=semester,
                hari=hari,
                jam_mulai=jam_mulai,
                jam_selesai=jam_selesai,
                kapasitas_kelas=kapasitas_kelas,
                kelas=kelas
            )

            db.add(db_schedule)
            db.flush()  # Get the ID without committing

            # Prepare schedule data for notification
            schedule_data = {
                'id': db_schedule.id,
                'kode_mk': db_schedule.kode_mk,
                'dosen_id': db_schedule.dosen_id,
                'ruang_id': db_schedule.ruang_id,
                'semester': db_schedule.semester,
                'hari': db_schedule.hari,
                'jam_mulai': db_schedule.jam_mulai,
                'jam_selesai': db_schedule.jam_selesai,
                'kapasitas_kelas': db_schedule.kapasitas_kelas,
                'kelas': db_schedule.kelas
            }

            # Notify observers about the new schedule
            schedule_subject.notify("SCHEDULE_CREATED", schedule_data)

            return db_schedule
        else:
            # Re-raise other exceptions
            raise e


def update_schedule(
    schedule_id: int,
    kode_mk: str = None,
    dosen_id: int = None,
    ruang_id: int = None,
    semester: str = None,
    hari: str = None,
    jam_mulai: time = None,
    jam_selesai: time = None,
    kapasitas_kelas: int = None,
    kelas: str = None,
    db: Session = None
) -> JadwalKelas:
    """
    Update an existing schedule with transaction support
    """
    try:
        with db.begin():
            db_schedule = db.query(JadwalKelas).filter(JadwalKelas.id == schedule_id).first()
            if not db_schedule:
                raise ValueError(f"Schedule with ID {schedule_id} not found")

            # Determine new values or keep existing ones
            new_kode_mk = kode_mk or db_schedule.kode_mk
            new_dosen_id = dosen_id or db_schedule.dosen_id
            new_ruang_id = ruang_id or db_schedule.ruang_id
            new_semester = semester or db_schedule.semester
            new_hari = hari or db_schedule.hari
            new_jam_mulai = jam_mulai or db_schedule.jam_mulai
            new_jam_selesai = jam_selesai or db_schedule.jam_selesai
            new_kapasitas_kelas = kapasitas_kelas or db_schedule.kapasitas_kelas
            new_kelas = kelas or db_schedule.kelas

            # Check for schedule conflicts before updating
            # Get all existing schedules for the same day (excluding the one we're updating) to check for conflicts
            existing_schedules = db.query(JadwalKelas).filter(
                JadwalKelas.hari == new_hari,
                JadwalKelas.id != schedule_id  # Exclude the schedule we're updating
            ).all()

            # Create a temporary schedule object to check conflicts
            temp_schedule = {
                'id': schedule_id,  # Use the actual schedule ID
                'hari': new_hari,
                'jam_mulai': new_jam_mulai,
                'jam_selesai': new_jam_selesai,
                'ruangan_id': new_ruang_id,
                'dosen_id': new_dosen_id
            }

            # Convert existing schedules to the same format for conflict detection
            existing_schedule_dicts = []
            for existing in existing_schedules:
                existing_schedule_dicts.append({
                    'id': existing.id,
                    'hari': existing.hari,
                    'jam_mulai': existing.jam_mulai,
                    'jam_selesai': existing.jam_selesai,
                    'ruangan_id': existing.ruang_id,
                    'dosen_id': existing.dosen_id
                })

            # Check for conflicts
            all_schedules = existing_schedule_dicts + [temp_schedule]
            conflicts = detect_schedule_conflicts(all_schedules)

            # Filter conflicts that involve our updated schedule
            schedule_conflicts = [
                c for c in conflicts
                if (c.schedule_1['id'] == schedule_id or c.schedule_2['id'] == schedule_id)
            ]

            if schedule_conflicts:
                # Get the conflicting schedule details for error message
                conflict_details = []
                for conflict in schedule_conflicts:
                    other_schedule = conflict.schedule_2 if conflict.schedule_1['id'] == schedule_id else conflict.schedule_1
                    conflict_details.append({
                        'type': conflict.type,
                        'conflicting_id': other_schedule['id'],
                        'conflicting_details': {
                            'kode_mk': other_schedule.get('kode_mk', ''),
                            'hari': other_schedule.get('hari', ''),
                            'jam_mulai': str(other_schedule.get('jam_mulai', '')),
                            'jam_selesai': str(other_schedule.get('jam_selesai', '')),
                            'ruangan_id': other_schedule.get('ruangan_id', ''),
                            'dosen_id': other_schedule.get('dosen_id', '')
                        }
                    })

                # Generate suggestions for the conflicting schedule
                from schedule_system.ai_rescheduler import generate_schedule_alternatives
                suggestions = generate_schedule_alternatives(
                    kode_mk=new_kode_mk,
                    dosen_id=new_dosen_id,
                    ruang_id=new_ruang_id,
                    hari=new_hari,
                    jam_mulai=new_jam_mulai,
                    jam_selesai=new_jam_selesai,
                    kapasitas_kelas=new_kapasitas_kelas,
                    semester=new_semester,
                    db=db
                )

                # Create a structured error for conflicts with suggestions
                error_result = {
                    "conflict_details": conflict_details,
                    "suggestions": suggestions
                }
                raise ValueError(str(error_result))

            # Store the original schedule values to check if critical fields changed
            original_dosen_id = db_schedule.dosen_id
            original_ruang_id = db_schedule.ruang_id
            original_hari = db_schedule.hari
            original_jam_mulai = db_schedule.jam_mulai
            original_jam_selesai = db_schedule.jam_selesai

            # Update the schedule if no conflicts
            db_schedule.kode_mk = new_kode_mk
            db_schedule.dosen_id = new_dosen_id
            db_schedule.ruang_id = new_ruang_id
            db_schedule.semester = new_semester
            db_schedule.hari = new_hari
            db_schedule.jam_mulai = new_jam_mulai
            db_schedule.jam_selesai = new_jam_selesai
            db_schedule.kapasitas_kelas = new_kapasitas_kelas
            db_schedule.kelas = new_kelas

            # Check if any critical fields changed that would affect KRS
            schedule_changed = (
                original_dosen_id != new_dosen_id or
                original_ruang_id != new_ruang_id or
                original_hari != new_hari or
                original_jam_mulai != new_jam_mulai or
                original_jam_selesai != new_jam_selesai
            )

            db.flush()  # Refresh object state without committing

            # If critical schedule information changed, invalidate affected KRS
            if schedule_changed:
                invalidate_affected_krs(db_schedule, db)

            # Prepare updated schedule data for notification
            updated_schedule_data = {
                'id': db_schedule.id,
                'kode_mk': db_schedule.kode_mk,
                'dosen_id': db_schedule.dosen_id,
                'ruang_id': db_schedule.ruang_id,
                'semester': db_schedule.semester,
                'hari': db_schedule.hari,
                'jam_mulai': db_schedule.jam_mulai,
                'jam_selesai': db_schedule.jam_selesai,
                'kapasitas_kelas': db_schedule.kapasitas_kelas,
                'kelas': db_schedule.kelas
            }

            # Notify observers about the updated schedule
            schedule_subject.notify("SCHEDULE_UPDATED", updated_schedule_data)

            return db_schedule
    except Exception as e:
        # If beginning transaction fails because one is already active, continue without a new transaction
        if "A transaction is already begun" in str(e):
            db_schedule = db.query(JadwalKelas).filter(JadwalKelas.id == schedule_id).first()
            if not db_schedule:
                raise ValueError(f"Schedule with ID {schedule_id} not found")

            # Determine new values or keep existing ones
            new_kode_mk = kode_mk or db_schedule.kode_mk
            new_dosen_id = dosen_id or db_schedule.dosen_id
            new_ruang_id = ruang_id or db_schedule.ruang_id
            new_semester = semester or db_schedule.semester
            new_hari = hari or db_schedule.hari
            new_jam_mulai = jam_mulai or db_schedule.jam_mulai
            new_jam_selesai = jam_selesai or db_schedule.jam_selesai
            new_kapasitas_kelas = kapasitas_kelas or db_schedule.kapasitas_kelas
            new_kelas = kelas or db_schedule.kelas

            # Check for schedule conflicts before updating
            # Get all existing schedules for the same day (excluding the one we're updating) to check for conflicts
            existing_schedules = db.query(JadwalKelas).filter(
                JadwalKelas.hari == new_hari,
                JadwalKelas.id != schedule_id  # Exclude the schedule we're updating
            ).all()

            # Create a temporary schedule object to check conflicts
            temp_schedule = {
                'id': schedule_id,  # Use the actual schedule ID
                'hari': new_hari,
                'jam_mulai': new_jam_mulai,
                'jam_selesai': new_jam_selesai,
                'ruangan_id': new_ruang_id,
                'dosen_id': new_dosen_id
            }

            # Convert existing schedules to the same format for conflict detection
            existing_schedule_dicts = []
            for existing in existing_schedules:
                existing_schedule_dicts.append({
                    'id': existing.id,
                    'hari': existing.hari,
                    'jam_mulai': existing.jam_mulai,
                    'jam_selesai': existing.jam_selesai,
                    'ruangan_id': existing.ruang_id,
                    'dosen_id': existing.dosen_id
                })

            # Check for conflicts
            all_schedules = existing_schedule_dicts + [temp_schedule]
            conflicts = detect_schedule_conflicts(all_schedules)

            # Filter conflicts that involve our updated schedule
            schedule_conflicts = [
                c for c in conflicts
                if (c.schedule_1['id'] == schedule_id or c.schedule_2['id'] == schedule_id)
            ]

            if schedule_conflicts:
                # Get the conflicting schedule details for error message
                conflict_details = []
                for conflict in schedule_conflicts:
                    other_schedule = conflict.schedule_2 if conflict.schedule_1['id'] == schedule_id else conflict.schedule_1
                    conflict_details.append({
                        'type': conflict.type,
                        'conflicting_id': other_schedule['id'],
                        'conflicting_details': {
                            'kode_mk': other_schedule.get('kode_mk', ''),
                            'hari': other_schedule.get('hari', ''),
                            'jam_mulai': str(other_schedule.get('jam_mulai', '')),
                            'jam_selesai': str(other_schedule.get('jam_selesai', '')),
                            'ruangan_id': other_schedule.get('ruangan_id', ''),
                            'dosen_id': other_schedule.get('dosen_id', '')
                        }
                    })

                # Generate suggestions for the conflicting schedule
                from schedule_system.ai_rescheduler import generate_schedule_alternatives
                suggestions = generate_schedule_alternatives(
                    kode_mk=new_kode_mk,
                    dosen_id=new_dosen_id,
                    ruang_id=new_ruang_id,
                    hari=new_hari,
                    jam_mulai=new_jam_mulai,
                    jam_selesai=new_jam_selesai,
                    kapasitas_kelas=new_kapasitas_kelas,
                    semester=new_semester,
                    db=db
                )

                # Create a structured error for conflicts with suggestions
                error_result = {
                    "conflict_details": conflict_details,
                    "suggestions": suggestions
                }
                raise ValueError(str(error_result))

            # Store the original schedule values to check if critical fields changed
            original_dosen_id = db_schedule.dosen_id
            original_ruang_id = db_schedule.ruang_id
            original_hari = db_schedule.hari
            original_jam_mulai = db_schedule.jam_mulai
            original_jam_selesai = db_schedule.jam_selesai

            # Update the schedule if no conflicts
            db_schedule.kode_mk = new_kode_mk
            db_schedule.dosen_id = new_dosen_id
            db_schedule.ruang_id = new_ruang_id
            db_schedule.semester = new_semester
            db_schedule.hari = new_hari
            db_schedule.jam_mulai = new_jam_mulai
            db_schedule.jam_selesai = new_jam_selesai
            db_schedule.kapasitas_kelas = new_kapasitas_kelas
            db_schedule.kelas = new_kelas

            # Check if any critical fields changed that would affect KRS
            schedule_changed = (
                original_dosen_id != new_dosen_id or
                original_ruang_id != new_ruang_id or
                original_hari != new_hari or
                original_jam_mulai != new_jam_mulai or
                original_jam_selesai != new_jam_selesai
            )

            db.flush()  # Refresh object state without committing

            # If critical schedule information changed, invalidate affected KRS
            if schedule_changed:
                invalidate_affected_krs(db_schedule, db)

            # Prepare updated schedule data for notification
            updated_schedule_data = {
                'id': db_schedule.id,
                'kode_mk': db_schedule.kode_mk,
                'dosen_id': db_schedule.dosen_id,
                'ruang_id': db_schedule.ruang_id,
                'semester': db_schedule.semester,
                'hari': db_schedule.hari,
                'jam_mulai': db_schedule.jam_mulai,
                'jam_selesai': db_schedule.jam_selesai,
                'kapasitas_kelas': db_schedule.kapasitas_kelas,
                'kelas': db_schedule.kelas
            }

            # Notify observers about the updated schedule
            schedule_subject.notify("SCHEDULE_UPDATED", updated_schedule_data)

            return db_schedule
        else:
            # Re-raise other exceptions
            raise e


def delete_schedule(
    schedule_id: int,
    db: Session = None
) -> bool:
    """
    Delete a schedule with transaction support
    """
    try:
        with db.begin():
            db_schedule = db.query(JadwalKelas).filter(JadwalKelas.id == schedule_id).first()
            if not db_schedule:
                raise ValueError(f"Schedule with ID {schedule_id} not found")
            
            # Check if any students are registered for this schedule
            registered_students = db.query(JadwalMahasiswa).filter(
                JadwalMahasiswa.jadwal_kelas_id == schedule_id
            ).count()
            
            if registered_students > 0:
                raise ValueError(f"Cannot delete schedule with ID {schedule_id} because {registered_students} student(s) are registered")
            
            # Prepare schedule data for notification before deletion
            schedule_data = {
                'id': db_schedule.id,
                'kode_mk': db_schedule.kode_mk,
                'dosen_id': db_schedule.dosen_id,
                'ruang_id': db_schedule.ruang_id,
                'semester': db_schedule.semester,
                'hari': db_schedule.hari,
                'jam_mulai': db_schedule.jam_mulai,
                'jam_selesai': db_schedule.jam_selesai,
                'kapasitas_kelas': db_schedule.kapasitas_kelas,
                'kelas': db_schedule.kelas
            }
            
            # Delete the schedule
            db.delete(db_schedule)
            
            # Notify observers about the deleted schedule
            schedule_subject.notify("SCHEDULE_DELETED", schedule_data)
            
            return True
    except Exception as e:
        # If beginning transaction fails because one is already active, continue without a new transaction
        if "A transaction is already begun" in str(e):
            db_schedule = db.query(JadwalKelas).filter(JadwalKelas.id == schedule_id).first()
            if not db_schedule:
                raise ValueError(f"Schedule with ID {schedule_id} not found")
            
            # Check if any students are registered for this schedule
            registered_students = db.query(JadwalMahasiswa).filter(
                JadwalMahasiswa.jadwal_kelas_id == schedule_id
            ).count()
            
            if registered_students > 0:
                raise ValueError(f"Cannot delete schedule with ID {schedule_id} because {registered_students} student(s) are registered")
            
            # Prepare schedule data for notification before deletion
            schedule_data = {
                'id': db_schedule.id,
                'kode_mk': db_schedule.kode_mk,
                'dosen_id': db_schedule.dosen_id,
                'ruang_id': db_schedule.ruang_id,
                'semester': db_schedule.semester,
                'hari': db_schedule.hari,
                'jam_mulai': db_schedule.jam_mulai,
                'jam_selesai': db_schedule.jam_selesai,
                'kapasitas_kelas': db_schedule.kapasitas_kelas,
                'kelas': db_schedule.kelas
            }
            
            # Delete the schedule
            db.delete(db_schedule)
            
            # Notify observers about the deleted schedule
            schedule_subject.notify("SCHEDULE_DELETED", schedule_data)
            
            return True
        else:
            # Re-raise other exceptions
            raise e


def invalidate_affected_krs(jadwal, db: Session) -> None:
    """
    Invalidate all KRS that contain the course from the given schedule
    When a schedule changes (room, lecturer, time), set related KRS status to "REVISION"
    
    Args:
        jadwal: JadwalKelas object that was updated
        db: Database session
    """
    from krs_system.enums import KRSStatusEnum
    from krs_system.models import KRS, KRSDetail, Matakuliah
    
    # Get the matakuliah_id associated with this schedule
    matakuliah = db.query(Matakuliah).filter(Matakuliah.kode == jadwal.kode_mk).first()
    if not matakuliah:
        return  # If matakuliah doesn't exist, nothing to invalidate
    
    # Find all KRS details that reference this matakuliah
    krs_details = db.query(KRSDetail).filter(KRSDetail.matakuliah_id == matakuliah.id).all()
    
    # Get all the KRS IDs that contain this course
    krs_ids = [detail.krs_id for detail in krs_details]
    
    if not krs_ids:
        return  # No KRS contains this course, nothing to invalidate
    
    # Update all affected KRS to REVISION status
    affected_krs = db.query(KRS).filter(KRS.id.in_(krs_ids)).all()
    
    for krs in affected_krs:
        # Set status to REVISION using the proper enum
        krs.status = KRSStatusEnum.REVISION
    
    db.flush()  # Update the records in the database


def check_capacity(schedule: JadwalKelas, db: Session) -> tuple[bool, str]:
    """
    Check if the number of students registered for a course exceeds room capacity
    
    Args:
        schedule: JadwalKelas object
        db: Database session
    
    Returns:
        tuple[bool, str]: (is_valid, reason) where is_valid indicates if capacity is respected
    """
    # Get the number of students registered for this schedule
    registered_count = db.query(JadwalMahasiswa).filter(
        JadwalMahasiswa.jadwal_kelas_id == schedule.id
    ).count()
    
    # Get the room capacity
    ruang = db.query(Ruang).filter(Ruang.id == schedule.ruang_id).first()
    if not ruang:
        return False, f"Room with ID {schedule.ruang_id} not found"
    
    room_capacity = ruang.kapasitas
    
    if registered_count > room_capacity:
        return False, f"Registered students ({registered_count}) exceed room capacity ({room_capacity})"
    
    return True, f"Capacity check passed: {registered_count}/{room_capacity} students"