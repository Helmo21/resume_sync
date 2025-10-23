"""
Pytest configuration and shared fixtures for ResumeSync tests.

This file contains:
- Database setup (in-memory SQLite for tests)
- FastAPI test client
- Mock data fixtures
- Common test utilities
"""

import pytest
import os
import json
from typing import Generator, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient
import jose.jwt as jwt

# Import app components
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.profile import LinkedInProfile
from app.models.job import JobPosting
from app.models.resume import Resume


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a test PostgreSQL database for testing.

    Uses the same database as production but with a test schema.
    Each test gets a fresh database that's cleaned up after the test.
    """
    # Use PostgreSQL test database (same as production, supports UUID)
    SQLALCHEMY_TEST_DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://resumesync_user:resumesync_password@db:5432/resumesync_db"
    )

    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()  # Rollback any uncommitted changes
        db.close()
        # Clean up: Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# USER & AUTH FIXTURES
# ============================================================================

@pytest.fixture
def db_session(test_db: Session) -> Session:
    """Alias for test_db for consistency."""
    return test_db


@pytest.fixture
async def test_client(test_db: Session):
    """Create an async test client."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        linkedin_id="test-linkedin-id"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Add access token for testing
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    user.access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return user


@pytest.fixture
def test_jwt_token(test_user: User) -> str:
    """Create a valid JWT token for test user."""
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


@pytest.fixture
def auth_headers(test_jwt_token: str) -> Dict[str, str]:
    """Create authorization headers with JWT token."""
    return {"Authorization": f"Bearer {test_jwt_token}"}


@pytest.fixture
def sample_profile(test_db: Session, test_user: User) -> LinkedInProfile:
    """Create a sample LinkedIn profile for testing."""
    profile = LinkedInProfile(
        user_id=test_user.id,
        profile_url="https://linkedin.com/in/johndoe",
        headline="Senior Software Engineer",
        summary="Software engineer with 5 years of experience",
        raw_data={
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "location": "San Francisco, CA"
        },
        experiences=[
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "start_date": "2020-01-01",
                "is_current": True
            }
        ],
        education=[
            {
                "degree": "BS Computer Science",
                "institution": "University of California",
                "location": "Berkeley, CA"
            }
        ],
        skills=["Python", "JavaScript", "React", "Docker", "AWS"]
    )
    test_db.add(profile)
    test_db.commit()
    test_db.refresh(profile)
    return profile


