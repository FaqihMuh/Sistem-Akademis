"""
Main entry point for the combined academic system (PMB + KRS)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from krs_system.endpoints import router as krs_router  # Import KRS router
from pmb_system.router import router as pmb_router  # Import PMB router from new file


# Create the main FastAPI app
app = FastAPI(
    title="Sistem Akademik API (PMB + KRS)",
    description="API untuk sistem akademik terintegrasi PMB dan KRS",
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

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Sistem Akademis API (PMB + KRS) is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)