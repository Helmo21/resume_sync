"""
API endpoints for uploaded resume management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import io

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..models.uploaded_resume import UploadedResume
from ..services.resume_parser import ResumeParser, ResumeParserError
from ..services.resume_analyzer import ResumeAnalyzer


router = APIRouter()


class UploadedResumeResponse(BaseModel):
    """Response model for uploaded resume"""
    id: str
    filename: str
    parsed_text: str
    analyzed_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadedResumeListResponse(BaseModel):
    """List of uploaded resumes"""
    id: str
    filename: str
    created_at: datetime
    has_analysis: bool

    class Config:
        from_attributes = True


@router.post("/upload", response_model=UploadedResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a resume file (PDF or DOCX).

    The file will be parsed to extract text and stored in the database.
    Supported formats: PDF, DOCX
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.docx')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF or DOCX files only."
        )

    # Read file content
    try:
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Parse resume to extract text
    try:
        parsed_text = ResumeParser.parse_resume(file_stream, file.filename)
    except ResumeParserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate extracted text
    if not parsed_text or len(parsed_text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Could not extract sufficient text from resume. Please ensure the file is not corrupted."
        )

    # Create uploaded resume record
    uploaded_resume = UploadedResume(
        id=uuid.uuid4(),
        user_id=user.id,
        filename=file.filename,
        file_path=None,  # We're not storing the file, just the parsed text
        parsed_text=parsed_text,
        analyzed_data=None,  # Will be populated by auto-analysis below
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Save to database
    try:
        db.add(uploaded_resume)
        db.commit()
        db.refresh(uploaded_resume)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")

    # Auto-analyze resume with AI (Phase 2)
    try:
        analyzer = ResumeAnalyzer()
        analysis_result = analyzer.analyze_resume(parsed_text)

        # Update with analysis
        uploaded_resume.analyzed_data = analysis_result
        uploaded_resume.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(uploaded_resume)
    except Exception as e:
        # Log error but don't fail the upload - user can manually trigger analysis later
        print(f"Auto-analysis failed for resume {uploaded_resume.id}: {str(e)}")
        # Analysis will remain None, user can trigger it manually

    return UploadedResumeResponse(
        id=str(uploaded_resume.id),
        filename=uploaded_resume.filename,
        parsed_text=uploaded_resume.parsed_text,
        analyzed_data=uploaded_resume.analyzed_data,
        created_at=uploaded_resume.created_at,
        updated_at=uploaded_resume.updated_at
    )


@router.get("/", response_model=List[UploadedResumeListResponse])
async def list_uploaded_resumes(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    List all uploaded resumes for the authenticated user.
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all uploaded resumes for user
    uploaded_resumes = db.query(UploadedResume)\
        .filter(UploadedResume.user_id == user.id)\
        .order_by(UploadedResume.created_at.desc())\
        .all()

    return [
        UploadedResumeListResponse(
            id=str(resume.id),
            filename=resume.filename,
            created_at=resume.created_at,
            has_analysis=resume.analyzed_data is not None
        )
        for resume in uploaded_resumes
    ]


@router.get("/{resume_id}", response_model=UploadedResumeResponse)
async def get_uploaded_resume(
    resume_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific uploaded resume.
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get uploaded resume
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID format")

    uploaded_resume = db.query(UploadedResume)\
        .filter(UploadedResume.id == resume_uuid, UploadedResume.user_id == user.id)\
        .first()

    if not uploaded_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return UploadedResumeResponse(
        id=str(uploaded_resume.id),
        filename=uploaded_resume.filename,
        parsed_text=uploaded_resume.parsed_text,
        analyzed_data=uploaded_resume.analyzed_data,
        created_at=uploaded_resume.created_at,
        updated_at=uploaded_resume.updated_at
    )


@router.delete("/{resume_id}")
async def delete_uploaded_resume(
    resume_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Delete an uploaded resume.
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get uploaded resume
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID format")

    uploaded_resume = db.query(UploadedResume)\
        .filter(UploadedResume.id == resume_uuid, UploadedResume.user_id == user.id)\
        .first()

    if not uploaded_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete from database
    try:
        db.delete(uploaded_resume)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete resume: {str(e)}")

    return {"message": "Resume deleted successfully"}


@router.post("/{resume_id}/analyze", response_model=UploadedResumeResponse)
async def analyze_uploaded_resume(
    resume_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Analyze an uploaded resume using AI to extract searchable metadata.

    This will:
    1. Extract skills (technical & soft)
    2. Identify job titles and experience level
    3. Determine industries/domains
    4. Infer language and remote preferences
    5. Generate LinkedIn search keywords
    """
    # Verify authentication
    token = authorization.replace("Bearer ", "")
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Get user from database using user ID from token
    user_id = user_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get uploaded resume
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID format")

    uploaded_resume = db.query(UploadedResume)\
        .filter(UploadedResume.id == resume_uuid, UploadedResume.user_id == user.id)\
        .first()

    if not uploaded_resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Check if already analyzed (allow re-analysis)
    if uploaded_resume.analyzed_data:
        # You can add a flag to prevent re-analysis if desired
        pass

    # Analyze resume with AI
    try:
        analyzer = ResumeAnalyzer()
        analysis_result = analyzer.analyze_resume(uploaded_resume.parsed_text)

        # Update database with analysis
        uploaded_resume.analyzed_data = analysis_result
        uploaded_resume.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(uploaded_resume)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Resume analysis failed: {str(e)}"
        )

    return UploadedResumeResponse(
        id=str(uploaded_resume.id),
        filename=uploaded_resume.filename,
        parsed_text=uploaded_resume.parsed_text,
        analyzed_data=uploaded_resume.analyzed_data,
        created_at=uploaded_resume.created_at,
        updated_at=uploaded_resume.updated_at
    )
