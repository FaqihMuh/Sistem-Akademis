"""
Simple test for enum consistency
"""
from krs_system.enums import KRSStatusEnum
from krs_system.state_manager import KRSStatus
from krs_system.models import KRS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from krs_system.krs_logic import get_or_create_krs

def test_enum():
    print("Testing enum consistency...")
    
    # Test that both enums are the same
    print(f"KRSStatusEnum.DRAFT: {KRSStatusEnum.DRAFT}")
    print(f"KRSStatus.DRAFT: {KRSStatus.DRAFT}")
    print(f"Are they the same? {KRSStatusEnum.DRAFT == KRSStatus.DRAFT}")

    # Test that KRS model uses the correct enum
    print(f"KRS.status column type: {KRS.__table__.c.status.type}")

if __name__ == "__main__":
    test_enum()