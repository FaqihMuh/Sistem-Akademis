from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pmb_system.database import get_db  # Using get_db from pmb_system.database as required
from .services import process_payment
from typing import Optional
from pydantic import BaseModel


router = APIRouter(tags=["Payment"]) # Using tags for Swagger UI

# Request body schemas
class ManualPaymentRequest(BaseModel):
    billing_id: int
    amount: int
    method_id: int
    transaction_ref: str


class WebhookPaymentRequest(BaseModel):
    signature: str
    billing_id: int
    amount: int
    method_id: int
    transaction_ref: str
    status: str


# Request/Response schemas
class PaymentResponse(BaseModel):
    message: str
    billing_status: str


class GenerateBillingRequest(BaseModel):
    nim: str
    semester: str


class GenerateBillingResponse(BaseModel):
    message: str
    billing_id: int


class FinancialReportRequest(BaseModel):
    month: int
    year: int


class TopArrear(BaseModel):
    nim: str
    semester: str
    outstanding: int


class FinancialReportResponse(BaseModel):
    total_revenue: int
    collection_rate: float
    paid_students: int
    total_students: int
    top_10_arrears: list[TopArrear]
    recommendation: str


class BillingInfo(BaseModel):
    semester: str
    total_amount: int
    paid_amount: int
    remaining: int
    status: str


class StudentBillingResponse(BaseModel):
    billing_data: list[BillingInfo]


# Test endpoint to ensure the payment module appears in Swagger UI
@router.get("/")
def get_payment_info():
    """
    Get information about the payment system
    """
    return {"message": "Payment system is running", "status": "active"}


# Endpoint: Manual Payment
@router.post("/pay", response_model=PaymentResponse)
def manual_payment(
    request: ManualPaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Process a manual payment
    """
    try:
        # Process the payment using the service function
        updated_billing = process_payment(
            db=db,
            billing_id=request.billing_id,
            amount=request.amount,
            method_id=request.method_id,
            transaction_ref=request.transaction_ref
        )

        return PaymentResponse(
            message="Payment processed",
            billing_status=updated_billing.status
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for billing not found)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")


# Endpoint: Payment Webhook (Simulation)
@router.post("/webhook")
def payment_webhook(
    request: WebhookPaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Handle payment webhook notifications
    """
    # Verify signature
    # if request.signature != "valid-signature":
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    # Only process if status is SUCCESS
    if request.status != "SUCCESS":
        return {"message": "Payment status not SUCCESS, ignoring"}

    try:
        # Process the payment using the service function
        updated_billing = process_payment(
            db=db,
            billing_id=request.billing_id,
            amount=request.amount,
            method_id=request.method_id,
            transaction_ref=request.transaction_ref
        )

        return {"message": "Webhook processed successfully", "billing_status": updated_billing.status}
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for billing not found)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# Endpoint: Generate Billing for Student
@router.post("/billing/generate", response_model=GenerateBillingResponse)
def generate_billing(
    request: GenerateBillingRequest,
    db: Session = Depends(get_db)
):
    """
    Generate billing for a specific student and semester
    """
    from .services import generate_billing_for_student

    try:
        # Generate billing for the student
        created_billing = generate_billing_for_student(
            db=db,
            nim=request.nim,
            semester=request.semester
        )

        return GenerateBillingResponse(
            message="Billing generated",
            billing_id=created_billing.id
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for no records found)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Billing generation failed: {str(e)}")


# Endpoint to get student billing data
@router.get("/billing/student", response_model=StudentBillingResponse)
def get_student_billing(
    nim: str,
    db: Session = Depends(get_db)
):
    """
    Get billing information for a specific student
    """
    from .services import get_billing_by_nim

    try:
        # Get billing data for the student
        billing_data = get_billing_by_nim(
            db=db,
            nim=nim
        )

        return StudentBillingResponse(billing_data=billing_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving billing data: {str(e)}")


# Endpoint: Financial Report
@router.post("/report", response_model=FinancialReportResponse)
def get_financial_report(
    request: FinancialReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate financial report for a specific month and year
    """
    from .services import generate_financial_report

    try:
        # Validate month and year
        if not (1 <= request.month <= 12):
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

        if request.year < 2000 or request.year > 2100:  # Reasonable year range
            raise HTTPException(status_code=400, detail="Invalid year")

        # Generate the report
        report = generate_financial_report(
            month=request.month,
            year=request.year,
            db=db
        )

        return FinancialReportResponse(**report)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")