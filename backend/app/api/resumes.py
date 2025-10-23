from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
import sys
import json
import os

# Add legacy code to path
sys.path.append('/app/legacy')

from ..core.database import get_db
from ..core.security import verify_token
from ..core.config import settings
from ..models.user import User
from ..models.profile import LinkedInProfile
from ..models.job import JobPosting
from ..models.resume import Resume
from ..services.apify_scraper import scrape_linkedin_job
from ..services.document_generator import generate_resume_pdf, generate_resume_docx, ATSTemplateGenerator
from ..services.ai_resume_agent import generate_intelligent_resume
from ..services.template_handler import get_available_templates, analyze_template_file, TemplateHandler
from ..services.template_matcher import select_templates_for_job

router = APIRouter()


class GenerateResumeRequest(BaseModel):
    job_url: HttpUrl
    template_id: str = "modern"
    use_profile_picture: bool = True  # Whether to include LinkedIn profile photo
    additional_links: Optional[List[str]] = []  # GitHub, portfolio, etc.


class GenerateResumeOptionsRequest(BaseModel):
    job_url: HttpUrl
    use_profile_picture: bool = True
    additional_links: Optional[List[str]] = []


class ResumeOption(BaseModel):
    option_id: int
    template_id: str
    template_name: str
    template_type: str
    score: int
    justification: str
    pdf_preview_url: str
    docx_url: str


class ResumeResponse(BaseModel):
    id: str
    template_id: str
    pdf_url: Optional[str]
    docx_url: Optional[str]
    created_at: str
    job_title: Optional[str]
    company_name: Optional[str]


class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total: int


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


