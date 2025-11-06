"""
Celery Application Configuration
Handles background tasks for job scraping and AI matching
"""
from celery import Celery
from .core.config import settings
import os

# Initialize Celery with Redis as broker and backend
celery_app = Celery(
    "resumesync",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=['app.tasks.job_matching_tasks']  # Import task modules
)

# Celery Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
    worker_prefetch_multiplier=1,  # One task at a time for long-running jobs
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (memory management)
    result_expires=3600,  # Results expire after 1 hour

    # Task routing - DISABLED: All tasks use default 'celery' queue
    # task_routes={
    #     'app.tasks.job_matching_tasks.scrape_and_match_jobs': {'queue': 'job_matching'},
    #     'app.tasks.job_matching_tasks.match_single_job': {'queue': 'matching'},
    # },

    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Health check task
@celery_app.task
def ping():
    """Simple health check task"""
    return "pong"
