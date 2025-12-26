"""
Main entry point for the combined academic system (PMB + KRS + Schedule + Grades)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from krs_system.endpoints import router as krs_router  # Import KRS router
from pmb_system.router import router as pmb_router  # Import PMB router from new file
from schedule_system.router import router as schedule_router  # Import Schedule router

# Import models to ensure they're registered with Base for Alembic
from pmb_system import models as pmb_models
from krs_system import models as krs_models
from schedule_system import models as schedule_models
from auth_system import models as auth_models
from grades_system import models as grades_models  # Import grades models
from payment_system import models as payment_models  # Import payment models
from payment_system.scheduler import start_scheduler, stop_scheduler
from apscheduler.schedulers.background import BackgroundScheduler



# Global scheduler variable
scheduler = None


# Create the main FastAPI app
app = FastAPI(
    title="Sistem Akademik API (PMB + KRS + Schedule + Grades)",
    description="API untuk sistem akademik terintegrasi PMB, KRS, Jadwal Kelas, dan Nilai",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include PMB router
app.include_router(pmb_router, prefix="/api/pmb", tags=["PMB"])

# Include KRS router
app.include_router(krs_router, prefix="/api/krs", tags=["KRS"])

# Include Schedule router
app.include_router(schedule_router, prefix="/api/schedule", tags=["Schedule"])

# Include Grades router
from grades_system.router import router as grades_router
app.include_router(grades_router)  # Using default prefix /api/grades from router

# Include GPA router
from grades_system.router_gpa import router as gpa_router
app.include_router(gpa_router)  # Using default prefix /api/gpa from router

# Include authentication router
from auth_system.routes import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Include payment router
from payment_system.router import router as payment_router
app.include_router(payment_router, prefix="/api/payment", tags=["Payment"])

# Include admin API router
from admin_api import router as admin_api_router
app.include_router(admin_api_router, prefix="/api")  # Add /api prefix so endpoints become /api/admin/*


# Mount the web dashboard app
from web_dashboard.app import dashboard_app
app.mount("/dashboard", dashboard_app)

# Event handlers for scheduler
@app.on_event("startup")
def startup_event():
    global scheduler
    print("Starting scheduler...")
    scheduler = start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    global scheduler
    if scheduler:
        print("Stopping scheduler...")
        stop_scheduler(scheduler)


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Sistem Akademis API (PMB + KRS + Schedule + Grades) is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)