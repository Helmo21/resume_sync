from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic job information
    url = Column(Text, nullable=False)
    linkedin_job_id = Column(String, nullable=True)  # LinkedIn job ID from URL
    company_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)

    # Additional Apify fields
    employment_type = Column(String, nullable=True)  # Full-time, Part-time, etc.
    seniority_level = Column(String, nullable=True)  # Entry, Mid, Senior, etc.
    is_remote = Column(Boolean, default=False)
    industries = Column(JSONB, nullable=True)  # List of industries

    # Salary information
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String, nullable=True, default='USD')

    # Skills and keywords
    parsed_keywords = Column(JSONB, nullable=True)  # Array of important keywords
    parsed_skills = Column(JSONB, nullable=True)  # Array of required skills

    # Application details
    application_url = Column(Text, nullable=True)

    # Raw data
    raw_html = Column(Text, nullable=True)
    apify_data = Column(JSONB, nullable=True)  # Complete Apify response

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="job_postings")
    resumes = relationship("Resume", back_populates="job_posting")
