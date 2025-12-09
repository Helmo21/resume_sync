from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from ..core.database import Base


class LinkedInServiceAccount(Base):
    """
    Service accounts used for LinkedIn scraping.

    These accounts are used to:
    - Scrape user LinkedIn profiles (Resume Generation feature)
    - Scrape job postings (Job Search feature)

    Credentials are encrypted before storage.
    Cookie persistence reduces login frequency and avoids security challenges.
    """
    __tablename__ = "linkedin_service_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)  # Encrypted
    password = Column(String, nullable=False)  # Encrypted
    is_premium = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime, nullable=True)
    requests_count_today = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Cookie persistence (NEW)
    cookies = Column(JSONB, nullable=True)  # Stored cookies for session persistence
    cookies_updated_at = Column(DateTime, nullable=True)  # When cookies were last saved
    cookies_expiry = Column(DateTime, nullable=True)  # When cookies expire (14 days from update)
