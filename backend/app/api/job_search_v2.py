"""
Enhanced Job Search API with Background Tasks and AI Matching

New Features:
- Background task processing (non-blocking)
- AI-powered job matching
- Match scoring (0-100)
- Cached results for cost optimization
- Service account rotation with rate limiting
"""
from fastapi import APIRouter, Depends, HTTPException, Header
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
from ..tasks.job_matching_tasks import scrape_and_match_jobs
from ..services.service_account_manager import ServiceAccountManager
from celery.result import AsyncResult
from ..celery_app import celery_app


router = APIRouter()


class SearchJobsRequest(BaseModel):
    """Request to search for jobs"""
    resume_id: str
    job_title: Optional[str] = None  # Auto-extract from resume if not provided
    location: Optional[str] = "Remote"
    max_results: int = 50  # Default 50 jobs (balance between quantity and speed)


class JobMatchResponse(BaseModel):
    """Response model for a matched job"""
    id: str
    job_title: Optional[str]
    company_name: Optional[str]
    location: Optional[str]
    description: Optional[str]
    posted_date: Optional[str]
    is_remote: Optional[bool]
    linkedin_post_url: str
    match_score: Optional[float]
    match_details: Optional[dict]
    scraped_at: datetime

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """Response for task status"""
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    progress: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/search")
async def start_job_search(
    request: SearchJobsRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Start a background job search task with AI matching.

    This endpoint:
    1. Validates user and resume
    2. Starts a Celery background task
    3. Returns task ID for status polling

    The background task will:
    - Scrape LinkedIn jobs (Camoufox + Selenium fallback)
    - Match each job against profile using AI
    - Save results with match scores
    - Cache results for cost optimization

    Returns:
        {
            "task_id": "uuid",
            "status": "started",
            "message": "Job search started in background"
        }
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

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

    # Auto-extract job title from resume if not provided
    job_title = request.job_title
    if not job_title:
        # Try to get current position from resume
        analysis_data = uploaded_resume.analyzed_data
        job_titles = analysis_data.get('job_titles', [])
        if job_titles:
            job_title = job_titles[0]  # Use most recent/relevant title
        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide a job title or ensure your resume has been properly analyzed"
            )

    # Check service account availability
    try:
        account_stats = ServiceAccountManager.get_account_stats(db)
        if account_stats['available'] == 0:
            raise HTTPException(
                status_code=503,
                detail=f"No service accounts available. {account_stats['rate_limited']} rate-limited, {account_stats['in_cooldown']} in cooldown."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Service account check failed: {str(e)}"
        )

    # Start background task
    task = scrape_and_match_jobs.delay(
        user_id=str(user.id),
        resume_id=str(uploaded_resume.id),
        job_title=job_title,
        location=request.location,
        max_results=request.max_results
    )

    print(f"🚀 Started background task {task.id} for user {user.email}")

    return {
        "task_id": task.id,
        "status": "started",
        "message": f"Job search started for '{job_title}' in '{request.location}'. Poll /api/jobs/search/status/{task.id} for updates.",
        "estimated_time_seconds": 120  # Rough estimate: 2 minutes
    }


@router.get("/search/status/{task_id}", response_model=TaskStatusResponse)
async def get_search_status(
    task_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get status of a background job search task.

    Returns:
        {
            "task_id": "uuid",
            "status": "SUCCESS|PENDING|STARTED|FAILURE",
            "result": {...} (if completed),
            "error": "..." (if failed)
        }
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get task result
    result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": result.state,
        "progress": None,
        "result": None,
        "error": None
    }

    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result) if result.result else "Task failed"
            response["status"] = "FAILURE"

    return response


@router.get("/resume/{resume_id}/jobs", response_model=List[JobMatchResponse])
async def get_scraped_jobs_for_resume(
    resume_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
    min_score: Optional[int] = 0,  # Filter by minimum match score
    limit: Optional[int] = 50
):
    """
    Get all scraped and matched jobs for a specific resume.

    Query Parameters:
        min_score: Minimum match score (0-100)
        limit: Maximum number of jobs to return

    Jobs are returned sorted by match score (descending).
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

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
    query = db.query(ScrapedJob).filter(
        ScrapedJob.uploaded_resume_id == resume_uuid,
        ScrapedJob.user_id == user.id
    )

    # Filter by minimum score if specified
    if min_score > 0:
        query = query.filter(ScrapedJob.match_score >= min_score)

    # Order by match score descending
    scraped_jobs = query.order_by(
        ScrapedJob.match_score.desc().nullslast(),
        ScrapedJob.scraped_at.desc()
    ).limit(limit).all()

    return [
        JobMatchResponse(
            id=str(job.id),
            job_title=job.job_title,
            company_name=job.company_name,
            location=job.location,
            description=job.description[:1000] if job.description else None,  # Truncate for response
            posted_date=job.posted_date,
            is_remote=job.is_remote,
            linkedin_post_url=job.linkedin_post_url,
            match_score=job.match_score,
            match_details=job.match_details,
            scraped_at=job.scraped_at
        )
        for job in scraped_jobs
    ]


@router.get("/service-accounts/stats")
async def get_service_account_stats(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get service account usage statistics (admin/debugging).

    Returns:
        {
            "total_active": 3,
            "available": 2,
            "rate_limited": 1,
            "in_cooldown": 0,
            "daily_limit_per_account": 100,
            "cooldown_minutes": 30
        }
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    stats = ServiceAccountManager.get_account_stats(db)

    return stats
