"""
Tests for job search functionality with service accounts
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.models.user import User
from app.models.uploaded_resume import UploadedResume
from app.models.linkedin_service_account import LinkedInServiceAccount
from app.services.service_account_manager import ServiceAccountManager


@pytest.fixture
def service_account(db_session):
    """Create a test service account"""
    from app.core.encryption import get_encryption_service

    encryption = get_encryption_service()
    account = LinkedInServiceAccount(
        id=uuid.uuid4(),
        email=encryption.encrypt("test@example.com"),
        password=encryption.encrypt("testpassword"),
        is_premium=False,
        is_active=True,
        last_used_at=None,
        requests_count_today=0,
        created_at=datetime.utcnow()
    )

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    return account


@pytest.fixture
def analyzed_resume(db_session, test_user):
    """Create an analyzed resume"""
    resume = UploadedResume(
        id=uuid.uuid4(),
        user_id=test_user.id,
        filename="test_resume.pdf",
        parsed_text="Test resume content with Python, AWS, DevOps experience.",
        analyzed_data={
            "search_keywords": ["Python", "AWS", "DevOps", "Cloud"],
            "technical_skills": ["Python", "AWS"],
            "years_of_experience": 5,
            "seniority_level": "mid"
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    return resume


class TestServiceAccountManager:
    """Test ServiceAccountManager functionality"""

    def test_get_available_account_success(self, db_session, service_account):
        """Test getting an available service account"""
        email, password = ServiceAccountManager.get_available_account(db_session)

        assert email == "test@example.com"
        assert password == "testpassword"

        # Verify usage was updated
        db_session.refresh(service_account)
        assert service_account.last_used_at is not None
        assert service_account.requests_count_today == 1

    def test_get_available_account_no_accounts(self, db_session):
        """Test error when no service accounts available"""
        with pytest.raises(Exception) as exc_info:
            ServiceAccountManager.get_available_account(db_session)

        assert "No LinkedIn service accounts available" in str(exc_info.value)

    def test_add_account(self, db_session):
        """Test adding a new service account"""
        account = ServiceAccountManager.add_account(
            db=db_session,
            email="new@example.com",
            password="newpassword",
            is_premium=True,
            is_active=True
        )

        assert account.id is not None
        assert account.is_premium is True
        assert account.is_active is True

        # Verify credentials are encrypted
        from app.core.encryption import get_encryption_service
        encryption = get_encryption_service()

        decrypted_email = encryption.decrypt(account.email)
        decrypted_password = encryption.decrypt(account.password)

        assert decrypted_email == "new@example.com"
        assert decrypted_password == "newpassword"

    def test_list_accounts(self, db_session, service_account):
        """Test listing service accounts"""
        accounts = ServiceAccountManager.list_accounts(db_session)

        assert len(accounts) == 1
        assert accounts[0]['id'] == str(service_account.id)
        assert 't***@example.com' in accounts[0]['email']  # Masked
        assert accounts[0]['is_active'] is True

    def test_deactivate_account(self, db_session, service_account):
        """Test deactivating a service account"""
        success = ServiceAccountManager.deactivate_account(
            db=db_session,
            account_id=str(service_account.id)
        )

        assert success is True

        # Verify account is deactivated
        db_session.refresh(service_account)
        assert service_account.is_active is False


class TestJobSearchAPI:
    """Test job search API endpoints"""

    @patch('app.services.linkedin_job_scraper.LinkedInJobScraper')
    def test_search_jobs_success(
        self,
        mock_scraper_class,
        client,
        test_user,
        analyzed_resume,
        service_account,
        auth_headers
    ):
        """Test successful job search"""
        # Mock the scraper
        mock_scraper = MagicMock()
        mock_scraper_class.return_value.__enter__.return_value = mock_scraper

        # Mock scraper methods
        mock_scraper.login.return_value = True
        mock_scraper.search_jobs.return_value = [
            {
                'linkedin_post_url': 'https://linkedin.com/jobs/123',
                'job_title': 'Python Developer',
                'company_name': 'Tech Corp',
                'location': 'Paris, France',
                'description': 'Looking for a Python developer...',
                'posted_date': '2 days ago',
                'is_remote': True,
                'employment_type': 'Full-time',
                'seniority_level': 'Mid',
                'scraped_at': datetime.utcnow()
            },
            {
                'linkedin_post_url': 'https://linkedin.com/jobs/456',
                'job_title': 'DevOps Engineer',
                'company_name': 'Cloud Inc',
                'location': 'Remote',
                'description': 'DevOps role with AWS...',
                'posted_date': '1 week ago',
                'is_remote': True,
                'employment_type': 'Full-time',
                'seniority_level': 'Senior',
                'scraped_at': datetime.utcnow()
            }
        ]

        # Make request
        response = client.post(
            '/api/job-search/search',
            json={
                'resume_id': str(analyzed_resume.id),
                'location': 'Paris, France',
                'remote_only': False,
                'max_results': 20
            },
            headers=auth_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data['jobs_found'] == 2
        assert data['jobs_saved'] == 2
        assert len(data['jobs']) == 2
        assert data['jobs'][0]['job_title'] == 'Python Developer'
        assert data['jobs'][1]['job_title'] == 'DevOps Engineer'

        # Verify scraper was called with service account credentials
        mock_scraper.login.assert_called_once_with('test@example.com', 'testpassword')
        mock_scraper.search_jobs.assert_called_once()

    def test_search_jobs_no_service_account(
        self,
        client,
        test_user,
        analyzed_resume,
        auth_headers
    ):
        """Test job search fails when no service account available"""
        response = client.post(
            '/api/job-search/search',
            json={
                'resume_id': str(analyzed_resume.id),
                'location': 'Paris, France',
                'remote_only': False,
                'max_results': 20
            },
            headers=auth_headers
        )

        # Should get 500 error about no service accounts
        assert response.status_code == 500
        assert 'No LinkedIn service accounts available' in response.json()['detail']

    def test_search_jobs_resume_not_analyzed(
        self,
        client,
        test_user,
        service_account,
        db_session,
        auth_headers
    ):
        """Test job search fails when resume not analyzed"""
        # Create unanalyzed resume
        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="unanalyzed.pdf",
            parsed_text="Some text",
            analyzed_data=None,  # Not analyzed
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        response = client.post(
            '/api/job-search/search',
            json={
                'resume_id': str(resume.id),
                'location': None,
                'remote_only': False,
                'max_results': 20
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert 'not been analyzed' in response.json()['detail']

    def test_get_scraped_jobs(
        self,
        client,
        test_user,
        analyzed_resume,
        auth_headers
    ):
        """Test getting scraped jobs for a resume"""
        response = client.get(
            f'/api/job-search/resume/{analyzed_resume.id}/jobs',
            headers=auth_headers
        )

        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)
