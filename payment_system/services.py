"""
Payment system services module
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
from fastapi import HTTPException
from datetime import date, timedelta
from pmb_system.database import get_db  # Using get_db from pmb_system.database as required
from .models import Billing, Payment, PaymentMethod
from .schemas import BillingCreate, BillingUpdate, PaymentCreate, PaymentMethodCreate
from pmb_system.models import StatusEnum
from krs_system.models import KRS

def get_billing_by_id(db: Session, billing_id: int):
    """Get a billing by its ID"""
    return db.query(Billing).filter(Billing.id == billing_id).first()


def get_billings_by_nim(db: Session, nim: str):
    """Get all billings for a specific student"""
    return db.query(Billing).filter(Billing.nim == nim).all()


def create_billing(db: Session, billing: BillingCreate):
    """Create a new billing record"""
    db_billing = Billing(**billing.model_dump())
    db.add(db_billing)
    db.commit()
    db.refresh(db_billing)
    return db_billing


def update_billing(db: Session, billing_id: int, billing_update: BillingUpdate):
    """Update a billing record"""
    db_billing = db.query(Billing).filter(Billing.id == billing_id).first()
    if db_billing:
        for field, value in billing_update.model_dump(exclude_unset=True).items():
            setattr(db_billing, field, value)
        db.commit()
        db.refresh(db_billing)
    return db_billing


def process_payment(db: Session, billing_id: int, amount: int, method_id: int, transaction_ref: str):
    """
    Process a payment for a specific billing

    Args:
        db: Database session
        billing_id: ID of the billing to pay
        amount: Amount to pay
        method_id: Payment method ID
        transaction_ref: Transaction reference string

    Returns:
        Updated billing object

    Raises:
        HTTPException: If billing not found
    """
    # Get billing by ID
    billing = db.query(Billing).filter(Billing.id == billing_id).first()
    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")

    # Create new payment record
    payment = Payment(
        billing_id=billing_id,
        amount=amount,
        method_id=method_id,
        transaction_ref=transaction_ref
    )
    db.add(payment)

    # Update billing paid amount
    billing.paid_amount += amount

    # Update billing status based on paid amount vs total amount
    if billing.paid_amount >= billing.total_amount:
        billing.status = "paid"
    elif billing.paid_amount > 0:
        billing.status = "partial"
    else:
        billing.status = "unpaid"

    #UNBLOCK KRS
    if billing.status in ("partial", "paid"):
        krs = db.query(KRS).filter(
            KRS.nim == billing.nim,
            KRS.semester == billing.semester
        ).first()

        if krs and krs.status == "BLOCKED":
            krs.status = "DRAFT"
            print(f"KRS UNBLOCKED → NIM {billing.nim} semester {billing.semester}")

    # Commit all changes in single transaction
    db.commit()
    db.refresh(billing)
    db.refresh(payment)

    return billing


def get_payment_by_id(db: Session, payment_id: int):
    """Get a payment by its ID"""
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payments_by_billing_id(db: Session, billing_id: int):
    """Get all payments for a specific billing"""
    return db.query(Payment).filter(Payment.billing_id == billing_id).all()


def create_payment(db: Session, payment: PaymentCreate):
    """Create a new payment record"""
    db_payment = Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    # Update the billing status after payment
    billing = get_billing_by_id(db, payment.billing_id)
    if billing:
        # Update paid amount
        billing.paid_amount += payment.amount

        # Update status based on paid amount vs total
        if billing.paid_amount >= billing.total_amount:
            billing.status = "paid"
        elif billing.paid_amount > 0:
            billing.status = "partial"
        else:
            billing.status = "unpaid"

        db.commit()
        db.refresh(billing)

    return db_payment


def get_payment_method_by_id(db: Session, method_id: int):
    """Get a payment method by its ID"""
    return db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()


def get_all_payment_methods(db: Session):
    """Get all payment methods"""
    return db.query(PaymentMethod).all()


def create_payment_method(db: Session, payment_method: PaymentMethodCreate):
    """Create a new payment method"""
    db_method = PaymentMethod(**payment_method.model_dump())
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method


def generate_billing_for_student(db: Session, nim: str, semester: str):
    """
    Generate billing for a specific student and semester

    Args:
        db: Database session
        nim: Student NIM
        semester: Semester identifier (e.g., "2025/1")

    Returns:
        Created billing object
    """
    from krs_system.models import KRS  # Import KRS model from existing module
    from pmb_system.models import CalonMahasiswa, ProgramStudi  # Import models from existing module

    # Debug: Show all KRS records for this semester
    print(f"Debug: Looking for KRS with nim={nim}, semester={semester}")
    all_krs_for_semester = db.query(KRS).filter(KRS.semester == semester).all()
    print(f"Debug: Found {len(all_krs_for_semester)} KRS records for semester {semester}")
    for krs_rec in all_krs_for_semester:
        print(f"  - NIM: {krs_rec.nim}, Semester: {krs_rec.semester}")

    # Check if KRS record exists for this student and semester
    krs_record = db.query(KRS).filter(
        KRS.nim == nim,
        KRS.semester == semester
    ).first()

    if not krs_record:
        raise HTTPException(status_code=404, detail="KRS tidak ditemukan untuk NIM dan semester tersebut")

    print(f"Debug: Found KRS record with ID {krs_record.id}")

    # Get student information to validate status
    student = db.query(CalonMahasiswa).filter(CalonMahasiswa.nim == nim).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Only approved students can have billing generated
    if student.status != StatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="Student not approved")


    # Check if billing already exists for this (nim, semester) combination
    existing_billing = db.query(Billing).filter(
        Billing.nim == nim,
        Billing.semester == semester
    ).first()

    # Return error if billing already exists
    if existing_billing:
        raise HTTPException(status_code=400, detail="Billing already exists for this student and semester")

    # Get program study to determine tuition amount
    program = db.query(ProgramStudi).filter(ProgramStudi.id == student.program_studi_id).first()

    # Determine tuition amount based on program study code
    if program and program.kode == 'TIF':
        tuition_amount = 5_000_000  # 5 million for TIF
    elif program and program.kode == 'SIF':
        tuition_amount = 4_000_000  # 4 million for SIF
    else:
        # Default tuition amount
        tuition_amount = 4_500_000  # Default to 4.5 million

    # Create new billing record
    new_billing = Billing(
        nim=nim,
        semester=semester,
        total_amount=tuition_amount,
        paid_amount=0,
        due_date=date.today() + timedelta(days=14),  # Due in 14 days
        status='unpaid'  # Default status
    )

    db.add(new_billing)
    db.commit()
    db.refresh(new_billing)

    return new_billing


def generate_financial_report(month: int, year: int, db: Session):
    """
    Generate financial report for a specific month and year

    Args:
        month: Month (1-12)
        year: Year (e.g., 2025)
        db: Database session

    Returns:
        Financial report data
    """
    from sqlalchemy import extract, distinct
    from .models import Payment, Billing  # Import Payment and Billing models

    # 1. Calculate Total Revenue: SUM(payment.amount) based on payment.paid_at (month, year)
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        extract('month', Payment.paid_at) == month,
        extract('year', Payment.paid_at) == year
    ).scalar() or 0

    # 2. Calculate Total Students: COUNT(DISTINCT billing.nim) based on billing.created_at (month, year)
    total_students = db.query(distinct(Billing.nim)).filter(
        extract('month', Billing.created_at) == month,
        extract('year', Billing.created_at) == year
    ).count()

    # 3. Calculate Paid Students: Count billing with status = 'paid'
    paid_students = db.query(Billing.nim).filter(
        extract('month', Billing.created_at) == month,
        extract('year', Billing.created_at) == year,
        Billing.status == 'paid'
    ).distinct().count()

    # 4. Calculate Collection Rate: paid_students / total_students
    collection_rate = (paid_students / total_students) if total_students > 0 else 0
    collection_rate = collection_rate * 100  # Convert to percentage

    # 5. Get Top 10 Arrears: billing.status != 'paid', arrears = total_amount - paid_amount
    from sqlalchemy import desc

    top_10_arrears = (
        db.query(Billing)
        .filter(
            Billing.status != 'paid',
            extract('month', Billing.created_at) == month,
            extract('year', Billing.created_at) == year
        )
        .order_by(desc(Billing.total_amount - Billing.paid_amount))
        .limit(10)
        .all()
    )

    top_10_arrears_list = []
    for billing in top_10_arrears:
        outstanding = billing.total_amount - billing.paid_amount
        top_10_arrears_list.append({
            "nim": billing.nim,
            "semester": billing.semester,
            "outstanding": outstanding
        })

    # 6. Generate Recommendation
    # Count billings with status not 'paid' for potential arrears
    arrears_count = db.query(Billing).filter(
        extract('month', Billing.created_at) == month,
        extract('year', Billing.created_at) == year,
        Billing.status != 'paid'
    ).count()

    recommendations = []

    # Check if there are arrears > 2 months (this is a simplified check)
    if arrears_count > 0:
        recommendations.append(f"Kirim reminder ke {arrears_count} mahasiswa dengan tunggakan")

    # Check if collection rate < 70%
    if collection_rate < 70:
        recommendations.append("Rekomendasi follow-up massal untuk meningkatkan collection rate")

    # Set recommendation based on conditions
    if recommendations:
        recommendation = " dan ".join(recommendations)
    else:
        recommendation = "Tidak ada rekomendasi khusus saat ini"

    # Prepare the response
    report = {
        "total_revenue": int(total_revenue),
        "collection_rate": round(collection_rate, 2),
        "paid_students": paid_students,
        "total_students": total_students,
        "top_10_arrears": top_10_arrears_list,
        "recommendation": recommendation
    }

    return report


def get_billing_by_nim(db: Session, nim: str):
    """
    Get billing data for a specific student

    Args:
        db: Database session
        nim: Student NIM

    Returns:
        List of billing records for the student
    """
    from sqlalchemy import asc

    # Get all billing records for the student, ordered by semester
    billing_records = db.query(Billing).filter(
        Billing.nim == nim
    ).order_by(asc(Billing.semester)).all()

    # Format the billing data
    billing_data = []
    for billing in billing_records:
        remaining = billing.total_amount - billing.paid_amount
        billing_data.append({
            "semester": billing.semester,
            "total_amount": billing.total_amount,
            "paid_amount": billing.paid_amount,
            "remaining": remaining,
            "status": billing.status
        })

    return billing_data