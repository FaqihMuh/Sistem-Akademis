from typing import Dict, Any
from schedule_system.observer.subject import Observer


class StudentObserver(Observer):
    def update(self, event_type: str, schedule_data: Dict[str, Any]) -> None:
        """Send notification to students"""
        schedule_id = schedule_data.get('id', 'unknown')
        print(f"[NOTIFY] Student menerima event {event_type} untuk jadwal {schedule_id}")


class LecturerObserver(Observer):
    def update(self, event_type: str, schedule_data: Dict[str, Any]) -> None:
        """Send notification to lecturers"""
        schedule_id = schedule_data.get('id', 'unknown')
        print(f"[NOTIFY] Lecturer menerima event {event_type} untuk jadwal {schedule_id}")


class AdminObserver(Observer):
    def update(self, event_type: str, schedule_data: Dict[str, Any]) -> None:
        """Send notification to admins"""
        schedule_id = schedule_data.get('id', 'unknown')
        print(f"[NOTIFY] Admin menerima event {event_type} untuk jadwal {schedule_id}")