@pytest.fixture
def sample_job(test_db: Session, test_user: User) -> JobPosting:
    """Create a sample job for testing."""
    job = JobPosting(
        user_id=test_user.id,
        job_title="Senior Python Developer",
        company_name="Tech Company",
        location="Remote",
        url="https://example.com/job/123",
        description="We are looking for a senior Python developer...",
        requirements="5+ years Python, FastAPI, PostgreSQL"
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


@pytest.fixture
def sample_resume(test_db: Session, test_user: User) -> Resume:
    """Create a sample resume for testing."""
    resume = Resume(
        user_id=test_user.id,
        template_id="modern",
        generated_content={
            "personal_info": {
                "full_name": "John Doe",
                "job_title": "Software Engineer"
            },
            "professional_summary": "Experienced developer",
            "match_score": 85.0
        },
        pdf_url="/resumes/test_resume.pdf",
        ats_score=85
    )
    test_db.add(resume)
    test_db.commit()
    test_db.refresh(resume)
    return resume


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_profile_data() -> Dict[str, Any]:
    """Mock LinkedIn profile data."""
    return {
        "full_name": "Antoine Pedretti",
        "email": "antoine@example.com",
        "phone": "+33 6 12 34 56 78",
        "location": "Paris, France",
        "profile_url": "https://linkedin.com/in/antoinepedretti",
        "headline": "DevOps Engineer",
        "summary": "Experienced DevOps Engineer with expertise in cloud infrastructure, CI/CD, and automation. Scaled systems from 0 to 100+ cities.",
        "photo_url": "https://example.com/photo.jpg",
        "additional_links": ["https://github.com/antoinepedretti"],
        "experiences": [
            {
                "title": "DevOps Engineer",
                "company": "Vizzia",
                "location": "Paris, France",
                "start_date": "Oct 2023",
                "end_date": "Present",
                "description": "Led DevOps initiatives for cloud infrastructure and automation."
            },
            {
                "title": "Cloud Engineer",
                "company": "Tech Startup",
                "location": "Paris, France",
                "start_date": "Jan 2021",
                "end_date": "Sep 2023",
                "description": "Managed AWS infrastructure and CI/CD pipelines."
            }
        ],
        "education": [
            {
                "degree": "Master Cloud & Cybersecurity",
                "school": "IPSSI",
                "field": "Cloud Computing & Cybersecurity",
                "location": "Paris, France",
                "start_date": "2023",
                "end_date": "2025"
            }
        ],
        "skills": [
            "AWS", "Docker", "Kubernetes", "Terraform", "Jenkins",
            "Python", "Linux", "CI/CD", "GitOps", "DevSecOps"
        ],
        "certifications": []
    }


@pytest.fixture
def mock_job_data() -> Dict[str, Any]:
    """Mock job posting data (DevOps Engineer)."""
    return {
        "title": "Senior DevOps Engineer",
        "company": "Metyis",
        "location": "Paris, France",
        "seniority_level": "Senior",
        "description": """
We are looking for a Senior DevOps Engineer to join our team.

Required Skills:
- 4+ years of experience in DevOps
- Strong expertise in AWS, Docker, Kubernetes
- Experience with CI/CD pipelines (Jenkins, GitLab CI, Azure DevOps)
- Infrastructure as Code (Terraform, Ansible)
- GitOps and DevSecOps practices
- Agile/Scrum methodology
- Strong Python and automation skills

Responsibilities:
- Design and implement CI/CD pipelines
- Manage cloud infrastructure on AWS
- Automate deployment processes
- Ensure high availability and scalability
- Collaborate with development teams
        """,
        "job_url": "https://www.linkedin.com/jobs/view/4256544321"
    }


@pytest.fixture
def mock_job_data_sales() -> Dict[str, Any]:
    """Mock job posting data (Sales role)."""
    return {
        "title": "Sales Manager",
        "company": "Tech Corp",
        "location": "Paris, France",
        "seniority_level": "Mid-Senior",
        "description": """
Looking for an experienced Sales Manager to drive revenue growth.

Requirements:
- 5+ years in B2B sales
- Proven track record of exceeding quotas
- CRM experience (Salesforce, HubSpot)
- Strong negotiation and communication skills
- Team leadership experience
        """,
        "job_url": "https://www.linkedin.com/jobs/view/123456"
    }


@pytest.fixture
def expected_resume_structure() -> Dict[str, Any]:
    """Expected structure of generated resume with ATS optimizations."""
    return {
        "personal_info": {
            "full_name": str,
            "email": str,
            "phone": str,
            "location": str,
            "linkedin": str,
            "headline": str,
            "job_title_variants": list,  # NEW: ATS optimization
            "additional_links": list
        },
        "professional_summary": str,
        "work_experience": [
            {
                "title": str,
                "company": str,
                "location": str,
                "start_date": str,
                "end_date": str,
                "bullets": list  # NEW: Bullet points instead of paragraphs
            }
        ],
        "education": list,
        "skills": dict,
        "certifications": list,  # NEW: AI-generated
        "projects": list,  # NEW: AI-generated
        "languages": list  # NEW: AI-generated
    }


# ============================================================================
# MOCK EXTERNAL SERVICES
# ============================================================================

@pytest.fixture
def mock_apify_response():
    """Mock Apify API response for profile scraping."""
    return {
        "fullName": "Antoine Pedretti",
        "headline": "DevOps Engineer",
        "summary": "Experienced DevOps Engineer...",
        "photoUrl": "https://example.com/photo.jpg",
        "experiences": [],
        "education": [],
        "skills": []
    }


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response for AI generation."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "professional_summary": "DevOps Engineer with 3+ years...",
                        "job_title_variants": ["DevOps Engineer", "Cloud Engineer", "SRE"],
                        "enhanced_experiences": [],
                        "skill_descriptions": {},
                        "certifications": [],
                        "projects": [],
                        "languages": []
                    })
                }
            }
        ]
    }


# ============================================================================
# TEMPORARY DIRECTORIES FOR FILE TESTS
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary directory for generated files."""
    output_dir = tmp_path / "generated_resumes"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_templates_dir(tmp_path):
    """Create temporary directory for test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a dummy template file
    template_file = templates_dir / "ATS_test_template.docx"
    template_file.write_text("dummy template content")

    return templates_dir


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def load_fixture():
    """Helper to load fixture files from tests/fixtures/."""
    def _load_fixture(filename: str) -> Dict[str, Any]:
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            filename
        )
        with open(fixture_path, 'r') as f:
            return json.load(f)
    return _load_fixture


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "ai: Tests using AI/LLM")
    config.addinivalue_line("markers", "mock: Tests with mocked services")
