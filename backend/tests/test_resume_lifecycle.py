"""
Comprehensive tests for resume upload, analyze, view, and delete functionality.
Ensures these operations never fail again.

Run with: docker compose exec backend python -m pytest tests/test_resume_lifecycle.py -v -s
"""
import pytest
from datetime import datetime
import uuid
import io


class TestResumeUpload:
    """Test resume upload functionality"""

    def test_upload_pdf_resume(self, client, test_user, auth_headers):
        """Test uploading a PDF resume"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4 test resume content with Python and AWS experience"
        pdf_file = ('test_resume.pdf', io.BytesIO(pdf_content), 'application/pdf')

        response = client.post(
            '/api/uploaded-resumes/upload',
            files={'file': pdf_file},
            headers=auth_headers
        )

        assert response.status_code == 200, f"Upload failed: {response.json()}"
        data = response.json()

        assert 'id' in data
        assert data['filename'] == 'test_resume.pdf'
        assert 'parsed_text' in data
        assert data['analyzed_data'] is None  # Not analyzed yet

        print(f"✅ Resume uploaded successfully: {data['id']}")
        return data['id']

    def test_upload_docx_resume(self, client, test_user, auth_headers):
        """Test uploading a DOCX resume"""
        docx_content = b"PK mock DOCX content with DevOps and Cloud keywords"
        docx_file = ('test_resume.docx', io.BytesIO(docx_content), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

        response = client.post(
            '/api/uploaded-resumes/upload',
            files={'file': docx_file},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['filename'] == 'test_resume.docx'

        print(f"✅ DOCX resume uploaded successfully")

    def test_upload_invalid_file_type(self, client, test_user, auth_headers):
        """Test that invalid file types are rejected"""
        txt_file = ('test.txt', io.BytesIO(b"plain text resume"), 'text/plain')

        response = client.post(
            '/api/uploaded-resumes/upload',
            files={'file': txt_file},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert 'Only PDF and DOCX' in response.json()['detail']

        print(f"✅ Invalid file type correctly rejected")

    def test_upload_without_auth(self, client):
        """Test that upload requires authentication"""
        pdf_file = ('test.pdf', io.BytesIO(b"%PDF test"), 'application/pdf')

        response = client.post(
            '/api/uploaded-resumes/upload',
            files={'file': pdf_file}
        )

        assert response.status_code in [401, 403]

        print(f"✅ Unauthenticated upload correctly rejected")


class TestResumeAnalysis:
    """Test resume analysis functionality"""

    def test_analyze_uploaded_resume(self, client, test_user, auth_headers, db_session):
        """Test analyzing an uploaded resume"""
        from app.models.uploaded_resume import UploadedResume

        # Create a resume to analyze
        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="test_resume.pdf",
            parsed_text="Python Developer with 5 years experience in AWS, Docker, Kubernetes, and DevOps. Skilled in Terraform, Jenkins, and microservices architecture.",
            analyzed_data=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()
        db_session.refresh(resume)

        # Mock the AI analysis (since we don't want to call real API in tests)
        from unittest.mock import patch

        mock_analysis = {
            "search_keywords": ["Python", "AWS", "Docker", "DevOps", "Kubernetes"],
            "technical_skills": ["Python", "AWS", "Docker", "Kubernetes", "Terraform", "Jenkins"],
            "years_of_experience": 5,
            "seniority_level": "mid",
            "job_titles": ["Python Developer", "DevOps Engineer", "Cloud Engineer"]
        }

        with patch('app.api.uploaded_resumes.analyze_resume_with_ai', return_value=mock_analysis):
            response = client.post(
                f'/api/uploaded-resumes/{resume.id}/analyze',
                headers=auth_headers
            )

        assert response.status_code == 200, f"Analysis failed: {response.json()}"
        data = response.json()

        assert data['id'] == str(resume.id)
        assert data['analyzed_data'] is not None
        assert 'search_keywords' in data['analyzed_data']
        assert len(data['analyzed_data']['search_keywords']) > 0

        print(f"✅ Resume analyzed successfully with {len(data['analyzed_data']['search_keywords'])} keywords")

    def test_analyze_nonexistent_resume(self, client, test_user, auth_headers):
        """Test analyzing a resume that doesn't exist"""
        fake_id = str(uuid.uuid4())

        response = client.post(
            f'/api/uploaded-resumes/{fake_id}/analyze',
            headers=auth_headers
        )

        assert response.status_code == 404

        print(f"✅ Nonexistent resume correctly returns 404")

    def test_analyze_already_analyzed_resume(self, client, test_user, auth_headers, db_session):
        """Test re-analyzing an already analyzed resume"""
        from app.models.uploaded_resume import UploadedResume

        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="analyzed.pdf",
            parsed_text="Already analyzed resume content",
            analyzed_data={"search_keywords": ["Python", "AWS"]},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        from unittest.mock import patch
        with patch('app.api.uploaded_resumes.analyze_resume_with_ai', return_value={"search_keywords": ["Updated"]}):
            response = client.post(
                f'/api/uploaded-resumes/{resume.id}/analyze',
                headers=auth_headers
            )

        # Should succeed and update the analysis
        assert response.status_code == 200

        print(f"✅ Re-analysis works correctly")


