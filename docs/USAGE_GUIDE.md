# Multi-Agent Resume Generation - Usage Guide

## Quick Start

### Basic Usage

```python
from app.services.cv_generator import CVGenerator
from app.services.document_generator import ATSTemplateGenerator

# 1. Initialize the generator
generator = CVGenerator(use_multi_agent=True)

# 2. Prepare your data
profile_data = {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-234-567-8900",
    "location": "New York, USA",
    "headline": "Software Engineer",
    "summary": "...",
    "experiences": [...],
    "education": [...],
    "skills": [...]
}

job_data = {
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "description": "...",
    "skills": [...]
}

# 3. Generate the resume
resume_content = generator.generate_resume(profile_data, job_data)

# 4. Access the results
print(f"Professional Summary: {resume_content['professional_summary']}")
print(f"Match Score: {resume_content['match_score']}%")

# 5. Generate DOCX file
doc_generator = ATSTemplateGenerator()
doc_generator.generate_docx(resume_content, "output.docx")
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# OpenRouter API (required)
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Application URLs (for API headers)
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### Custom Configuration

```python
# Use specific model
generator = CVGenerator(
    api_key="your_key",
    model="anthropic/claude-3.5-sonnet",
    use_multi_agent=True
)

# Disable multi-agent (use legacy system)
generator = CVGenerator(use_multi_agent=False)
```

## Data Format

### Profile Data Structure

```python
profile_data = {
    # Required fields
    "full_name": "John Doe",
    "email": "john@example.com",

    # Optional but recommended
    "phone": "+1-234-567-8900",
    "location": "New York, USA",
    "profile_url": "https://linkedin.com/in/johndoe",
    "headline": "Software Engineer | Python | React",
    "summary": "Passionate developer with 5 years...",

    # Experiences (list)
    "experiences": [
        {
            "title": "Senior Developer",
            "company": "Tech Corp",
            "location": "New York, USA",
            "start_date": "2022-01",
            "end_date": "Present",  # or "2024-12"
            "description": "Led development of...",
            "achievements": [
                "Increased performance by 40%",
                "Mentored 3 junior developers"
            ]
        }
    ],

    # Education (list)
    "education": [
        {
            "degree": "Bachelor of Science",
            "school": "University of Technology",
            "field": "Computer Science",
            "graduation_date": "2020",
            "gpa": "3.8/4.0"  # optional
        }
    ],

    # Skills (list)
    "skills": [
        "Python", "JavaScript", "React", "Node.js",
        "PostgreSQL", "Docker", "AWS"
    ],

    # Certifications (optional, list)
    "certifications": [
        {
            "name": "AWS Certified Developer",
            "authority": "Amazon Web Services",
            "date": "2023-06"
        }
    ]
}
```

### Job Data Structure

```python
job_data = {
    # Required fields
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "description": """
    Full job description text here.
    Include responsibilities, requirements, etc.
    """,

    # Optional but recommended
    "location": "New York, USA",
    "seniority_level": "Mid-Senior level",

    # Skills (list) - extracted from description or provided
    "skills": [
        "Python", "JavaScript", "React", "Docker", "AWS"
    ]
}
```

## Output Format

The `generate_resume()` method returns:

```python
{
    # Personal information
    "personal_info": {
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-234-567-8900",
        "location": "New York, USA",
        "linkedin": "https://linkedin.com/in/johndoe"
    },

    # AI-generated professional summary
    "professional_summary": "Dynamic Software Engineer with...",

    # Selected and enhanced experiences
    "work_experience": [
        {
            "title": "Senior Developer",
            "company": "Tech Corp",
            "location": "New York, USA",
            "start_date": "2022-01",
            "end_date": "Present",
            "achievements": [
                "Enhanced achievement 1",
                "Enhanced achievement 2"
            ],
            "original_index": 0  # reference to original
        }
    ],

    # Selected education
    "education": [
        {
            "degree": "Bachelor of Science",
            "school": "University of Technology",
            "field": "Computer Science",
            "graduation_date": "2020"
        }
    ],

    # Prioritized skills
    "skills": {
        "technical": ["Python", "JavaScript", "React", ...],
        "soft": [],  # if any identified
        "tools": []  # if any identified
    },

    # Certifications
    "certifications": [...],

    # Match analysis
    "match_score": 85.0,  # 0-100%

    # Generation metadata
    "generation_metadata": {
        "generated_at": "2025-10-16T16:41:07",
        "model": "anthropic/claude-3.5-sonnet",
        "iterations": 2,
        "quality_score": 85.0
    }
}
```

## Document Generation

### Generate DOCX (Custom Template)

```python
from app.services.document_generator import ATSTemplateGenerator

generator = ATSTemplateGenerator()

# Modern template (default)
generator.generate_docx(resume_content, "resume_modern.docx", template="modern")

# Classic template
generator.generate_docx(resume_content, "resume_classic.docx", template="classic")

# Technical template
generator.generate_docx(resume_content, "resume_tech.docx", template="technical")
```

### Generate DOCX (Pre-made Template)

```python
# Use pre-made template from /teamplate/ directory
generator.generate_docx(
    resume_content,
    "resume.docx",
    template="sales",  # or "accounting", "attorney", "office_manager"
    use_template_file=True
)
```

### Generate PDF

```python
# Generate PDF instead of DOCX
generator.generate_pdf(resume_content, "resume.pdf", template="modern")
```

## Error Handling

```python
try:
    resume_content = generator.generate_resume(profile_data, job_data)
    print(f"Success! Match score: {resume_content['match_score']}%")
