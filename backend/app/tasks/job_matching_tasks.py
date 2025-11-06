"""
Celery Tasks for Job Scraping and Matching

Risk Mitigation:
- AI matching too slow → Run as background task, user gets updates via polling
- LinkedIn blocks → Service account rotation, automatic retries
- High load → Queue management, task prioritization
"""
import asyncio
import uuid
from typing import Dict, List
from datetime import datetime
from celery import Task

from ..celery_app import celery_app
from ..services.linkedin_job_scraper_v2 import LinkedInJobScraperV2, ScraperMode
from ..services.job_matcher import JobMatcher
from ..services.service_account_manager import ServiceAccountManager
from ..models.scraped_job import ScrapedJob
from ..models.uploaded_resume import UploadedResume
from ..models.user import User
from ..core.database import SessionLocal


class DatabaseTask(Task):
    """
    Base task with database session management
    """
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name='app.tasks.job_matching_tasks.scrape_and_match_jobs',
    max_retries=2,
    default_retry_delay=60  # Retry after 60 seconds
)
def scrape_and_match_jobs(
    self,
    user_id: str,
    resume_id: str,
    job_title: str,
    location: str,
    max_results: int = 20
) -> Dict:
    """
    Background task: Scrape LinkedIn jobs and match against profile

    This task:
    1. Gets available LinkedIn service account
    2. Scrapes jobs using LinkedInJobScraperV2 (Camoufox + Selenium fallback)
    3. Matches each job against user profile using AI
    4. Saves results to database
    5. Returns summary

    Returns:
        {
            "status": "success",
            "jobs_found": 15,
            "jobs_saved": 15,
            "scraper_mode": "camoufox",
            "top_match_score": 95,
            "job_ids": [...]
        }
    """
    print(f"🚀 Starting job search task for user {user_id}")

    try:
        # Get user and resume from database
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise Exception("User not found")

        resume = self.db.query(UploadedResume).filter(
            UploadedResume.id == uuid.UUID(resume_id),
            UploadedResume.user_id == user.id
        ).first()

        if not resume:
            raise Exception("Resume not found")

        if not resume.analyzed_data:
            raise Exception("Resume not analyzed yet")

        # Get LinkedIn service account
        print("🔐 Getting service account...")
        try:
            email, password = ServiceAccountManager.get_available_account(self.db)
            print(f"✅ Got service account: {email}")
        except Exception as e:
            raise Exception(f"No service accounts available: {str(e)}")

        # Extract profile data for matching
        profile_data = {
            'skills': resume.analyzed_data.get('skills', []),
            'experiences': resume.analyzed_data.get('experience', []),
            'summary': resume.analyzed_data.get('summary', ''),
        }

        # Step 1: Scrape jobs with dual-mode scraper
        print(f"🕷️  Scraping jobs: '{job_title}' in '{location}'")
        scraper = LinkedInJobScraperV2(headless=True, max_jobs=max_results)

        # Run async scrape in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            jobs_data, scraper_mode = loop.run_until_complete(
                scraper.scrape_jobs(email, password, job_title, location)
            )
        finally:
            loop.close()

        print(f"✅ Scraped {len(jobs_data)} jobs using {scraper_mode.value}")

        if not jobs_data:
            return {
                "status": "success",
                "jobs_found": 0,
                "jobs_saved": 0,
                "scraper_mode": scraper_mode.value,
                "message": "No jobs found for this search"
            }

        # Step 2: Match jobs against profile with AI
        print("🤖 Starting AI matching...")
        matcher = JobMatcher()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            matched_jobs = loop.run_until_complete(
                matcher.match_multiple_jobs(profile_data, jobs_data)
            )
        finally:
            loop.close()

        print(f"✅ Matching complete! Top score: {matched_jobs[0]['match_score'] if matched_jobs else 0}")

        # Step 3: Save to database
        print("💾 Saving to database...")
        saved_job_ids = []

        for job_data in matched_jobs:
            # Check if already exists
            existing = self.db.query(ScrapedJob).filter(
                ScrapedJob.linkedin_post_url == job_data['linkedin_post_url']
            ).first()

            if existing:
                print(f"  ⏭️  Skipping duplicate: {job_data['job_title'][:50]}")
                saved_job_ids.append(str(existing.id))
                continue

            # Create new job record
            scraped_job = ScrapedJob(
                id=uuid.uuid4(),
                user_id=user.id,
                uploaded_resume_id=resume.id,
                linkedin_post_url=job_data['linkedin_post_url'],
                job_title=job_data.get('job_title'),
                company_name=job_data.get('company_name'),
                location=job_data.get('location'),
                description=job_data.get('description'),
                posted_date=job_data.get('posted_date'),
                is_remote=job_data.get('is_remote', False),
                match_score=job_data.get('match_score'),
                match_details=job_data.get('match_details'),  # JSON field
                scraped_at=datetime.utcnow()
            )

            self.db.add(scraped_job)
            saved_job_ids.append(str(scraped_job.id))

        self.db.commit()
        print(f"✅ Saved {len(saved_job_ids)} jobs")

        # Return summary
        return {
            "status": "success",
            "jobs_found": len(jobs_data),
            "jobs_saved": len(saved_job_ids),
            "scraper_mode": scraper_mode.value,
            "top_match_score": matched_jobs[0]['match_score'] if matched_jobs else 0,
            "job_ids": saved_job_ids,
            "cache_stats": matcher.get_cache_stats()
        }

    except Exception as e:
        print(f"❌ Task failed: {str(e)}")

        # Retry with exponential backoff for certain errors
        if "service account" in str(e).lower() or "login failed" in str(e).lower():
            # These errors might be temporary, retry
            raise self.retry(exc=e, countdown=60)

        # For other errors, return failure
        return {
            "status": "failed",
            "error": str(e),
            "jobs_found": 0,
            "jobs_saved": 0
        }


@celery_app.task(
    name='app.tasks.job_matching_tasks.match_single_job',
    max_retries=1
)
def match_single_job(profile_data: Dict, job_data: Dict) -> Dict:
    """
    Task to match a single job (for testing or re-matching)
    """
    matcher = JobMatcher()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            matcher.match_job_to_profile(profile_data, job_data)
        )
        return result
    finally:
        loop.close()


@celery_app.task(name='app.tasks.job_matching_tasks.get_task_status')
def get_task_status(task_id: str) -> Dict:
    """
    Get status of a background task
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": result.state,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None
    }
