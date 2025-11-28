from typing import List, Dict, Any
from sqlalchemy.orm import Session
from schedule_system.models import JadwalKelas, Ruang, JadwalMahasiswa
from schedule_system.services import detect_schedule_conflicts
from datetime import time


def suggest_alternative_slots(conflict: Dict[str, Any], available_slots: List[Dict[str, Any]], db: Session) -> List[Dict[str, Any]]:
    """
    Suggest alternative time slots for resolving schedule conflicts

    Args:
        conflict: Dictionary containing conflict information
        available_slots: List of available time slots with format:
                        {hari, jam_mulai, jam_selesai, ruangan_id}
        db: Database session

    Returns:
        List of 3 recommended slots with format:
        [
            {hari, jam_mulai, jam_selesai, ruangan, reason},
            ...
        ]
    """
    suggestions = []

    # Determine which schedule is involved in the conflict and get its details
    schedule_1 = conflict['schedule_1']
    schedule_2 = conflict['schedule_2']

    # Extract the schedule that needs to be rescheduled (we'll focus on schedule_1)
    target_schedule = schedule_1  # We'll suggest alternatives for schedule_1

    # Get the course ID to find registered students
    target_jadwal_kelas = db.query(JadwalKelas).filter(JadwalKelas.id == target_schedule['id']).first()
    if not target_jadwal_kelas:
        return []

    # Get students registered for this schedule
    registered_students = db.query(JadwalMahasiswa).filter(
        JadwalMahasiswa.jadwal_kelas_id == target_schedule['id']
    ).all()
    student_nims = [reg.nim for reg in registered_students]

    # Get lecturer ID and current room ID
    lecturer_id = target_schedule['dosen_id']
    current_room_id = target_schedule['ruangan_id']

    # Evaluate each available slot
    valid_slots = []
    for slot in available_slots:
        # Check 1: Room capacity
        room = db.query(Ruang).filter(Ruang.id == slot['ruangan_id']).first()
        if not room or room.kapasitas < len(student_nims):
            continue  # Skip if room capacity is insufficient

        # Check 2: Lecturer availability (no conflicts)
        # Get all existing schedules for this lecturer on this day
        lecturer_schedules = db.query(JadwalKelas).filter(
            JadwalKelas.dosen_id == lecturer_id,
            JadwalKelas.hari == slot['hari'],
            JadwalKelas.id != target_schedule['id']  # Exclude current schedule
        ).all()

        # Check for time conflicts with lecturer's other classes
        has_lecturer_conflict = False
        for existing_schedule in lecturer_schedules:
            if (slot['jam_mulai'] < existing_schedule.jam_selesai and
                slot['jam_selesai'] > existing_schedule.jam_mulai):
                has_lecturer_conflict = True
                break

        if has_lecturer_conflict:
            continue  # Skip if lecturer has a conflict

        # Check 3: Student schedule conflicts
        has_student_conflict = False
        if student_nims:
            # Get all class schedules for these students on the target day
            student_class_schedules = db.query(JadwalKelas).join(JadwalMahasiswa).filter(
                JadwalMahasiswa.nim.in_(student_nims),
                JadwalKelas.hari == slot['hari'],
                JadwalKelas.id != target_schedule['id']  # Exclude current schedule
            ).all()

            # Check if the proposed slot conflicts with any student's existing classes
            for student_schedule in student_class_schedules:
                if (slot['jam_mulai'] < student_schedule.jam_selesai and
                    slot['jam_selesai'] > student_schedule.jam_mulai):
                    has_student_conflict = True
                    break

        if has_student_conflict:
            continue  # Skip if it conflicts with student schedules

        # If all checks pass, this is a valid slot
        valid_slots.append(slot)

    # Sort valid slots based on preference: morning -> afternoon -> evening
    def time_preference(slot):
        hour = slot['jam_mulai'].hour
        if 8 <= hour <= 11:  # Morning
            return 0
        elif 12 <= hour <= 15:  # Afternoon
            return 1
        else:  # Evening
            return 2

    valid_slots.sort(key=lambda x: (time_preference(x), x['jam_mulai']))

    # Generate suggestions with reasons
    for i, slot in enumerate(valid_slots[:3]):  # Take up to 3 suggestions
        room = db.query(Ruang).filter(Ruang.id == slot['ruangan_id']).first()
        room_name = room.nama if room else f"Room ID {slot['ruangan_id']}"

        # Determine reason for the suggestion
        time_period = "pagi" if 8 <= slot['jam_mulai'].hour <= 11 else \
                     "siang" if 12 <= slot['jam_mulai'].hour <= 15 else "sore"

        reason = f"Tidak bentrok dosen + ruangan kosong + kapasitas mencukupi, waktu {time_period}"

        suggestion = {
            'hari': slot['hari'],
            'jam_mulai': slot['jam_mulai'],
            'jam_selesai': slot['jam_selesai'],
            'ruang_id': slot['ruangan_id'],  # Changed to match requirements
            'reason': reason
        }
        suggestions.append(suggestion)

    # If we don't have 3 suggestions and there's a current room, consider keeping same room
    if len(suggestions) < 3:
        # Try to find other times in the same room
        same_room_slots = [slot for slot in available_slots if slot['ruangan_id'] == current_room_id]
        for slot in same_room_slots:
            if len(suggestions) >= 3:
                break
            if not any(s['hari'] == slot['hari'] and
                      s['jam_mulai'] == slot['jam_mulai'] and
                      s['jam_selesai'] == slot['jam_selesai'] for s in suggestions):
                room = db.query(Ruang).filter(Ruang.id == slot['ruangan_id']).first()
                room_name = room.nama if room else f"Room ID {slot['ruangan_id']}"

                reason = f"Tetap di ruangan yang sama, waktu {time_period}"

                suggestion = {
                    'hari': slot['hari'],
                    'jam_mulai': slot['jam_mulai'],
                    'jam_selesai': slot['jam_selesai'],
                    'ruang_id': slot['ruangan_id'],  # Changed to match requirements
                    'reason': reason
                }
                suggestions.append(suggestion)

    # Return up to 3 suggestions
    return suggestions[:3]


