"""
Admin API endpoints for dashboard data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pmb_system.database import get_db
from typing import List, Dict, Any
from schedule_system.models import JadwalKelas as Jadwal
from auth_system.dependencies import get_current_user
from krs_system.models import KRS
from pmb_system.models import CalonMahasiswa, ProgramStudi
from payment_system.models import Billing, Payment
from sqlalchemy import extract
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin Dashboard Data"])


@router.get("/summary")
def admin_summary(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_pmb = db.query(CalonMahasiswa).count()
    total_mahasiswa = db.query(CalonMahasiswa).filter(
        CalonMahasiswa.status == "APPROVED"
    ).count()
    total_krs = db.query(KRS).count()
    total_schedule = db.query(Jadwal).count()

    return {
        "total_pmb": total_pmb,
        "total_mahasiswa": total_mahasiswa,
        "total_krs": total_krs,
        "total_schedule": total_schedule
    }


# Admin endpoints to get all data for dashboard
@router.get("/pmb", response_model=List[Dict[str, Any]])
def get_all_pmb(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all PMB (calon mahasiswa) data for admin dashboard
    """
    try:
        from pmb_system.models import CalonMahasiswa

        pmb_records = db.query(CalonMahasiswa).all()

        # Convert to the required format
        pmb_data = []
        for record in pmb_records:
            pmb_data.append({
                "id": record.id,
                "nim": record.nim,
                "nama": record.nama_lengkap,
                "email": record.email,
                "status": record.status.value if hasattr(record.status, 'value') else record.status,
                "program_studi_id": record.program_studi_id,
                "jalur_masuk": record.jalur_masuk.value if hasattr(record.jalur_masuk, 'value') else record.jalur_masuk,
                "created_at": record.created_at
            })

        return pmb_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving PMB data: {str(e)}")


@router.get("/krs", response_model=List[Dict[str, Any]])
def get_all_krs(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all KRS data for admin dashboard
    """
    try:
        from krs_system.models import KRS as KRSModel

        krs_records = db.query(KRSModel).all()

        # Convert to the required format
        krs_data = []
        for record in krs_records:
            krs_data.append({
                "id": record.id,
                "nim": record.nim,
                "semester": record.semester,
                "status": record.status.value if hasattr(record.status, 'value') else record.status,
                "dosen_pa_id": record.dosen_pa_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            })

        return krs_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving KRS data: {str(e)}")


@router.get("/schedule", response_model=List[Dict[str, Any]])
def get_all_schedule(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all Schedule data for admin dashboard
    """
    try:
        from schedule_system.models import JadwalKelas

        schedule_records = db.query(JadwalKelas).all()

        # Convert to the required format
        schedule_data = []
        for record in schedule_records:
            schedule_data.append({
                "id": record.id,
                "kode_mk": record.kode_mk,
                "dosen_id": record.dosen_id,
                "kelas": record.kelas,
                "hari": record.hari,
                "jam_mulai": record.jam_mulai,
                "jam_selesai": record.jam_selesai,
                "ruang_id": record.ruang_id,
                "kuota": record.kuota,
                "created_at": record.created_at
            })

        return schedule_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Schedule data: {str(e)}")


@router.get("/payment-summary")
def get_payment_summary(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment summary data for admin dashboard:
    - Collection rate per program study
    - Monthly payment chart data
    """
    try:
        # Get all billings
        billings = db.query(Billing).all()

        # Get all students to map NIM to program study
        students = db.query(CalonMahasiswa).all()

        # Create mapping of NIM to program study
        nim_to_prodi = {}
        prodi_names = {}
        for student in students:
            nim_to_prodi[student.nim] = student.program_studi_id
            # Get program study name
            prodi = db.query(ProgramStudi).filter(ProgramStudi.id == student.program_studi_id).first()
            if prodi:
                prodi_names[student.program_studi_id] = f"{prodi.nama} ({prodi.kode})"
            else:
                prodi_names[student.program_studi_id] = f"Program Studi {student.program_studi_id}"

        # Calculate collection rate per program study
        prodi_stats = {}
        for billing in billings:
            prodi_id = nim_to_prodi.get(billing.nim)
            if prodi_id:
                if prodi_id not in prodi_stats:
                    prodi_stats[prodi_id] = {
                        "total_mahasiswa": 0,
                        "sudah_bayar": 0,
                        "total_billing": 0,
                        "paid_billing": 0
                    }

                prodi_stats[prodi_id]["total_mahasiswa"] += 1
                prodi_stats[prodi_id]["total_billing"] += 1

                # Count if billing is paid or partially paid
                if billing.status in ["paid", "partial"]:
                    prodi_stats[prodi_id]["sudah_bayar"] += 1
                    prodi_stats[prodi_id]["paid_billing"] += 1

        # Format collection rate data
        collection_rate_per_prodi = []
        for prodi_id, stats in prodi_stats.items():
            if stats["total_billing"] > 0:
                collection_rate = (stats["paid_billing"] / stats["total_billing"]) * 100
            else:
                collection_rate = 0

            collection_rate_per_prodi.append({
                "program_studi": prodi_names.get(prodi_id, f"Program Studi {prodi_id}"),
                "total_mahasiswa": stats["total_mahasiswa"],
                "sudah_bayar": stats["sudah_bayar"],
                "collection_rate": round(collection_rate, 2)
            })

        # Get all payments for monthly chart
        payments = db.query(Payment).all()

        # Group payments by month
        monthly_payments = {}
        for payment in payments:
            if payment.paid_at:
                month_year = payment.paid_at.strftime("%Y-%m")  # Format as "YYYY-MM"
                if month_year in monthly_payments:
                    monthly_payments[month_year] += payment.amount
                else:
                    monthly_payments[month_year] = payment.amount

        # Sort monthly payments by date and format for chart
        sorted_months = sorted(monthly_payments.keys())
        monthly_payment_chart_data = [
            {"month": month, "total_payment": monthly_payments[month]}
            for month in sorted_months
        ]

        return {
            "collection_rate_per_prodi": collection_rate_per_prodi,
            "monthly_payment_chart_data": monthly_payment_chart_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving payment summary data: {str(e)}")