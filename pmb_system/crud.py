"""
CRUD operations for PMB system
Contains thread-safe functions for NIM generation and other operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import models

def generate_nim(db: Session, calon_mahasiswa_id: int) -> str:
    """
    Generate NIM for a calon mahasiswa in a thread-safe manner.
    
    Format: [Tahun:4][Kode Prodi:3][Running Number:4]
    Example: 20250010001 for Teknik Informatika, 20250020001 for Sistem Informasi
    
    Args:
        db: Database session
        calon_mahasiswa_id: ID of the calon mahasiswa
        
    Returns:
        str: Generated NIM
        
    Raises:
        ValueError: If calon mahasiswa doesn't exist, program studi doesn't exist, or student is already approved
    """
    # Get the calon mahasiswa record within a transaction for thread safety
    # Using SELECT FOR UPDATE to prevent race conditions
    calon_mahasiswa = db.query(models.CalonMahasiswa).filter(
        models.CalonMahasiswa.id == calon_mahasiswa_id
    ).with_for_update().first()
    
    if not calon_mahasiswa:
        raise ValueError(f"Calon mahasiswa with ID {calon_mahasiswa_id} not found")
    
    # Check if already approved
    if calon_mahasiswa.status == models.StatusEnum.APPROVED:
        raise ValueError(f"Calon mahasiswa with ID {calon_mahasiswa_id} is already approved")
    
    # Get the current year
    current_year = str(datetime.now().year)
    
    # Get the program studi info
    program_studi = db.query(models.ProgramStudi).filter(
        models.ProgramStudi.id == calon_mahasiswa.program_studi_id
    ).with_for_update().first()  # Lock program studi row as well to prevent race conditions
    
    if not program_studi:
        raise ValueError(f"Program studi with ID {calon_mahasiswa.program_studi_id} not found")
    
    # Count how many students have been approved in the same program in the current year
    # Using SELECT FOR UPDATE to prevent race conditions
    approved_count = db.query(models.CalonMahasiswa).filter(
        models.CalonMahasiswa.program_studi_id == calon_mahasiswa.program_studi_id,
        func.extract('year', models.CalonMahasiswa.approved_at) == int(current_year),
        models.CalonMahasiswa.status == models.StatusEnum.APPROVED
    ).with_for_update().count()
    
    # Calculate the running number (the next number in sequence)
    running_number = f"{approved_count + 1:04d}"  # Format as 4 digits with leading zeros
    
    # Generate NIM in format: [Tahun:4][Kode Prodi:3][Running Number:4]
    nim = f"{current_year}{program_studi.kode}{running_number}"
    
    # Set the NIM and update the student's status and approved_at timestamp
    calon_mahasiswa.nim = nim
    calon_mahasiswa.status = models.StatusEnum.APPROVED
    calon_mahasiswa.approved_at = datetime.now()
    
    # Commit the changes
    db.commit()
    db.refresh(calon_mahasiswa)
    
    return nim