@router.post("/generate-options")
async def generate_resume_options(
    request: GenerateResumeOptionsRequest,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Generate 2 resume options with automatically selected templates.

    This endpoint:
    1. Scrapes the job posting
    2. Analyzes the job to select the 2 best-matching templates
    3. Generates resume content once with AI
    4. Creates 2 PDFs with different templates
    5. Returns both options with justifications for the user to choose
    """
    try:
        # Get user's LinkedIn profile
        profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="LinkedIn profile not found. Please log in again.")

        # STEP 1: Scrape job posting
        print(f"Scraping job from: {request.job_url}")
        job_data = scrape_linkedin_job(str(request.job_url))

        if not job_data:
            raise HTTPException(status_code=400, detail="Failed to scrape job posting")

        # STEP 2: Select 2 best templates for this job
        print(f"\n🎯 Selecting best templates for: {job_data.get('title')} at {job_data.get('company')}")
        selected_templates = select_templates_for_job(job_data, num_templates=2)

        if len(selected_templates) < 2:
            raise HTTPException(
                status_code=500,
                detail="Not enough custom templates available. Please add more .docx templates to /teamplate directory."
            )

        print(f"✅ Selected {len(selected_templates)} templates:")
        for i, sel in enumerate(selected_templates, 1):
            print(f"   {i}. {sel['template']['name']} (score: {sel['score']})")

        # STEP 3: Prepare LinkedIn profile data
        raw_data = profile.raw_data or {}
        linkedin_data = {
            "full_name": raw_data.get("name", profile.headline or ""),
            "email": raw_data.get("email"),
            "phone": raw_data.get("phone"),
            "location": raw_data.get("location"),
            "headline": profile.headline,
            "summary": profile.summary,
            "experiences": profile.experiences or [],
            "education": profile.education or [],
            "skills": profile.skills or [],
            "certifications": profile.certifications or [],
            "photo_url": raw_data.get("photo_url", "") if request.use_profile_picture else "",
            "profile_image_url": raw_data.get("profile_image_url", "") if request.use_profile_picture else "",
            "additional_links": request.additional_links or []
        }

        # STEP 4: Generate resume content ONCE with AI (expensive operation)
        print("\n🤖 Generating resume content with Multi-Agent AI System...")
        resume_content = generate_intelligent_resume(
            profile_data=linkedin_data,
            job_data=job_data
        )

        if not resume_content:
            raise HTTPException(status_code=500, detail="Failed to generate resume content")

        # Ensure resumes directory exists
        os.makedirs("/app/resumes", exist_ok=True)

        # STEP 5: Generate 2 PDFs with different templates
        options = []
        template_handler = TemplateHandler()

        for i, selection in enumerate(selected_templates, 1):
            template = selection['template']
            template_id = template['id']
            template_path = template['path']

            print(f"\n📄 Generating resume {i}/2 with template: {template['name']}")

            # Generate unique filenames
            pdf_filename = f"resume_option_{i}_{user.id}_{template_id}.pdf"
            docx_filename = f"resume_option_{i}_{user.id}_{template_id}.docx"
            pdf_path = f"/app/resumes/{pdf_filename}"
            docx_path = f"/app/resumes/{docx_filename}"

            # Fill template with resume data
            try:
                # Debug: Print company names before PDF generation
                print(f"\n🔍 DEBUG - Company names in resume_content:")
                for idx, exp in enumerate(resume_content.get('work_experience', [])):
                    print(f"   Experience {idx + 1}: {exp.get('company')} | {exp.get('start_date')} - {exp.get('end_date')}")

                template_handler.fill_template(
                    template_path=template_path,
                    resume_data=resume_content,
                    output_path=docx_path
                )

                # Generate PDF using the SAME template logic
                # Note: PDF generator still uses "modern" style but applies resume data correctly
                generate_resume_pdf(
                    resume_data=resume_content,
                    output_path=pdf_path,
                    template="modern"  # All PDFs use modern styling for consistency
                )

                pdf_url = f"{settings.BACKEND_URL}/resumes/{pdf_filename}"
                docx_url = f"{settings.BACKEND_URL}/resumes/{docx_filename}"

                options.append({
                    "option_id": i,
                    "template_id": template_id,
                    "template_name": template['name'],
                    "template_type": template['type'],
                    "score": selection['score'],
                    "justification": selection['justification'],
                    "pdf_preview_url": pdf_url,
                    "docx_url": docx_url
                })

                print(f"✅ Option {i} generated successfully")

            except Exception as e:
                print(f"❌ Error generating option {i}: {str(e)}")
                continue

        if not options:
            raise HTTPException(status_code=500, detail="Failed to generate any resume options")

        # Return both options
        return {
            "options": options,
            "job_title": job_data.get("title"),
            "company": job_data.get("company"),
            "message": "Choose the resume template that best represents your professional profile"
        }

    except Exception as e:
        print(f"Error generating resume options: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate resume options: {str(e)}")


@router.post("/generate", response_model=ResumeResponse)
async def generate_resume(
    request: GenerateResumeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Generate a tailored resume from job URL

    Workflow:
    1. Scrape job posting
    2. Get user's LinkedIn profile from DB
    3. Generate resume content with OpenAI
    4. Create PDF with selected template
    5. Upload to S3 (optional)
    6. Save resume to DB
    """

    try:
        # Get user's LinkedIn profile
        profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="LinkedIn profile not found. Please log in again.")

        # STEP 1: Scrape job posting using Apify
        print(f"Scraping job from: {request.job_url}")
        job_data = scrape_linkedin_job(str(request.job_url))

        if not job_data:
            raise HTTPException(status_code=400, detail="Failed to scrape job posting")

        # Check if job already exists
        existing_job = db.query(JobPosting).filter(
            JobPosting.user_id == user.id,
            JobPosting.linkedin_job_id == job_data.get("job_id")
        ).first()

        if existing_job:
            # Update existing job
            job_posting = existing_job
            job_posting.job_title = job_data.get("title")
            job_posting.company_name = job_data.get("company")
            job_posting.location = job_data.get("location")
            job_posting.description = job_data.get("description")
            job_posting.employment_type = job_data.get("employment_type")
            job_posting.seniority_level = job_data.get("seniority_level")
            job_posting.is_remote = job_data.get("is_remote", False)
            job_posting.industries = job_data.get("industries")
            job_posting.parsed_skills = job_data.get("skills")
            job_posting.salary_min = job_data.get("salary_min")
            job_posting.salary_max = job_data.get("salary_max")
            job_posting.salary_currency = job_data.get("salary_currency")
            job_posting.application_url = job_data.get("application_url")
            job_posting.apify_data = job_data.get("raw_data")
            job_posting.last_scraped_at = datetime.utcnow()
        else:
            # Create new job posting
            job_posting = JobPosting(
                user_id=user.id,
                url=str(request.job_url),
                linkedin_job_id=job_data.get("job_id"),
                company_name=job_data.get("company"),
                job_title=job_data.get("title"),
                location=job_data.get("location"),
                description=job_data.get("description"),
                employment_type=job_data.get("employment_type"),
                seniority_level=job_data.get("seniority_level"),
                is_remote=job_data.get("is_remote", False),
                industries=job_data.get("industries"),
                parsed_skills=job_data.get("skills"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                salary_currency=job_data.get("salary_currency"),
                application_url=job_data.get("application_url"),
                apify_data=job_data.get("raw_data")
            )
            db.add(job_posting)

        db.commit()
        db.refresh(job_posting)

        # STEP 2: Prepare LinkedIn profile data for AI Multi-Agent System
        raw_data = profile.raw_data or {}
        linkedin_data = {
            "full_name": raw_data.get("name", profile.headline or ""),
            "email": raw_data.get("email"),
            "phone": raw_data.get("phone"),
            "location": raw_data.get("location"),
            "headline": profile.headline,
            "summary": profile.summary,
            "experiences": profile.experiences or [],
            "education": profile.education or [],
            "skills": profile.skills or [],
            "certifications": profile.certifications or [],
            "photo_url": raw_data.get("photo_url", "") if request.use_profile_picture else "",
            "profile_image_url": raw_data.get("profile_image_url", "") if request.use_profile_picture else "",
            "additional_links": request.additional_links or []
        }

        # STEP 3: Generate resume content with Multi-Agent AI System
        print("Generating resume with Multi-Agent AI System (5 specialized agents)...")
        resume_content = generate_intelligent_resume(
            profile_data=linkedin_data,
            job_data=job_data
        )

        if not resume_content:
            raise HTTPException(status_code=500, detail="Failed to generate resume content")

        # STEP 4: Generate PDF with advanced template
        print(f"Generating PDF with template: {request.template_id}")
        pdf_filename = f"resume_{user.id}_{job_posting.id}.pdf"
        pdf_full_path = f"/app/resumes/{pdf_filename}"

        # Ensure resumes directory exists
        os.makedirs("/app/resumes", exist_ok=True)

        # Generate PDF with professional template
        generate_resume_pdf(
            resume_data=resume_content,
            output_path=pdf_full_path,
            template=request.template_id
        )

        # URL to access the PDF (full backend URL for frontend)
        from ..core.config import settings
        pdf_url = f"{settings.BACKEND_URL}/resumes/{pdf_filename}"

        # STEP 4.5: Generate DOCX
        print(f"Generating DOCX with template: {request.template_id}")
        docx_filename = f"resume_{user.id}_{job_posting.id}.docx"
        docx_full_path = f"/app/resumes/{docx_filename}"

        try:
            generate_resume_docx(
                resume_data=resume_content,
                output_path=docx_full_path,
                template=request.template_id
            )
            docx_url = f"{settings.BACKEND_URL}/resumes/{docx_filename}"
            print(f"DOCX generated successfully: {docx_url}")
        except Exception as e:
            print(f"Warning: Failed to generate DOCX: {str(e)}")
            docx_url = None

        # STEP 5: Save resume to DB
        resume = Resume(
            user_id=user.id,
            job_posting_id=job_posting.id,
            template_id=request.template_id,
            generated_content=resume_content,
            pdf_url=pdf_url,
            docx_url=docx_url,
            openai_prompt=json.dumps(linkedin_data),  # For debugging
            openai_response=json.dumps(resume_content)
        )
        db.add(resume)

        # Update user's resume count
        user.resumes_generated_count = str(int(user.resumes_generated_count) + 1)

        db.commit()
        db.refresh(resume)

        return ResumeResponse(
            id=str(resume.id),
            template_id=resume.template_id,
            pdf_url=resume.pdf_url,
            docx_url=resume.docx_url,
            created_at=resume.created_at.isoformat(),
            job_title=job_posting.job_title,
            company_name=job_posting.company_name
        )

    except Exception as e:
        print(f"Error generating resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate resume: {str(e)}")


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all resumes for current user"""
    resumes = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.created_at.desc()).all()

    resume_list = []
    for resume in resumes:
        job = db.query(JobPosting).filter(JobPosting.id == resume.job_posting_id).first()
        resume_list.append(ResumeResponse(
            id=str(resume.id),
            template_id=resume.template_id,
            pdf_url=resume.pdf_url,
            docx_url=resume.docx_url,
            created_at=resume.created_at.isoformat(),
            job_title=job.job_title if job else None,
            company_name=job.company_name if job else None
        ))

    return ResumeListResponse(
        resumes=resume_list,
        total=len(resume_list)
    )


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get specific resume details"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = db.query(JobPosting).filter(JobPosting.id == resume.job_posting_id).first()

    return {
        "id": str(resume.id),
        "template_id": resume.template_id,
        "content": resume.generated_content,
        "pdf_url": resume.pdf_url,
        "docx_url": resume.docx_url,
        "created_at": resume.created_at.isoformat(),
        "job": {
            "title": job.job_title if job else None,
            "company": job.company_name if job else None,
            "url": job.url if job else None
        }
    }


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    format: str = "pdf",
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Download resume as PDF or DOCX"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if format == "pdf":
        file_url = resume.pdf_url
    elif format == "docx":
        file_url = resume.docx_url
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'docx'")

    if not file_url:
        raise HTTPException(status_code=404, detail=f"{format.upper()} not available")

    # Extract filename from URL (e.g., /resumes/resume_xxx.pdf -> /app/resumes/resume_xxx.pdf)
    filename = file_url.split('/')[-1]
    file_path = f"/app/resumes/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=file_path,
        media_type='application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=filename
    )


@router.get("/templates/list")
async def list_templates():
    """List available resume templates (both built-in and custom DOCX templates)"""

    # Built-in templates
    built_in_templates = [
        {
            "id": "modern",
            "name": "Modern",
            "description": "Clean and contemporary design with ATS optimization",
            "type": "built-in",
            "preview_url": "/static/templates/modern-preview.png"
        },
        {
            "id": "classic",
            "name": "Classic",
            "description": "Traditional professional layout",
            "type": "built-in",
            "preview_url": "/static/templates/classic-preview.png"
        },
        {
            "id": "technical",
            "name": "Technical",
            "description": "Optimized for tech roles with skills emphasis",
            "type": "built-in",
            "preview_url": "/static/templates/technical-preview.png"
        }
    ]

    # Scan custom DOCX templates
    custom_templates = []
    try:
        docx_templates = get_available_templates()
        for template in docx_templates:
            custom_templates.append({
                "id": template['id'],
                "name": template['name'],
                "description": f"{template['type'].title()} template",
                "type": "custom",
                "template_type": template['type'],
                "preview_url": f"/static/templates/{template['id']}-preview.png"
            })
    except Exception as e:
        print(f"Warning: Could not load custom templates: {e}")

    all_templates = built_in_templates + custom_templates

    return {
        "templates": all_templates,
        "total": len(all_templates),
        "built_in_count": len(built_in_templates),
        "custom_count": len(custom_templates)
    }


@router.get("/templates/analyze/{template_id}")
async def analyze_template(template_id: str):
    """
    Analyze a custom DOCX template to see its structure.

    Args:
        template_id: Template identifier

    Returns:
        Template analysis with placeholders, styles, and structure
    """
    try:
        templates = get_available_templates()

        # Find the template
        template = next((t for t in templates if t['id'] == template_id), None)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Analyze the template
        analysis = analyze_template_file(template['path'])

        return {
            "id": template_id,
            "name": template['name'],
            "type": template['type'],
            "path": template['path'],
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze template: {str(e)}")
