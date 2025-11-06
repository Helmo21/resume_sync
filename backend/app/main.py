from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .api import auth, resumes, profile, jobs, uploaded_resumes, job_search, job_search_v2
from .core.database import SessionLocal
from .core.service_account_loader import load_service_accounts_from_env, verify_service_accounts
import os

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0"
)


# Startup Event: Auto-load LinkedIn service accounts from .env
@app.on_event("startup")
async def startup_event():
    """
    Run on application startup:
    1. Load LinkedIn service accounts from .env
    2. Verify accounts are available
    """
    print("\n" + "="*60)
    print("🚀 ResumeSync Backend - Starting Up")
    print("="*60 + "\n")

    # Load service accounts from environment variables
    db = SessionLocal()
    try:
        print("📧 Loading LinkedIn service accounts from .env...")
        results = load_service_accounts_from_env(db)

        # Verify accounts
        verify_service_accounts(db)

    except Exception as e:
        print(f"❌ Error loading service accounts: {str(e)}")
    finally:
        db.close()

    print("\n" + "="*60)
    print("✅ ResumeSync Backend - Ready")
    print("="*60 + "\n")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create resumes directory if it doesn't exist
os.makedirs("/app/resumes", exist_ok=True)

# Mount static files for PDF downloads
app.mount("/resumes", StaticFiles(directory="/app/resumes"), name="resumes")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(uploaded_resumes.router, prefix="/api/uploaded-resumes", tags=["Uploaded Resumes"])
app.include_router(job_search.router, prefix="/api/job-search", tags=["Job Search (Legacy)"])
app.include_router(job_search_v2.router, prefix="/api/jobs", tags=["Job Search V2"])


@app.get("/")
async def root():
    return {
        "message": "ResumeSync API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
