"""
API endpoints for LinkedIn job search (Phase 4)
"""
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..models.uploaded_resume import UploadedResume
from ..models.scraped_job import ScrapedJob
from ..services.linkedin_job_scraper import LinkedInJobScraper
from ..services.service_account_manager import ServiceAccountManager


router = APIRouter()


class SearchJobsRequest(BaseModel):
    """Request to search for jobs"""
    resume_id: str
    location: Optional[str] = None
    remote_only: bool = False
    max_results: int = 20


class ScrapedJobResponse(BaseModel):
    """Response model for scraped job"""
    id: str
    job_title: Optional[str]
    company_name: Optional[str]
    location: Optional[str]
    description: Optional[str]
    posted_date: Optional[str]
    is_remote: Optional[bool]
    linkedin_post_url: str
    match_score: Optional[float]
    scraped_at: datetime

    class Config:
        from_attributes = True


@router.post("/search")
async def search_linkedin_jobs(
    request: SearchJobsRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Search LinkedIn for jobs matching the uploaded resume.

    This endpoint:
    1. Gets the resume analysis data
    2. Retrieves stored LinkedIn credentials
    3. Logs into LinkedIn with Selenium
    4. Searches for jobs using extracted keywords
    5. Scrapes and stores job details
    6. Returns found jobs

    WARNING: This process takes 1-3 minutes. Consider running in background.
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get uploaded resume
    try:
        resume_uuid = uuid.UUID(request.resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    uploaded_resume = db.query(UploadedResume)\
        .filter(UploadedResume.id == resume_uuid, UploadedResume.user_id == user.id)\
        .first()

    if not uploaded_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Check if resume has been analyzed
    if not uploaded_resume.analyzed_data:
        raise HTTPException(
            status_code=400,
            detail="Resume has not been analyzed yet. Please analyze it first."
        )

    # Get service account credentials
    try:
        email, password = ServiceAccountManager.get_available_account(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No LinkedIn service accounts available: {str(e)}"
        )

    # Extract search keywords from analysis
    analysis_data = uploaded_resume.analyzed_data
    search_keywords = analysis_data.get('search_keywords', [])[:10]  # Top 10 keywords

    if not search_keywords:
        # Fallback to job titles if no keywords
        search_keywords = analysis_data.get('job_titles', [])[:5]

    if not search_keywords:
        raise HTTPException(
            status_code=400,
            detail="No search keywords found in resume analysis"
        )

    # Perform LinkedIn scraping
    try:
        import sys
        print(f"🚀 Starting LinkedIn job search for user {user.email}", flush=True)
        print(f"   Keywords: {search_keywords}", flush=True)
        sys.stdout.flush()

        with LinkedInJobScraper(headless=True) as scraper:
            # Login to LinkedIn
            print("🔐 Logging in to LinkedIn...", flush=True)
            sys.stdout.flush()

            login_success = scraper.login(email, password)
            if not login_success:
                raise Exception("LinkedIn login failed")

            print("✅ Login successful!", flush=True)
            sys.stdout.flush()

            # Search for jobs
            print(f"🔍 Searching for jobs...", flush=True)
            sys.stdout.flush()

            jobs_data = scraper.search_jobs(
                keywords=search_keywords,
                location=request.location,
                remote_only=request.remote_only,
                max_results=request.max_results
            )

            print(f"✅ Found {len(jobs_data)} jobs", flush=True)
            sys.stdout.flush()

            # Save jobs to database
            saved_jobs = []
            for job_data in jobs_data:
                # Check if job already exists (by URL)
                existing_job = db.query(ScrapedJob)\
                    .filter(ScrapedJob.linkedin_post_url == job_data['linkedin_post_url'])\
                    .first()

                if existing_job:
                    print(f"   ⏭️  Skipping duplicate: {job_data['job_title']}")
                    saved_jobs.append(existing_job)
                    continue

                # Create new scraped job
                scraped_job = ScrapedJob(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    uploaded_resume_id=uploaded_resume.id,
                    **job_data
                )

                db.add(scraped_job)
                saved_jobs.append(scraped_job)

            db.commit()

            # Refresh all jobs to get IDs
            for job in saved_jobs:
                db.refresh(job)

            print(f"💾 Saved {len(saved_jobs)} jobs to database")

            return {
                "message": f"Successfully scraped {len(jobs_data)} jobs",
                "jobs_found": len(jobs_data),
                "jobs_saved": len(saved_jobs),
                "jobs": [
                    ScrapedJobResponse(
                        id=str(job.id),
                        job_title=job.job_title,
                        company_name=job.company_name,
                        location=job.location,
                        description=job.description[:500] if job.description else None,  # Truncate for response
                        posted_date=job.posted_date,
                        is_remote=job.is_remote,
                        linkedin_post_url=job.linkedin_post_url,
                        match_score=job.match_score,
                        scraped_at=job.scraped_at
                    )
                    for job in saved_jobs
                ]
            }

    except Exception as e:
        import sys
        import traceback
        error_msg = f"❌ Job search failed: {str(e)}"
        print(error_msg, flush=True)
        print(f"   Traceback: {traceback.format_exc()}", flush=True)
        sys.stdout.flush()

        raise HTTPException(
            status_code=500,
            detail=f"Job search failed: {str(e)}"
        )


@router.get("/resume/{resume_id}/jobs", response_model=List[ScrapedJobResponse])
async def get_scraped_jobs_for_resume(
    resume_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get all scraped jobs for a specific resume.
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get uploaded resume
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    # Get all scraped jobs for this resume
    scraped_jobs = db.query(ScrapedJob)\
        .filter(
            ScrapedJob.uploaded_resume_id == resume_uuid,
            ScrapedJob.user_id == user.id
        )\
        .order_by(ScrapedJob.scraped_at.desc())\
        .all()

    return [
        ScrapedJobResponse(
            id=str(job.id),
            job_title=job.job_title,
            company_name=job.company_name,
            location=job.location,
            description=job.description[:500] if job.description else None,
            posted_date=job.posted_date,
            is_remote=job.is_remote,
            linkedin_post_url=job.linkedin_post_url,
            match_score=job.match_score,
            scraped_at=job.scraped_at
        )
        for job in scraped_jobs
    ]
