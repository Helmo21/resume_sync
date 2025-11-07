from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sys

# Add legacy code to path
sys.path.append('/app/legacy')

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..models.profile import LinkedInProfile

router = APIRouter()


class ProfileResponse(BaseModel):
    id: str
    headline: Optional[str]
    summary: Optional[str]
    experiences: list
    education: list
    skills: list
    last_synced_at: str


def get_current_user_from_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get current user's LinkedIn profile"""
    profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return ProfileResponse(
        id=str(profile.id),
        headline=profile.headline,
        summary=profile.summary,
        experiences=profile.experiences or [],
        education=profile.education or [],
        skills=profile.skills or [],
        last_synced_at=profile.last_synced_at.isoformat()
    )


class UpdateProfileRequest(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    profile_url: Optional[str] = None
    experiences: Optional[list] = None
    education: Optional[list] = None
    skills: Optional[list] = None


@router.put("/update")
async def update_profile(
    data: UpdateProfileRequest,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update user's LinkedIn profile data"""
    profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update fields if provided
    if data.headline is not None:
        profile.headline = data.headline
    if data.summary is not None:
        profile.summary = data.summary
    if data.profile_url is not None:
        profile.profile_url = data.profile_url
    if data.experiences is not None:
        profile.experiences = data.experiences
    if data.education is not None:
        profile.education = data.education
    if data.skills is not None:
        profile.skills = data.skills
    
    # Update raw_data to include contact info
    raw_data = profile.raw_data or {}
    if data.email is not None:
        raw_data['email'] = data.email
    if data.phone is not None:
        raw_data['phone'] = data.phone
    if data.location is not None:
        raw_data['location'] = data.location
    profile.raw_data = raw_data
    
    db.commit()
    db.refresh(profile)
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "profile": {
            "headline": profile.headline,
            "summary": profile.summary,
            "experiences": profile.experiences,
            "education": profile.education,
            "skills": profile.skills
        }
    }


class SyncProfileRequest(BaseModel):
    profile_url: Optional[str] = None


@router.post("/sync-with-apify")
async def sync_profile_with_apify(
    data: SyncProfileRequest = SyncProfileRequest(),
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Sync LinkedIn profile using Camoufox (with service account) or Apify fallback.
    Camoufox is more reliable and bypasses LinkedIn detection.
    """
    from ..services.linkedin_profile_scraper import scrape_linkedin_profile_with_account
    from ..services.service_account_manager import ServiceAccountManager
    from ..services.apify_scraper import ApifyLinkedInScraper
    from ..core.config import settings

    print(f"\n{'='*80}")
    print(f"PROFILE SYNC - User: {user.email}")
    print(f"{'='*80}")

    try:
        # Get or create user's profile
        profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()
        if not profile:
            print("⚠️  Profile not found - creating new one")
            profile = LinkedInProfile(user_id=user.id, raw_data={})
            db.add(profile)
            db.commit()
            db.refresh(profile)

        # Determine profile URL to use
        profile_url = data.profile_url or profile.profile_url

        # Check if we have a profile URL
        if not profile_url:
            raise HTTPException(
                status_code=400,
                detail="No LinkedIn profile URL provided. Please provide your LinkedIn profile URL in the request or update your profile first."
            )

        # Update profile URL if provided in request
        if data.profile_url and data.profile_url != profile.profile_url:
            profile.profile_url = data.profile_url
            db.commit()

        print(f"Profile URL: {profile_url}")

        # Try Method 1: Camoufox with service account (BEST - most reliable)
        try:
            print(f"\n🦊 Attempting profile scrape with Camoufox + Service Account...")

            # Get available service account
            email, password = ServiceAccountManager.get_available_account(db)

            print(f"   Using account: {email}")

            # Scrape with Camoufox
            profile_data = await scrape_linkedin_profile_with_account(
                profile_url=profile_url,
                email=email,
                password=password,
                headless=True
            )

            # Note: Account already marked as used by get_available_account()

            # Update profile with scraped data
            profile.profile_url = profile_data.get("profile_url", profile.profile_url)
            profile.headline = profile_data.get("headline", profile.headline)
            profile.summary = profile_data.get("about", profile.summary)
            profile.experiences = profile_data.get("experiences", [])
            profile.education = profile_data.get("education", [])
            profile.skills = profile_data.get("skills", [])
            profile.raw_data = profile_data
            profile.last_synced_at = datetime.utcnow()

            db.commit()

            print(f"\n✅ Profile synced successfully with Camoufox!")
            print(f"   - Name: {profile_data.get('full_name', 'N/A')}")
            print(f"   - Profile URL: {profile.profile_url}")
            print(f"   - Location: {profile_data.get('location', 'N/A')}")
            print(f"   - Headline: {profile.headline}")
            print(f"   - Experiences: {len(profile.experiences)}")
            print(f"   - Education: {len(profile.education)}")
            print(f"   - Skills: {len(profile.skills)}")

            return {
                "success": True,
                "message": "Profile synced successfully with Camoufox",
                "method": "camoufox",
                "profile": {
                    "full_name": profile_data.get("full_name", ""),
                    "profile_url": profile.profile_url,
                    "location": profile_data.get("location", ""),
                    "headline": profile.headline,
                    "summary": profile.summary,
                    "experiences_count": len(profile.experiences),
                    "education_count": len(profile.education),
                    "skills_count": len(profile.skills)
                }
            }

        except Exception as camoufox_error:
            print(f"\n⚠️  Camoufox scraping failed: {str(camoufox_error)}")
            print(f"🔄 Falling back to Apify...")

            # Fallback Method 2: Apify
            if not settings.APIFY_API_TOKEN:
                raise HTTPException(
                    status_code=500,
                    detail=f"Camoufox failed and Apify not configured. Camoufox error: {str(camoufox_error)}"
                )

            try:
                scraper = ApifyLinkedInScraper()
                apify_data = scraper.scrape_profile(profile_url)
                parsed_data = scraper.parse_profile_data(apify_data)

                # Update profile with scraped data
                profile.headline = parsed_data.get("headline", profile.headline)
                profile.summary = parsed_data.get("summary", profile.summary)
                profile.experiences = parsed_data.get("experiences", [])
                profile.education = parsed_data.get("education", [])
                profile.skills = parsed_data.get("skills", [])
                profile.certifications = parsed_data.get("certifications", [])
                profile.apify_data = apify_data
                profile.last_synced_at = datetime.utcnow()

                db.commit()

                print(f"\n✅ Profile synced successfully with Apify fallback!")

                return {
                    "success": True,
                    "message": "Profile synced successfully with Apify (fallback)",
                    "method": "apify",
                    "profile": {
                        "headline": profile.headline,
                        "summary": profile.summary,
                        "experiences_count": len(profile.experiences),
                        "education_count": len(profile.education),
                        "skills_count": len(profile.skills)
                    }
                }
            except Exception as apify_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Both methods failed. Camoufox: {str(camoufox_error)}. Apify: {str(apify_error)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Error during profile sync: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync profile: {str(e)}"
        )


@router.post("/sync-with-camoufox")
async def sync_profile_with_camoufox(
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Trigger Camoufox scraping of LinkedIn profile.
    On first run, will require manual login.
    Subsequent runs will use saved cookies.
    """
    print(f"\n{'='*80}")
    print(f"PROFILE SYNC REQUEST - User: {user.email}")
    print(f"{'='*80}")

    try:
        # Check if scraper is available
        try:
            # Import from the correct location (root directory)
            import sys
            import os
            # Add the project root to the path
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            import linkedin_camoufox_scraper
        except ImportError as e:
            print(f"Import error: {e}")
            raise HTTPException(
                status_code=501,
                detail="LinkedIn scraper not available. Please use the manual profile update endpoint at /api/profile/update"
            )

        # Check if user has saved cookies
        saved_cookies = user.linkedin_cookies
        has_cookies = saved_cookies is not None and len(saved_cookies) > 0

        print(f"Saved cookies: {'Yes (' + str(len(saved_cookies)) + ' cookies)' if has_cookies else 'No'}")

        # If no cookies, require manual login (non-headless)
        # If cookies exist, try headless first
        if not has_cookies:
            print("⚠️  First time sync - manual login required")
            print("   This will open a browser window for you to log in")

            # Run in non-headless mode and allow manual login
            profile_data, captured_cookies = linkedin_camoufox_scraper.scrape_linkedin_profile_camoufox(
                cookies=None,
                headless=False,  # Show browser for manual login
                allow_manual_login=True
            )

            # Save captured cookies
            if captured_cookies:
                user.linkedin_cookies = captured_cookies
                db.commit()
                print(f"✓ Saved {len(captured_cookies)} cookies for future use")

        else:
            print("✓ Using saved cookies for scraping")

            # Try with saved cookies in headless mode
            profile_data, _ = linkedin_camoufox_scraper.scrape_linkedin_profile_camoufox(
                cookies=saved_cookies,
                headless=True,
                allow_manual_login=False
            )

            # Check if scraping succeeded
            if not profile_data.get("full_name") and not profile_data.get("experiences"):
                print("⚠️  Cookies may be expired - trying manual login")

                # Cookies expired, need manual login again
                profile_data, captured_cookies = linkedin_camoufox_scraper.scrape_linkedin_profile_camoufox(
                    cookies=None,
                    headless=False,
                    allow_manual_login=True
                )

                if captured_cookies:
                    user.linkedin_cookies = captured_cookies
                    db.commit()
                    print(f"✓ Updated with {len(captured_cookies)} new cookies")

        # Update profile in database
        profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()

        if not profile:
            print("⚠️  Profile not found - creating new one")
            profile = LinkedInProfile(user_id=user.id)
            db.add(profile)

        # Update profile data
        profile.headline = profile_data.get("headline", profile.headline or "")
        profile.summary = profile_data.get("summary", "")
        profile.experiences = profile_data.get("experiences", [])
        profile.education = profile_data.get("education", [])
        profile.skills = profile_data.get("skills", [])

        # Update raw_data with full profile
        profile.raw_data = profile_data

        db.commit()

        print(f"\n✓ Profile sync completed successfully!")
        print(f"   - Headline: {profile.headline}")
        print(f"   - Experiences: {len(profile.experiences)}")
        print(f"   - Education: {len(profile.education)}")
        print(f"   - Skills: {len(profile.skills)}")

        return {
            "success": True,
            "message": "Profile synced successfully",
            "profile": {
                "headline": profile.headline,
                "summary": profile.summary,
                "experiences_count": len(profile.experiences),
                "education_count": len(profile.education),
                "skills_count": len(profile.skills)
            }
        }

    except Exception as e:
        print(f"\n❌ Error during profile sync: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync profile: {str(e)}"
        )


@router.post("/resync")
async def resync_profile(
    data: SyncProfileRequest = SyncProfileRequest(),
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Re-sync LinkedIn profile data (uses Apify by default)"""
    return await sync_profile_with_apify(data, user, db)