def generate_schedule_alternatives(
    kode_mk: str,
    dosen_id: int,
    ruang_id: int,  # Original ruang_id for student conflict checking
    hari: str,
    jam_mulai: time,
    jam_selesai: time,
    kapasitas_kelas: int,
    semester: str,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Generate alternative schedules for a given schedule that would cause conflicts
    This function performs comprehensive validation identical to detect_schedule_conflict logic

    The function checks for conflicts against ALL existing schedules in the database
    excluding potentially the same schedule that is being updated/created.

    Args:
        All schedule details that would cause conflicts

    Returns:
        List of 3 recommended slots with format:
        [
            {"hari": "senin", "jam_mulai": "09:00", "jam_selesai": "11:00", "ruang_id": 2, "reason": "..."},
            ...
        ]
    """
    from schedule_system.services import _check_time_overlap

    suggestions = []

    # Get ALL existing schedules from the database (no filtering)
    all_existing_schedules = db.query(JadwalKelas).all()

    # Get all available rooms
    all_rooms = db.query(Ruang).all()

    # Calculate expected student count based on the provided kapasitas_kelas
    expected_student_count = kapasitas_kelas

    # Define available time slots according to specification
    time_slots = [
        (time(8, 0), time(10, 0)),   # 08:00–10:00
        (time(10, 0), time(12, 0)),  # 10:00–12:00
        (time(13, 0), time(15, 0)),  # 13:00–15:00
        (time(15, 0), time(17, 0))   # 15:00–17:00
    ]

    # Define available days
    days = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]

    # Validate each possible slot against ALL existing schedules
    valid_slots = []
    for day in days:
        for start_time, end_time in time_slots:
            for room in all_rooms:
                # Check 1: Room capacity
                if room.kapasitas < expected_student_count:
                    print(f"[DEBUG] Skip slot: {day} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} in room {room.id} karena kapasitas ruangan tidak mencukupi (butuh {expected_student_count}, tersedia {room.kapasitas})")
                    continue  # Skip if room capacity is insufficient

                # Check against ALL existing schedules using the same conflict detection logic
                is_invalid = False

                for existing_schedule in all_existing_schedules:
                    # Check for room conflict: same day, same room, overlapping time
                    if (existing_schedule.hari == day and
                        existing_schedule.ruang_id == room.id and
                        _check_time_overlap(start_time, end_time, existing_schedule.jam_mulai, existing_schedule.jam_selesai)):
                        print(f"[DEBUG] Skip slot: {day} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} in room {room.id} karena bentrok ruangan dengan jadwal {existing_schedule.id}")
                        is_invalid = True
                        break

                    # Check for lecturer conflict: same day, same lecturer, overlapping time
                    if (existing_schedule.hari == day and
                        existing_schedule.dosen_id == dosen_id and
                        _check_time_overlap(start_time, end_time, existing_schedule.jam_mulai, existing_schedule.jam_selesai)):
                        print(f"[DEBUG] Skip slot: {day} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} untuk dosen {dosen_id} karena bentrok dosen dengan jadwal {existing_schedule.id}")
                        is_invalid = True
                        break

                if is_invalid:
                    continue  # Skip this slot if any conflict was detected

                # If all checks pass, this is a valid slot
                valid_slots.append({
                    'hari': day,
                    'jam_mulai': start_time,
                    'jam_selesai': end_time,
                    'ruangan_id': room.id
                })

    # Sort valid slots based on preference: morning -> afternoon -> evening
    def time_preference(slot):
        hour = slot['jam_mulai'].hour
        if 8 <= hour <= 11:  # Morning
            return 0
        elif 12 <= hour <= 15:  # Afternoon
            return 1
        else:  # Evening
            return 2

    valid_slots.sort(key=lambda x: (time_preference(x), x['jam_mulai']))

    # Generate suggestions with reasons
    for i, slot in enumerate(valid_slots[:3]):  # Take up to 3 suggestions
        room = db.query(Ruang).filter(Ruang.id == slot['ruangan_id']).first()

        # Determine reason for the suggestion
        time_period = "pagi" if 8 <= slot['jam_mulai'].hour <= 11 else \
                     "siang" if 12 <= slot['jam_mulai'].hour <= 15 else "sore"

        reason = f"Tidak bentrok dosen + ruangan kosong + kapasitas mencukupi, waktu {time_period}"

        suggestion = {
            'hari': slot['hari'],
            'jam_mulai': slot['jam_mulai'].strftime("%H:%M"),
            'jam_selesai': slot['jam_selesai'].strftime("%H:%M"),
            'ruang_id': slot['ruangan_id'],
            'reason': reason
        }
        suggestions.append(suggestion)

    return suggestions[:3]