except ValueError as e:
    print(f"Invalid data: {e}")
except Exception as e:
    print(f"Generation failed: {e}")
    # Multi-agent system will automatically fallback to legacy
```

## Advanced Usage

### Access Individual Agent Results

The multi-agent system runs 5 agents sequentially. You can access intermediate results:

```python
from app.services.ai_resume_agent import MultiAgentResumeGenerator

generator = MultiAgentResumeGenerator()

# Each agent can be called individually if needed
profile_analysis = generator.profile_analyzer.analyze(profile_data)
print(f"Career level: {profile_analysis.career_level}")
print(f"Years of experience: {profile_analysis.years_of_experience}")
```

### Custom Iteration Limit

```python
# Allow more reviewer iterations
resume_content = generator.generate_resume(
    profile_data,
    job_data,
    max_iterations=3  # default is 2
)
```

### Disable Multi-Agent System

```python
# Fall back to legacy single-prompt generation
generator = CVGenerator(use_multi_agent=False)
resume_content = generator.generate_resume(profile_data, job_data)
```

## Testing

Run the test script:

```bash
cd /home/antoine/Documents/dev/ResumeSync/backend
python3 test_multiagent.py
```

Expected output:
- All 5 agents execute successfully
- Professional summary generated
- Match score calculated (0-100%)
- DOCX file created in /tmp/

## Troubleshooting

### Issue: "OpenRouter API key not provided"

**Solution**: Set `OPENROUTER_API_KEY` in `.env` file

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### Issue: "Multi-agent generation failed: ..."

**Solution**: System automatically falls back to legacy. Check:
1. API key is valid
2. Internet connection works
3. OpenRouter service is up

### Issue: "Module not found: langchain"

**Solution**: Install dependencies

```bash
pip install -r requirements.txt
```

### Issue: Resume not fitting on 1 page

**Solution**: The system estimates word count but actual fit depends on:
1. Font size in template
2. Margins in template
3. Spacing settings

Adjust template or regenerate with fewer experiences/skills.

### Issue: Match score is low

**Solution**: Low score (< 50%) means:
1. Profile skills don't match job requirements
2. Experience is not relevant to the role
3. Candidate might not be suitable for this job

This is expected behavior - the system is being honest about fit.

## Best Practices

### 1. Complete Profile Data

Provide as much data as possible for best results:
- Full experiences with achievements
- Complete skill list
- Detailed education information

### 2. Detailed Job Descriptions

Better job descriptions = better matching:
- Include full job requirements
- List required and preferred skills
- Mention key responsibilities

### 3. Review Generated Content

Always review the AI-generated content:
- Check for accuracy
- Verify dates and companies
- Ensure tone matches your brand

### 4. Iterate if Needed

If first result isn't perfect:
- Adjust profile data (add missing skills/experiences)
- Try different job descriptions
- Use reviewer suggestions to improve

### 5. Use Appropriate Template

Choose template based on job type:
- `sales`: Sales, marketing, business roles
- `accounting`: Finance, accounting roles
- `attorney`: Legal roles
- `office_manager`: Administrative roles
- `modern`: Tech, creative roles
- `classic`: Traditional corporate roles
- `technical`: Engineering, developer roles

## API Integration Example

```python
from fastapi import FastAPI, HTTPException
from app.services.cv_generator import CVGenerator
from app.services.document_generator import ATSTemplateGenerator

app = FastAPI()

@app.post("/api/generate-resume")
async def generate_resume(profile_data: dict, job_data: dict):
    try:
        # Generate resume content
        generator = CVGenerator(use_multi_agent=True)
        resume_content = generator.generate_resume(profile_data, job_data)

        # Generate DOCX file
        output_path = f"/tmp/resume_{profile_data['full_name']}.docx"
        doc_generator = ATSTemplateGenerator()
        doc_generator.generate_docx(resume_content, output_path)

        return {
            "success": True,
            "match_score": resume_content["match_score"],
            "file_path": output_path,
            "summary": resume_content["professional_summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Performance Tips

### 1. Cache Profile Analysis

If generating multiple resumes for same profile:

```python
# Cache profile analysis to avoid re-analyzing
profile_analysis = generator.profile_analyzer.analyze(profile_data)
# Use cached analysis for multiple jobs
```

### 2. Batch Processing

For multiple candidates:

```python
import asyncio

async def generate_batch(candidates, job_data):
    tasks = []
    for profile_data in candidates:
        task = generate_resume_async(profile_data, job_data)
        tasks.append(task)
    return await asyncio.gather(*tasks)
```

### 3. Reduce API Calls

- Use `max_iterations=1` for reviewer
- Cache analyses when possible
- Fall back to legacy for less critical resumes

## Support

For issues or questions:
1. Check `/backend/MULTIAGENT_IMPLEMENTATION.md` for technical details
2. Review test script: `/backend/test_multiagent.py`
3. Check logs for detailed error messages

## License

Part of ResumeSync project.
