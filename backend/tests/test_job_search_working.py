"""
Working test for job search with mocked LinkedIn scraper
Run with: docker compose exec backend python -m pytest tests/test_job_search_working.py -v -s
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import uuid


class TestJobSearchWorkflow:
    """Test the complete job search workflow"""

    @patch('app.api.job_search.LinkedInJobScraper')
    def test_search_jobs_end_to_end(
        self,
        mock_scraper_class,
        client,
        test_user,
        auth_headers,
        db_session
    ):
        """Test complete job search from upload to results"""
        from app.models.uploaded_resume import UploadedResume
        from app.models.linkedin_service_account import LinkedInServiceAccount
        from app.core.encryption import get_encryption_service

        # 1. Create a service account
        encryption = get_encryption_service()
        service_account = LinkedInServiceAccount(
            id=uuid.uuid4(),
            email=encryption.encrypt("scraper@example.com"),
            password=encryption.encrypt("password123"),
            is_premium=False,
            is_active=True,
            last_used_at=None,
            requests_count_today=0,
            created_at=datetime.utcnow()
        )
        db_session.add(service_account)
        db_session.commit()

        # 2. Create an analyzed resume
        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="test_resume.pdf",
            parsed_text="Python developer with AWS and DevOps experience",
            analyzed_data={
                "search_keywords": ["Python", "AWS", "DevOps", "Cloud Engineer"],
                "technical_skills": ["Python", "AWS", "Docker"],
                "years_of_experience": 5,
                "seniority_level": "mid"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()
        db_session.refresh(resume)

        # 3. Mock the LinkedIn scraper
        mock_scraper = MagicMock()
        mock_scraper_class.return_value.__enter__.return_value = mock_scraper

        # Mock successful login
        mock_scraper.login.return_value = True

        # Mock job search results
        mock_scraper.search_jobs.return_value = [
            {
                'linkedin_post_url': 'https://linkedin.com/jobs/python-dev-123',
                'job_title': 'Senior Python Developer',
                'company_name': 'Tech Corp',
                'location': 'Paris, France',
                'description': 'Looking for a Python developer with AWS experience...',
                'posted_date': '2 days ago',
                'is_remote': True,
                'employment_type': 'Full-time',
                'seniority_level': 'Senior',
                'scraped_at': datetime.utcnow()
            },
            {
                'linkedin_post_url': 'https://linkedin.com/jobs/devops-456',
                'job_title': 'DevOps Engineer',
                'company_name': 'Cloud Solutions Inc',
                'location': 'Remote',
                'description': 'DevOps engineer needed for cloud infrastructure...',
                'posted_date': '1 week ago',
                'is_remote': True,
                'employment_type': 'Full-time',
                'seniority_level': 'Mid-Senior',
                'scraped_at': datetime.utcnow()
            }
        ]

        # 4. Make the API request
        response = client.post(
            '/api/job-search/search',
            json={
                'resume_id': str(resume.id),
                'location': 'Paris, France',
                'remote_only': False,
                'max_results': 20
            },
            headers=auth_headers
        )

        # 5. Verify the response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

        data = response.json()
        assert 'jobs_found' in data
        assert 'jobs_saved' in data
        assert 'jobs' in data

        assert data['jobs_found'] == 2
        assert data['jobs_saved'] == 2
        assert len(data['jobs']) == 2

        # Verify job details
        job1 = data['jobs'][0]
        assert job1['job_title'] == 'Senior Python Developer'
        assert job1['company_name'] == 'Tech Corp'
        assert job1['is_remote'] is True

        job2 = data['jobs'][1]
        assert job2['job_title'] == 'DevOps Engineer'
        assert job2['company_name'] == 'Cloud Solutions Inc'

        # 6. Verify scraper was called correctly
        mock_scraper.login.assert_called_once_with('scraper@example.com', 'password123')
        mock_scraper.search_jobs.assert_called_once()

        call_kwargs = mock_scraper.search_jobs.call_args[1]
        assert 'Python' in call_kwargs['keywords']
        assert call_kwargs['location'] == 'Paris, France'
        assert call_kwargs['remote_only'] is False
        assert call_kwargs['max_results'] == 20

        # 7. Verify jobs are in database
        from app.models.scraped_job import ScrapedJob
        saved_jobs = db_session.query(ScrapedJob)\
            .filter(ScrapedJob.uploaded_resume_id == resume.id)\
            .all()

        assert len(saved_jobs) == 2

        print("\n✅ Test passed! Job search workflow working correctly.")


    @patch('app.api.job_search.LinkedInJobScraper')
    def test_search_jobs_login_failure(
        self,
        mock_scraper_class,
        client,
        test_user,
        auth_headers,
        db_session
    ):
        """Test job search fails gracefully when LinkedIn login fails"""
        from app.models.uploaded_resume import UploadedResume
        from app.models.linkedin_service_account import LinkedInServiceAccount
        from app.core.encryption import get_encryption_service

        # Create service account
        encryption = get_encryption_service()
        service_account = LinkedInServiceAccount(
            id=uuid.uuid4(),
            email=encryption.encrypt("scraper@example.com"),
            password=encryption.encrypt("wrongpassword"),
            is_premium=False,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(service_account)
        db_session.commit()

        # Create resume
        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="test.pdf",
            parsed_text="test",
            analyzed_data={
                "search_keywords": ["Python"],
                "technical_skills": ["Python"]
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        # Mock login failure
        mock_scraper = MagicMock()
        mock_scraper_class.return_value.__enter__.return_value = mock_scraper
        mock_scraper.login.return_value = False

        # Make request
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

        # Should fail with proper error
        assert response.status_code == 500
        assert 'login failed' in response.json()['detail'].lower()

        print("\n✅ Login failure handled correctly!")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
