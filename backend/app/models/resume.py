from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=True)

    template_id = Column(String, nullable=False)  # e.g., "modern", "classic", "technical"
    generated_content = Column(JSONB, nullable=False)  # Structured resume data
    pdf_url = Column(Text, nullable=True)  # S3 URL
    docx_url = Column(Text, nullable=True)  # S3 URL for DOCX
    ats_score = Column(Integer, nullable=True)
    openai_prompt = Column(Text, nullable=True)  # For debugging
    openai_response = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resumes")
    job_posting = relationship("JobPosting", back_populates="resumes")
