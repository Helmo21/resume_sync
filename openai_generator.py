"""
OpenRouter Resume Generator
Uses various AI models via OpenRouter to generate tailored resumes based on LinkedIn profile and job posting
"""

import os
import json
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_resume_prompt(linkedin_profile: Dict, job_posting: Dict) -> str:
    """Create the prompt for OpenAI to generate a tailored resume."""

    prompt = f"""You are an expert resume writer and ATS optimization specialist. Your task is to create a highly tailored, professional resume based STRICTLY on the candidate's ACTUAL LinkedIn profile.

CANDIDATE'S LINKEDIN PROFILE:
{json.dumps(linkedin_profile, indent=2)}

TARGET JOB POSTING:
Company: {job_posting.get('company_name', 'N/A')}
Title: {job_posting.get('job_title', 'N/A')}
Location: {job_posting.get('location', 'N/A')}

Job Description:
{job_posting.get('description', 'N/A')}

CRITICAL INSTRUCTIONS - READ CAREFULLY:

🚫 NEVER DO THIS:
- DO NOT invent or fabricate any experiences, projects, or achievements
- DO NOT add companies, positions, or education that are not in the profile
- DO NOT create generic content - every line must be traceable to the actual profile
- DO NOT change company names, job titles, or dates from the original profile

✅ ALWAYS DO THIS:
1. **USE THE EXACT PROFILE AS THE FOUNDATION**:
   - EVERY experience must come directly from the "experiences" array in the profile
   - EVERY education entry must come from the "education" array
   - EVERY skill must be from the "skills" array or clearly demonstrated in experiences
   - Keep the SAME company names, job titles, locations, and date ranges

2. **TAILOR BY REWRITING, NOT REPLACING**:
   - Take each REAL experience and rewrite the bullet points to emphasize aspects relevant to the target job
   - Highlight accomplishments that match the job requirements
   - Use keywords from the job description naturally in the achievement descriptions
   - Quantify results when possible (but only if you can infer reasonable metrics from the profile)

3. **SUMMARY TAILORING**:
   - Create a professional summary that:
     * Reflects the candidate's ACTUAL career level and experience from the profile
     * Incorporates their real headline and summary
     * Emphasizes aspects of their background that match the target job
     * Uses keywords from the job posting naturally

4. **PRIORITIZE RELEVANCE**:
   - List the most relevant experiences FIRST (even if not chronologically first)
   - For each experience, write 3-5 achievement bullets that:
     * Are based on the actual job description/responsibilities from the profile
     * Emphasize aspects that match the target job requirements
     * Include keywords from the job posting naturally
     * Use strong action verbs (Led, Developed, Managed, Implemented, etc.)

5. **EDUCATION & SKILLS**:
   - List education EXACTLY as provided in the profile
   - For skills, prioritize those mentioned in the job posting (but only include skills the candidate actually has)
   - Organize skills by category if it helps (Technical Skills, Languages, Tools, etc.)

6. **ATS OPTIMIZATION**:
   - Use standard section headers (Summary, Experience, Education, Skills)
   - Include keywords from job description naturally throughout
   - Use standard date formats (MM/YYYY)
   - Use bullet points, not paragraphs

EXAMPLE OF CORRECT TAILORING:

Original Profile Experience:
- Company: ABC Corp
- Title: Software Engineer
- Description: "Worked on web applications"

Job Requirement: "React developer for e-commerce platform"

❌ WRONG (inventing new experience):
"Developed e-commerce checkout system for 10M users with React and Redux"

✅ CORRECT (tailoring actual experience):
"Developed and maintained web applications using modern frameworks, focusing on user experience and performance optimization"

OUTPUT FORMAT:
Return ONLY a valid JSON object with this EXACT structure:
{{
  "contact": {{
    "name": "{linkedin_profile.get('full_name', 'N/A')}",
    "email": "{linkedin_profile.get('email', 'N/A')}",
    "phone": "{linkedin_profile.get('phone', 'null')}",
    "location": "{linkedin_profile.get('location', 'N/A')}",
    "linkedin": "null"
  }},
  "summary": "2-3 sentence professional summary based on candidate's ACTUAL background, tailored to target job",
  "experience": [
    {{
      "title": "EXACT title from profile",
      "company": "EXACT company from profile",
      "location": "EXACT location from profile or null",
      "start_date": "EXACT start date from profile (MM/YYYY)",
      "end_date": "EXACT end date from profile (MM/YYYY or Present)",
      "achievements": [
        "Achievement rewritten to emphasize job-relevant aspects (based on actual experience)",
        "Another achievement with keywords from job description (based on actual experience)",
        "Third achievement quantified if possible (based on actual experience)"
      ]
    }}
  ],
  "education": [
    {{
      "degree": "EXACT degree from profile",
      "school": "EXACT school from profile",
      "graduation_year": "EXACT year from profile or null",
      "gpa": "GPA from profile or null"
    }}
  ],
  "skills": [
    "Actual skill from profile (prioritized if in job description)",
    "Another actual skill (prioritized if in job description)",
    "..."
  ]
}}

REMEMBER:
- Your job is to TAILOR the EXISTING profile, not create a new one
- Every single piece of information must be traceable back to the LinkedIn profile provided
- The resume should read like "this person's actual background, presented in the best light for this specific job"
- Think: "How can I present THIS person's REAL experience to best match THIS job?"

Generate the tailored resume now (JSON only, no explanations):"""

    return prompt


