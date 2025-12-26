"""
Common enums for KRS system
"""
from enum import Enum


class KRSStatusEnum(Enum):
    """
    Enum representing the possible states of a KRS
    """
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REVISION = "REVISION"
    BLOCKED = "BLOCKED"