from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add legacy code to path
sys.path.append('/app/legacy')

from ..core.database import get_db
from ..core.security import create_access_token, verify_token
from ..core.config import settings
from ..models.user import User
from ..models.profile import LinkedInProfile

# Import your existing LinkedIn scraper
try:
    import linkedin_scraper_final
except ImportError:
    linkedin_scraper_final = None

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    linkedin_id: Optional[str]
    subscription_status: str
    resumes_generated_count: str


@router.get("/linkedin/login")
async def linkedin_login():
    """Redirect to LinkedIn OAuth"""
    # Request comprehensive profile access
    # Note: r_liteprofile is deprecated, using w_member_social for profile access
    # openid, profile, email - basic OAuth2 scopes
    # r_basicprofile - basic profile (deprecated but may still work)
    # w_member_social - allows reading member's profile
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={settings.LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={settings.LINKEDIN_REDIRECT_URI}"
        f"&scope=openid%20profile%20email%20w_member_social"
    )
    return {"auth_url": linkedin_auth_url}


@router.get("/linkedin/callback")
async def linkedin_callback(code: str, db: Session = Depends(get_db)):
    """Handle LinkedIn OAuth callback"""

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    try:
        # Import your existing LinkedIn OAuth handler
        import requests

        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        }

        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        # Get LinkedIn profile data using access token
        profile_url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        # Extract user info
        linkedin_id = profile_data.get("sub")
        email = profile_data.get("email")
        full_name = profile_data.get("name", "")  # Get user's full name
        
        # Try to construct LinkedIn profile URL from vanity name
        profile_url_linkedin = None
        vanity_name = profile_data.get("sub")  # LinkedIn ID can be used to construct URL
        # Note: LinkedIn doesn't always provide the vanity URL in OAuth, but we'll try

        if not linkedin_id or not email:
            raise HTTPException(status_code=400, detail="Failed to get user info from LinkedIn")

        # Check if user exists by linkedin_id OR email (prevent duplicate email error)
        user = db.query(User).filter(
            (User.linkedin_id == linkedin_id) | (User.email == email)
        ).first()

        if not user:
            # Create new user
            user = User(
                email=email,
                linkedin_id=linkedin_id,
                linkedin_access_token=access_token,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Try to fetch profile data using Apify
            # First create a basic profile, then we'll try to enhance it with Apify in background
            profile_raw_data = profile_data.copy()
            profile_raw_data["name"] = full_name

            linkedin_profile = LinkedInProfile(
                user_id=user.id,
                raw_data=profile_raw_data,
                headline=full_name,  # Start with basic name
                summary="",
                experiences=[],
                education=[],
                skills=[],
                certifications=[]
            )

            print(f"✓ Basic LinkedIn profile created for {email}")
            print(f"   User will be prompted to sync their full profile via Apify")

            db.add(linkedin_profile)
            db.commit()
        else:
            # Update existing user (in case linkedin_id changed or user logging in again)
            user.linkedin_id = linkedin_id
            user.linkedin_access_token = access_token
            db.commit()
            print(f"✓ Existing user {email} logged in")

        # Create JWT token
        jwt_token = create_access_token({"sub": str(user.id)})

        # Redirect to frontend with token
        frontend_redirect = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
        return RedirectResponse(url=frontend_redirect)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"LinkedIn API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's name from profile if available
    profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()
    name = None
    if profile and profile.raw_data:
        name = profile.raw_data.get("name") or profile.headline
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=name,
        linkedin_id=user.linkedin_id,
        subscription_status=user.subscription_status.value,
        resumes_generated_count=user.resumes_generated_count
    )
