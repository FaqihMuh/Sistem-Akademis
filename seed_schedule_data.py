"""
Seed data script for the schedule system tables
This script adds basic data for dosen and ruang tables to support testing
"""

import sqlite3
from datetime import datetime, time


def seed_database():
    # Connect to the database
    conn = sqlite3.connect('pmb_local.db')
    cursor = conn.cursor()
    
    try:
        # Insert sample dosen data
        dosen_data = [
            (1, "1234567890", "Dr. Budi Santoso", "budi.santoso@email.com", "081234567890", "Teknik Informatika"),
            (2, "1234567891", "Dr. Siti Aminah", "siti.aminah@email.com", "081234567891", "Sistem Informasi"),
            (3, "1234567892", "Prof. Ahmad Hidayat", "ahmad.hidayat@email.com", "081234567892", "Teknik Komputer"),
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO dosen (id, nip, nama, email, phone, program_studi, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', dosen_data)
        
        # Insert sample ruang data
        ruang_data = [
            (1, "A101", "Ruang Kelas A101", 60, "Kelas"),
            (2, "B201", "Ruang Kelas B201", 50, "Kelas"),
            (3, "LabTI1", "Laboratorium Teknik Informatika 1", 30, "Laboratorium"),
            (4, "LabSI1", "Laboratorium Sistem Informasi 1", 25, "Laboratorium"),
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO ruang (id, kode, nama, kapasitas, jenis, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', ruang_data)
        
        # Commit the changes
        conn.commit()
        print("Seed data successfully added to database!")
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM dosen")
        dosen_count = cursor.fetchone()[0]
        print(f"Number of dosen records: {dosen_count}")
        
        cursor.execute("SELECT COUNT(*) FROM ruang")
        ruang_count = cursor.fetchone()[0]
        print(f"Number of ruang records: {ruang_count}")
        
    except Exception as e:
        print(f"Error inserting seed data: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()