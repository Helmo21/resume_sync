from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class LinkedInProfile(Base):
    __tablename__ = "linkedin_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Structured data
    raw_data = Column(JSONB, nullable=False)  # Full LinkedIn response
    profile_url = Column(String, nullable=True)  # LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
    apify_data = Column(JSONB, nullable=True)  # Complete profile data from Apify scraper
    headline = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    experiences = Column(JSONB, nullable=True)  # Array of work experiences
    education = Column(JSONB, nullable=True)  # Array of education
    skills = Column(JSONB, nullable=True)  # Array of skills
    certifications = Column(JSONB, nullable=True)

    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
