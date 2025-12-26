import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pmb_system.database import SessionLocal
from pmb_system.models import CalonMahasiswa

def check_pmb_data():
    """Check if there are PMB records in the database"""
    db = SessionLocal()
    try:
        # Count PMB records
        total_pmb = db.query(CalonMahasiswa).count()
        approved_pmb = db.query(CalonMahasiswa).filter(
            CalonMahasiswa.status == "APPROVED"
        ).count()
        
        print(f"Total PMB records: {total_pmb}")
        print(f"Approved PMB records: {approved_pmb}")
        
        if total_pmb > 0:
            # Show first few records
            pmb_records = db.query(CalonMahasiswa).limit(5).all()
            print("\nFirst 5 PMB records:")
            for record in pmb_records:
                print(f"  ID: {record.id}, NIM: {record.nim}, Name: {record.nama_lengkap}, Status: {record.status}")
        
    except Exception as e:
        print(f"Error checking PMB data: {e}")
    finally:
        db.close()

def check_krs_data():
    """Check if there are KRS records in the database"""
    db = SessionLocal()
    try:
        from krs_system.models import KRS
        total_krs = db.query(KRS).count()
        print(f"Total KRS records: {total_krs}")
        
        if total_krs > 0:
            krs_records = db.query(KRS).limit(5).all()
            print("\nFirst 5 KRS records:")
            for record in krs_records:
                print(f"  ID: {record.id}, NIM: {record.nim}, Semester: {record.semester}, Status: {record.status}")
        
    except Exception as e:
        print(f"Error checking KRS data: {e}")
    finally:
        db.close()

def check_schedule_data():
    """Check if there are Schedule records in the database"""
    db = SessionLocal()
    try:
        from schedule_system.models import JadwalKelas
        total_schedule = db.query(JadwalKelas).count()
        print(f"Total Schedule records: {total_schedule}")
        
        if total_schedule > 0:
            schedule_records = db.query(JadwalKelas).limit(5).all()
            print("\nFirst 5 Schedule records:")
            for record in schedule_records:
                print(f"  ID: {record.id}, Kode MK: {record.kode_mk}, Dosen ID: {record.dosen_id}, Hari: {record.hari}")
        
    except Exception as e:
        print(f"Error checking Schedule data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Checking database for existing data...")
    check_pmb_data()
    check_krs_data()
    check_schedule_data()