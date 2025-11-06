"""
Simple integration test for job search
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.uploaded_resume import UploadedResume
from app.models.linkedin_service_account import LinkedInServiceAccount
from app.services.service_account_manager import ServiceAccountManager
from datetime import datetime
import uuid


def test_service_account_retrieval():
    """Test that we can retrieve a service account"""
    db = SessionLocal()
    try:
        # Check if service account exists
        account = db.query(LinkedInServiceAccount)\
            .filter(LinkedInServiceAccount.is_active == True)\
            .first()

        if not account:
            print("❌ No active service account found!")
            print("   Run: docker compose exec backend python scripts/add_service_account.py --list")
            return False

        print(f"✅ Found service account: {account.id}")

        # Try to get credentials
        try:
            email, password = ServiceAccountManager.get_available_account(db)
            print(f"✅ Successfully decrypted credentials: {email}")
            return True
        except Exception as e:
            print(f"❌ Failed to get service account: {e}")
            return False

    finally:
        db.close()


def test_resume_analysis():
    """Test that resume has been analyzed"""
    db = SessionLocal()
    try:
        resume = db.query(UploadedResume)\
            .filter(UploadedResume.analyzed_data != None)\
            .first()

        if not resume:
            print("❌ No analyzed resumes found!")
            return False

        print(f"✅ Found analyzed resume: {resume.filename}")

        # Check for search keywords
        search_keywords = resume.analyzed_data.get('search_keywords', [])
        if not search_keywords:
            print("❌ No search keywords in resume analysis!")
            return False

        print(f"✅ Search keywords: {search_keywords[:5]}")
        return True

    finally:
        db.close()


if __name__ == '__main__':
    print("\n=== Testing Job Search Prerequisites ===\n")

    test1 = test_service_account_retrieval()
    test2 = test_resume_analysis()

    print("\n=== Results ===")
    print(f"Service Account: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Resume Analysis: {'✅ PASS' if test2 else '❌ FAIL'}")

    if test1 and test2:
        print("\n✅ All prerequisites met! Job search should work.")
    else:
        print("\n❌ Some prerequisites failed. Fix them before testing job search.")