class TestResumeView:
    """Test viewing resumes"""

    def test_list_uploaded_resumes(self, client, test_user, auth_headers, db_session):
        """Test listing all uploaded resumes"""
        from app.models.uploaded_resume import UploadedResume

        # Create multiple resumes
        resumes = []
        for i in range(3):
            resume = UploadedResume(
                id=uuid.uuid4(),
                user_id=test_user.id,
                filename=f"resume_{i}.pdf",
                parsed_text=f"Resume {i} content",
                analyzed_data={"search_keywords": ["Python"]} if i % 2 == 0 else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            resumes.append(resume)
            db_session.add(resume)

        db_session.commit()

        response = client.get(
            '/api/uploaded-resumes/',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

        # Verify each resume has required fields
        for resume_data in data:
            assert 'id' in resume_data
            assert 'filename' in resume_data
            assert 'analyzed_data' in resume_data

        print(f"✅ Listed {len(data)} resumes successfully")

    def test_get_single_resume(self, client, test_user, auth_headers, db_session):
        """Test getting a single resume by ID"""
        from app.models.uploaded_resume import UploadedResume

        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="single_resume.pdf",
            parsed_text="Single resume content with AWS and Python",
            analyzed_data={"search_keywords": ["AWS", "Python"]},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        response = client.get(
            f'/api/uploaded-resumes/{resume.id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == str(resume.id)
        assert data['filename'] == 'single_resume.pdf'
        assert data['analyzed_data'] is not None

        print(f"✅ Retrieved single resume successfully")

    def test_get_resume_of_another_user(self, client, test_user, auth_headers, db_session):
        """Test that users cannot view other users' resumes"""
        from app.models.uploaded_resume import UploadedResume
        from app.models.user import User

        # Create another user
        other_user = User(
            email="other@example.com",
            linkedin_id="other-linkedin-id"
        )
        db_session.add(other_user)
        db_session.commit()

        # Create resume for other user
        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=other_user.id,
            filename="other_resume.pdf",
            parsed_text="Other user's resume",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        # Try to access it with test_user's auth
        response = client.get(
            f'/api/uploaded-resumes/{resume.id}',
            headers=auth_headers
        )

        assert response.status_code == 404  # Should not find it

        print(f"✅ Cross-user access correctly denied")


class TestResumeDelete:
    """Test resume deletion"""

    def test_delete_resume(self, client, test_user, auth_headers, db_session):
        """Test deleting an uploaded resume"""
        from app.models.uploaded_resume import UploadedResume

        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="to_delete.pdf",
            parsed_text="Resume to be deleted",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        resume_id = resume.id

        response = client.delete(
            f'/api/uploaded-resumes/{resume_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'deleted' in data['message'].lower()

        # Verify it's actually deleted
        deleted_resume = db_session.query(UploadedResume).filter_by(id=resume_id).first()
        assert deleted_resume is None

        print(f"✅ Resume deleted successfully")

    def test_delete_nonexistent_resume(self, client, test_user, auth_headers):
        """Test deleting a resume that doesn't exist"""
        fake_id = str(uuid.uuid4())

        response = client.delete(
            f'/api/uploaded-resumes/{fake_id}',
            headers=auth_headers
        )

        assert response.status_code == 404

        print(f"✅ Nonexistent resume delete correctly returns 404")

    def test_delete_resume_with_jobs(self, client, test_user, auth_headers, db_session):
        """Test deleting a resume that has associated scraped jobs"""
        from app.models.uploaded_resume import UploadedResume
        from app.models.scraped_job import ScrapedJob

        # Create resume
        resume = UploadedResume(
            id=uuid.uuid4(),
            user_id=test_user.id,
            filename="resume_with_jobs.pdf",
            parsed_text="Resume with jobs",
            analyzed_data={"search_keywords": ["Python"]},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(resume)
        db_session.commit()

        # Create associated job
        job = ScrapedJob(
            id=uuid.uuid4(),
            user_id=test_user.id,
            uploaded_resume_id=resume.id,
            linkedin_post_url="https://linkedin.com/jobs/123",
            job_title="Python Developer",
            company_name="Tech Corp",
            scraped_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()

        resume_id = resume.id

        # Delete resume (should also delete associated jobs or handle gracefully)
        response = client.delete(
            f'/api/uploaded-resumes/{resume_id}',
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify resume is deleted
        deleted_resume = db_session.query(UploadedResume).filter_by(id=resume_id).first()
        assert deleted_resume is None

        print(f"✅ Resume with jobs deleted successfully")


class TestDatabaseMigrations:
    """Test that database is properly migrated"""

    def test_all_tables_exist(self, db_session):
        """Test that all required tables exist"""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()

        required_tables = [
            'users',
            'linkedin_profiles',
            'job_postings',
            'resumes',
            'uploaded_resumes',
            'scraped_jobs',
            'linkedin_service_accounts',
            'alembic_version'
        ]

        for table in required_tables:
            assert table in tables, f"Required table '{table}' is missing!"

        print(f"✅ All {len(required_tables)} required tables exist")

    def test_uploaded_resumes_schema(self, db_session):
        """Test that uploaded_resumes table has correct schema"""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        columns = {col['name']: col for col in inspector.get_columns('uploaded_resumes')}

        required_columns = [
            'id', 'user_id', 'filename', 'file_path', 'parsed_text',
            'analyzed_data', 'created_at', 'updated_at'
        ]

        for col_name in required_columns:
            assert col_name in columns, f"Required column '{col_name}' is missing!"

        print(f"✅ uploaded_resumes table schema is correct")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
