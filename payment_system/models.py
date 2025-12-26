from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import date
from pmb_system.database import Base, engine  # Using absolute import as required
import enum


class BillingStatus(str, enum.Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class Billing(Base):
    __tablename__ = "billing"

    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String, nullable=False)  # FK reference to calon_mahasiswa.nim (managed at DB level)
    semester = Column(String, nullable=False)
    total_amount = Column(Integer, nullable=False)
    paid_amount = Column(Integer, default=0)
    due_date = Column(Date, nullable=False)
    status = Column(SQLEnum(BillingStatus), default=BillingStatus.unpaid, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to the existing calon_mahasiswa table would be defined in the original model
    # Since this is a cross-module reference, we'll handle this in business logic


class PaymentMethod(Base):
    __tablename__ = "payment_method"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Examples: CASH, TRANSFER, GATEWAY_SIM


class Payment(Base):
    __tablename__ = "payment"

    id = Column(Integer, primary_key=True, index=True)
    billing_id = Column(Integer, ForeignKey("billing.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    method_id = Column(Integer, ForeignKey("payment_method.id"), nullable=False)
    transaction_ref = Column(String, nullable=False)
    paid_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    billing = relationship("Billing", back_populates="payments")
    method = relationship("PaymentMethod")


# Define relationships after all models are defined
Billing.payments = relationship("Payment", back_populates="billing")


def create_payment_tables():
    """Function to create payment system tables in the database."""
    Base.metadata.create_all(bind=engine)