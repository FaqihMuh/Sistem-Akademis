"""
Schedule System Router - extracted to integrate with combined system
"""
from fastapi import APIRouter
from schedule_system import endpoints

# Create a router for Schedule endpoints (endpoints already has the /api/schedule prefix)
router = endpoints.router