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
from ..services.linkedin_job_scraper_v2 import LinkedInJobScraperV2
from ..services.service_account_manager import ServiceAccountManager
from ..services.keyword_expander import KeywordExpander
from datetime import timedelta


router = APIRouter()


class SearchJobsRequest(BaseModel):
    """Request to search for jobs"""
    resume_id: str
    location: Optional[str] = None
    remote_only: bool = False
    max_results: int = 100  # Increased from 20 to 100
    date_posted: str = 'week'  # 'day', 'week', 'month', 'any'
    experience_level: Optional[str] = None  # 'entry', 'mid', 'senior', 'director', 'executive'
    job_type: Optional[str] = None  # 'full_time', 'part_time', 'contract', 'temporary'
    sort_by: str = 'date'  # 'date' or 'relevance'


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

    # Get service account credentials with cookie support
    try:
        email, password, account = ServiceAccountManager.get_available_account_with_cookies(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No LinkedIn service accounts available: {str(e)}"
        )

    # Check if cookies are valid (not expired, less than 7 days old)
    cookies_valid = False
    if account.cookies and account.cookies_updated_at:
        cookies_age = datetime.utcnow() - account.cookies_updated_at
        cookies_valid = cookies_age < timedelta(days=7)
        if cookies_valid:
            print(f"🍪 Using saved cookies (age: {cookies_age.days} days)", flush=True)
        else:
            print(f"⚠️  Cookies expired (age: {cookies_age.days} days), will re-login", flush=True)
            account.cookies = None  # Clear expired cookies

    # Generate multiple search queries from different angles
    analysis_data = uploaded_resume.analyzed_data

    print(f"📊 Analyzing resume data...", flush=True)
    print(f"   Job titles: {analysis_data.get('job_titles', [])[:3]}", flush=True)
    print(f"   Technical skills: {analysis_data.get('technical_skills', [])[:5]}", flush=True)
    print(f"   Industries: {analysis_data.get('industries', [])[:3]}", flush=True)
    print(f"   Seniority: {analysis_data.get('seniority_level', 'N/A')}", flush=True)
    sys.stdout.flush()

    # Generate multiple query strategies
    search_queries = KeywordExpander.generate_search_queries(analysis_data)

    if not search_queries:
        raise HTTPException(
            status_code=400,
            detail="Could not generate search queries from resume analysis"
        )

    print(f"\n🔍 Generated {len(search_queries)} search strategies:", flush=True)
    for i, query in enumerate(search_queries, 1):
        print(f"   {i}. {query['description']}", flush=True)
    sys.stdout.flush()

    # Perform LinkedIn scraping with V2 scraper (cookie persistence)
    try:
        import sys
        print(f"\n🚀 Starting LinkedIn job search for user {user.email}", flush=True)
        sys.stdout.flush()

        # Use primary job title from first search query
        primary_query = search_queries[0] if search_queries else {"keywords": []}
        job_title = KeywordExpander.format_query_for_linkedin(
            primary_query['keywords'],
            max_keywords=3
        ) if primary_query['keywords'] else "Software Engineer"

        print(f"🔍 Searching for: {job_title}", flush=True)
        print(f"📍 Location: {request.location or 'Any'}", flush=True)
        sys.stdout.flush()

        # Initialize V2 scraper with cookie support
        scraper = LinkedInJobScraperV2(headless=True, max_jobs=request.max_results)

        # Run async scrape
        jobs_data, scraper_mode, new_cookies = await scraper.scrape_jobs(
            email=email,
            password=password,
            job_title=job_title,
            location=request.location or "",
            cookies=account.cookies  # Use existing cookies if available
        )

        print(f"\n✅ Scraping complete! Found {len(jobs_data)} jobs using {scraper_mode.value}", flush=True)
        sys.stdout.flush()

        # Save cookies back to account
        if new_cookies:
            account.cookies = new_cookies
            account.cookies_updated_at = datetime.utcnow()
            account.cookies_expiry = datetime.utcnow() + timedelta(days=7)
            db.commit()
            print(f"🍪 Saved session cookies (expires in 7 days)", flush=True)
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
