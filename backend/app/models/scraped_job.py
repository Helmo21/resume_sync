from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class ScrapedJob(Base):
    """Store jobs scraped from LinkedIn feed for job matching"""
    __tablename__ = "scraped_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_resume_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_resumes.id"), nullable=True)

    # Job details
    linkedin_post_url = Column(Text, nullable=False, unique=True)  # Unique constraint on URL
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    posted_date = Column(String, nullable=True)  # From LinkedIn (e.g., "2 days ago")

    # Job characteristics
    is_remote = Column(Boolean, nullable=True)
    employment_type = Column(String, nullable=True)  # Full-time, Part-time, Contract
    seniority_level = Column(String, nullable=True)

    # Match data (populated by AI matching service)
    match_score = Column(Float, nullable=True)  # 0-100 relevance score
    match_reasoning = Column(Text, nullable=True)  # Legacy text reasoning
    match_details = Column(JSONB, nullable=True)  # Structured match data: {matching_skills, missing_skills, experience_fit, reasoning}

    # Raw data
    raw_html = Column(Text, nullable=True)
    extracted_data = Column(JSONB, nullable=True)  # Any additional scraped data

    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="scraped_jobs")
    uploaded_resume = relationship("UploadedResume", backref="scraped_jobs")
