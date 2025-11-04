"""
PMB System Router - extracted from main.py for integration with combined system
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime
import re
import sys
import os

# Add the current directory to the path to support both relative imports and direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def import_modules():
    """Import modules with both relative and absolute fallbacks"""
    global Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum, models
    global get_db_func, SessionLocal, database
    global generate_nim, crud
    global schemas
    global commit_with_retry
    
    # First try relative imports
    try:
        from . import models as _models
        from .models import Base as _Base, CalonMahasiswa as _CM, ProgramStudi as _PS, JalurMasukEnum as _JME, StatusEnum as _SE
        from . import database as _database
        from .database import get_db as _get_db_func, SessionLocal as _SessionLocal, commit_with_retry
        from . import crud as _crud
        from .crud import generate_nim as _generate_nim
        from . import schemas as _schemas
        Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum = _Base, _CM, _PS, _JME, _SE
        get_db_func, SessionLocal = _get_db_func, _SessionLocal
        models = _models
        database = _database
        crud = _crud
        generate_nim = _generate_nim
        schemas = _schemas
    except ImportError:
        # Fall back to absolute imports
        import models as _models
        from models import Base as _Base, CalonMahasiswa as _CM, ProgramStudi as _PS, JalurMasukEnum as _JME, StatusEnum as _SE
        import database as _database
        from database import get_db as _get_db_func, SessionLocal as _SessionLocal, commit_with_retry
        import crud as _crud
        from crud import generate_nim as _generate_nim
        import schemas as _schemas
        Base, CalonMahasiswa, ProgramStudi, JalurMasukEnum, StatusEnum = _Base, _CM, _PS, _JME, _SE
        get_db_func, SessionLocal = _get_db_func, _SessionLocal
        models = _models
        database = _database
        crud = _crud
        generate_nim = _generate_nim
        schemas = _schemas

import_modules()

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict
from datetime import datetime

# Create a router for PMB endpoints
router = APIRouter(prefix="/api/pmb", tags=["PMB"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. POST /api/pmb/register → menerima JSON calon mahasiswa, validasi input, status default = 'pending'.
@router.post("/register", response_model=schemas.CalonMahasiswaResponse)
def register_calon_mahasiswa(
    calon_mahasiswa: schemas.CalonMahasiswaCreate,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_email = db.query(models.CalonMahasiswa).filter(models.CalonMahasiswa.email == calon_mahasiswa.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Validate program_studi_id exists
    program_studi = db.query(models.ProgramStudi).filter(models.ProgramStudi.id == calon_mahasiswa.program_studi_id).first()
    if not program_studi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program Studi not found"
        )
    
    # Create new calon mahasiswa with status pending (the default)
    db_calon_mahasiswa = models.CalonMahasiswa(
        nama_lengkap=calon_mahasiswa.nama_lengkap,
        email=calon_mahasiswa.email,
        phone=calon_mahasiswa.phone,
        tanggal_lahir=calon_mahasiswa.tanggal_lahir,
        alamat=calon_mahasiswa.alamat,
        program_studi_id=calon_mahasiswa.program_studi_id,
        jalur_masuk=models.JalurMasukEnum(calon_mahasiswa.jalur_masuk)
        # status will default to pending
    )
    
    db.add(db_calon_mahasiswa)
    commit_with_retry(db)  # Use retry logic for commit
    db.refresh(db_calon_mahasiswa)
    
    return db_calon_mahasiswa

# 2. PUT /api/pmb/approve/{id} → ubah status ke 'approved', generate NIM format [tahun][kode_prodi][running number], return NIM.
@router.put("/approve/{id}", response_model=dict)
def approve_calon_mahasiswa(
    id: int,
    db: Session = Depends(get_db)
):
    # Get the calon mahasiswa by ID
    calon_mahasiswa = db.query(models.CalonMahasiswa).filter(models.CalonMahasiswa.id == id).first()
    if not calon_mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calon mahasiswa not found"
        )
    
    # Check if already approved
    if calon_mahasiswa.status == models.StatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calon mahasiswa already approved"
        )
    
    # Generate NIM using the thread-safe function
    try:
        nim = crud.generate_nim(db, id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Update the status and approved_at timestamp
    calon_mahasiswa.status = models.StatusEnum.APPROVED
    calon_mahasiswa.approved_at = datetime.now()
    
    commit_with_retry(db)  # Use retry logic for commit
    db.refresh(calon_mahasiswa)
    
    return {"nim": nim, "message": "Calon mahasiswa approved successfully"}

# 3. GET /api/pmb/status/{id} → tampilkan data pendaftar dan statusnya.
@router.get("/status/{id}", response_model=schemas.CalonMahasiswaResponse)
def get_calon_mahasiswa_status(
    id: int,
    db: Session = Depends(get_db)
):
    calon_mahasiswa = db.query(models.CalonMahasiswa).filter(models.CalonMahasiswa.id == id).first()
    if not calon_mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calon mahasiswa not found"
        )
    
    return calon_mahasiswa

# 4. GET /api/pmb/stats → jumlah pendaftar per jalur_masuk.
@router.get("/stats", response_model=Dict[str, int])
def get_pmb_stats(
    db: Session = Depends(get_db)
):
    # Count number of applicants per jalur_masuk
    stats = db.query(
        models.CalonMahasiswa.jalur_masuk,
        func.count(models.CalonMahasiswa.id).label('count')
    ).group_by(models.CalonMahasiswa.jalur_masuk).all()
    
    # Convert to dictionary
    result = {}
    for jalur, count in stats:
        result[jalur.value] = count
    
    # Ensure all jalur masuk types are represented, even if count is 0
    for jalur in models.JalurMasukEnum:
        if jalur.value not in result:
            result[jalur.value] = 0
    
    return result

# Endpoint for creating program studies
@router.post("/program-studi", response_model=schemas.ProgramStudiResponse)
def create_program_studi(
    program_studi: schemas.ProgramStudiCreate,
    db: Session = Depends(get_db)
):
    # Check if kode already exists
    existing_kode = db.query(models.ProgramStudi).filter(models.ProgramStudi.kode == program_studi.kode).first()
    if existing_kode:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kode program studi already exists"
        )
    
    # Create new program studi
    db_program_studi = models.ProgramStudi(
        kode=program_studi.kode,
        nama=program_studi.nama,
        fakultas=program_studi.fakultas
    )
    
    db.add(db_program_studi)
    commit_with_retry(db)  # Use retry logic for commit
    db.refresh(db_program_studi)
    
    return db_program_studi

# Endpoint for getting all program studies
@router.get("/program-studi", response_model=List[schemas.ProgramStudiResponse])
def get_all_program_studi(
    db: Session = Depends(get_db)
):
    program_studi = db.query(models.ProgramStudi).all()
    return program_studi

# Endpoint for getting a specific program study by ID
@router.get("/program-studi/{id}", response_model=schemas.ProgramStudiResponse)
def get_program_studi(
    id: int,
    db: Session = Depends(get_db)
):
    program_studi = db.query(models.ProgramStudi).filter(models.ProgramStudi.id == id).first()
    if not program_studi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program Studi not found"
        )
    
    return program_studi