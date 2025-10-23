from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..models.job import JobPosting
from ..services.apify_scraper import scrape_linkedin_job

router = APIRouter()


class ScrapeJobRequest(BaseModel):
    job_url: HttpUrl


class JobResponse(BaseModel):
    id: str
    linkedin_job_id: Optional[str]
    job_title: Optional[str]
    company_name: Optional[str]
    location: Optional[str]
    description: Optional[str]
    employment_type: Optional[str]
    seniority_level: Optional[str]
    is_remote: bool
    industries: Optional[List[str]]
    parsed_skills: Optional[List[str]]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: Optional[str]
    application_url: Optional[str]
    created_at: str


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


def get_current_user_from_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/scrape", response_model=JobResponse)
async def scrape_job(
    request: ScrapeJobRequest,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Scrape a LinkedIn job posting and save it to the database.

    This endpoint:
    1. Uses Apify to scrape the job posting
    2. Stores the job data in the database
    3. Returns the structured job data
    """

    try:
        # Scrape job using Apify
        print(f"Scraping job from: {request.job_url}")
        job_data = scrape_linkedin_job(str(request.job_url))

        if not job_data:
            raise HTTPException(status_code=400, detail="Failed to scrape job posting")

        # Check if we already have this job for this user
        existing_job = db.query(JobPosting).filter(
            JobPosting.user_id == user.id,
            JobPosting.linkedin_job_id == job_data.get("job_id")
        ).first()

        if existing_job:
            # Update existing job
            existing_job.job_title = job_data.get("title")
            existing_job.company_name = job_data.get("company")
            existing_job.location = job_data.get("location")
            existing_job.description = job_data.get("description")
            existing_job.employment_type = job_data.get("employment_type")
            existing_job.seniority_level = job_data.get("seniority_level")
            existing_job.is_remote = job_data.get("is_remote", False)
            existing_job.industries = job_data.get("industries")
            existing_job.parsed_skills = job_data.get("skills")
            existing_job.salary_min = job_data.get("salary_min")
            existing_job.salary_max = job_data.get("salary_max")
            existing_job.salary_currency = job_data.get("salary_currency")
            existing_job.application_url = job_data.get("application_url")
            existing_job.apify_data = job_data.get("raw_data")
            existing_job.last_scraped_at = datetime.utcnow()

            db.commit()
            db.refresh(existing_job)
            job_posting = existing_job
        else:
            # Create new job posting
            job_posting = JobPosting(
                user_id=user.id,
                url=str(request.job_url),
                linkedin_job_id=job_data.get("job_id"),
                company_name=job_data.get("company"),
                job_title=job_data.get("title"),
                location=job_data.get("location"),
                description=job_data.get("description"),
                employment_type=job_data.get("employment_type"),
                seniority_level=job_data.get("seniority_level"),
                is_remote=job_data.get("is_remote", False),
                industries=job_data.get("industries"),
                parsed_skills=job_data.get("skills"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                salary_currency=job_data.get("salary_currency"),
                application_url=job_data.get("application_url"),
                apify_data=job_data.get("raw_data")
            )
            db.add(job_posting)
            db.commit()
            db.refresh(job_posting)

        return JobResponse(
            id=str(job_posting.id),
            linkedin_job_id=job_posting.linkedin_job_id,
            job_title=job_posting.job_title,
            company_name=job_posting.company_name,
            location=job_posting.location,
            description=job_posting.description,
            employment_type=job_posting.employment_type,
            seniority_level=job_posting.seniority_level,
            is_remote=job_posting.is_remote,
            industries=job_posting.industries,
            parsed_skills=job_posting.parsed_skills,
            salary_min=job_posting.salary_min,
            salary_max=job_posting.salary_max,
            salary_currency=job_posting.salary_currency,
            application_url=job_posting.application_url,
            created_at=job_posting.created_at.isoformat()
        )

    except Exception as e:
        print(f"Error scraping job: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to scrape job: {str(e)}")


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all scraped jobs for current user"""
    jobs = db.query(JobPosting).filter(
        JobPosting.user_id == user.id
    ).order_by(JobPosting.created_at.desc()).all()

    job_list = [
        JobResponse(
            id=str(job.id),
            linkedin_job_id=job.linkedin_job_id,
            job_title=job.job_title,
            company_name=job.company_name,
            location=job.location,
            description=job.description,
            employment_type=job.employment_type,
            seniority_level=job.seniority_level,
            is_remote=job.is_remote,
            industries=job.industries,
            parsed_skills=job.parsed_skills,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            application_url=job.application_url,
            created_at=job.created_at.isoformat()
        )
        for job in jobs
    ]

    return JobListResponse(
        jobs=job_list,
        total=len(job_list)
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get specific job details"""
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.user_id == user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=str(job.id),
        linkedin_job_id=job.linkedin_job_id,
        job_title=job.job_title,
        company_name=job.company_name,
        location=job.location,
        description=job.description,
        employment_type=job.employment_type,
        seniority_level=job.seniority_level,
        is_remote=job.is_remote,
        industries=job.industries,
        parsed_skills=job.parsed_skills,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        application_url=job.application_url,
        created_at=job.created_at.isoformat()
    )
