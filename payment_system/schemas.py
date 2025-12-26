from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from enum import Enum


class BillingStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


# Billing Schemas
class BillingBase(BaseModel):
    nim: str
    semester: str
    total_amount: int
    paid_amount: int = 0
    due_date: date
    status: BillingStatus = BillingStatus.unpaid


class BillingCreate(BillingBase):
    pass


class BillingUpdate(BaseModel):
    paid_amount: Optional[int] = None
    status: Optional[BillingStatus] = None


class Billing(BillingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Payment Method Schemas
class PaymentMethodBase(BaseModel):
    name: str


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethod(PaymentMethodBase):
    id: int

    class Config:
        from_attributes = True


# Payment Schemas
class PaymentBase(BaseModel):
    billing_id: int
    amount: int
    method_id: int
    transaction_ref: str


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    id: int
    paid_at: datetime

    class Config:
        from_attributes = True


# Response schemas with relationships
class BillingWithPayments(Billing):
    payments: list[Payment] = []


class PaymentWithDetails(Payment):
    billing: Billing
    method: PaymentMethod