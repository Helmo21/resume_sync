from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class UploadedResume(Base):
    """Store user-uploaded resumes for job search matching"""
    __tablename__ = "uploaded_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # File metadata
    filename = Column(String, nullable=False)
    file_path = Column(Text, nullable=True)  # Optional: store file path if we keep originals

    # Parsed content
    parsed_text = Column(Text, nullable=False)  # Raw text extracted from PDF/DOCX

    # AI-analyzed metadata (populated after analysis)
    analyzed_data = Column(JSONB, nullable=True)  # Skills, experience, preferences, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="uploaded_resumes")
