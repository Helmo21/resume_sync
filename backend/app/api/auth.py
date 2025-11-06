from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..core.database import get_db
from ..core.security import verify_token, hash_password, verify_password, create_access_token
from ..models.user import User
from ..models.profile import LinkedInProfile

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    subscription_status: str
    resumes_generated_count: str


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user with email and password"""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create empty LinkedIn profile for the user
    # This ensures resume generation doesn't fail
    empty_profile = LinkedInProfile(
        user_id=new_user.id,
        headline="",
        summary="",
        raw_data={"name": request.email.split('@')[0]},  # Use email prefix as default name
        experiences=[],
        education=[],
        skills=[],
        certifications=[]
    )
    db.add(empty_profile)
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login with email and password"""

    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return TokenResponse(access_token=access_token)


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
        subscription_status=user.subscription_status.value,
        resumes_generated_count=user.resumes_generated_count
    )
