from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class SubscriptionStatus(str, enum.Enum):
    FREE = "free"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionPlan(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Hashed password for email/password auth
    # OAuth fields removed - no longer using LinkedIn OAuth
    # linkedin_id = Column(String, unique=True, nullable=True, index=True)
    # linkedin_access_token = Column(String, nullable=True)
    # linkedin_refresh_token = Column(String, nullable=True)
    linkedin_cookies = Column(JSON, nullable=True)  # Store browser session cookies for scraping

    # LinkedIn credentials for job search scraping (Phase 3)
    linkedin_scraper_email = Column(String, nullable=True)  # Encrypted
    linkedin_scraper_password = Column(String, nullable=True)  # Encrypted
    linkedin_credentials_consent = Column(DateTime, nullable=True)  # When user consented

    subscription_status = Column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.FREE,
        nullable=False
    )
    subscription_plan = Column(SQLEnum(SubscriptionPlan), nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    resumes_generated_count = Column(String, default="0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("LinkedInProfile", back_populates="user", uselist=False)
    job_postings = relationship("JobPosting", back_populates="user")
    resumes = relationship("Resume", back_populates="user")