def generate_resume(linkedin_profile: Dict, job_posting: Dict) -> Dict:
    """
    Use OpenRouter to generate a tailored resume.
    Returns the resume as a structured JSON object.
    """
    print("\n" + "="*80)
    print("STEP 3: GENERATE TAILORED RESUME")
    print("="*80)

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")  # Default to Claude 3.5 Sonnet

    if not api_key:
        print("\n❌ Error: OPENROUTER_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenRouter API key")
        print("Example: OPENROUTER_API_KEY=sk-or-v1-...")
        raise ValueError("Missing OPENROUTER_API_KEY")

    print(f"\n⏳ Generating tailored resume with {model}...")
    print("   This may take 10-30 seconds...")

    try:
        # Initialize OpenAI client with OpenRouter base URL
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        # Create the prompt
        prompt = create_resume_prompt(linkedin_profile, job_posting)

        # Call OpenRouter API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer specializing in ATS optimization and tailored job applications. You NEVER invent or fabricate experiences - you only work with the candidate's ACTUAL profile data and tailor the presentation to match specific job requirements. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,  # Lower temperature for more consistent, fact-based output
            max_tokens=3000,
        )

        # Extract the generated resume
        resume_json = response.choices[0].message.content

        # Clean up response if it contains markdown code blocks
        if "```json" in resume_json:
            resume_json = resume_json.split("```json")[1].split("```")[0].strip()
        elif "```" in resume_json:
            resume_json = resume_json.split("```")[1].split("```")[0].strip()

        resume_data = json.loads(resume_json)

        print("\n✓ Resume generated successfully!")
        if hasattr(response, 'usage') and response.usage:
            print(f"   Tokens used: {response.usage.total_tokens}")

        return resume_data

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Model returned invalid JSON")
        print(f"   Details: {e}")
        print(f"   Response: {resume_json[:200]}...")
        raise

    except Exception as e:
        print(f"\n❌ Error generating resume: {e}")
        raise


def save_resume_json(resume_data: Dict, filename: str = "generated_resume.json"):
    """Save generated resume to JSON file."""
    with open(filename, 'w') as f:
        json.dump(resume_data, f, indent=2)
    print(f"\n✓ Resume data saved to {filename}")


if __name__ == "__main__":
    # Test with sample data
    print("Testing OpenAI Resume Generator...")

    sample_profile = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "headline": "Software Engineer",
        "summary": "Experienced software engineer with 5 years in web development",
        "experiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "description": "Built web applications using React and Python"
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "school": "University of Technology",
                "graduation_year": "2019"
            }
        ],
        "skills": ["Python", "React", "JavaScript", "AWS"]
    }

    sample_job = {
        "company_name": "Google",
        "job_title": "Senior Software Engineer",
        "description": "Looking for a senior engineer with Python and React experience..."
    }

    resume = generate_resume(sample_profile, sample_job)
    print("\n" + "="*80)
    print("GENERATED RESUME:")
    print("="*80)
    print(json.dumps(resume, indent=2))
