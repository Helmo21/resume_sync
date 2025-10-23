"""
AI-Powered CV Generation Service

This service uses a multi-agent AI system with LangChain to generate
intelligent, tailored, ATS-friendly resumes by matching user profiles
with job requirements.
"""

import requests
import json
from typing import Dict, List, Optional
from ..core.config import settings
from .ai_resume_agent import MultiAgentResumeGenerator


class CVGenerator:
    """
    AI-powered CV generator that matches user profiles with job postings.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, use_multi_agent: bool = True):
        """
        Initialize CV Generator with API credentials.

        Args:
            api_key: OpenRouter API key (defaults to settings.OPENROUTER_API_KEY)
            model: Model to use (defaults to settings.OPENROUTER_MODEL)
            use_multi_agent: Use multi-agent system (default True, recommended)
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.use_multi_agent = use_multi_agent

        if not self.api_key:
            raise ValueError("OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable.")

        # Initialize multi-agent system if enabled
        if self.use_multi_agent:
            try:
                self.multi_agent_generator = MultiAgentResumeGenerator(
                    api_key=self.api_key,
                    model=self.model
                )
                print("Multi-agent system initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize multi-agent system: {e}")
                print("Falling back to legacy single-prompt generation")
                self.use_multi_agent = False

    def generate_resume(
        self,
        profile_data: Dict,
        job_data: Dict,
        template_style: str = "modern"
    ) -> Dict:
        """
        Generate an ATS-friendly resume matching the profile to the job.

        Uses multi-agent system by default for intelligent, tailored resume generation.
        Falls back to legacy single-prompt generation if multi-agent fails.

        Args:
            profile_data: User's LinkedIn profile data (experiences, education, skills)
            job_data: Job posting data (description, requirements, skills)
            template_style: Resume template style (modern, classic, technical)

        Returns:
            dict: Generated resume content with sections
        """
        # Try multi-agent system first
        if self.use_multi_agent:
            try:
                print("Using multi-agent system for resume generation...")
                resume_content = self.multi_agent_generator.generate_resume(
                    profile_data,
                    job_data
                )
                return resume_content
            except Exception as e:
                print(f"Multi-agent generation failed: {e}")
                print("Falling back to legacy single-prompt generation...")

        # Fallback: Legacy single-prompt generation
        return self._generate_resume_legacy(profile_data, job_data, template_style)

    def _generate_resume_legacy(
        self,
        profile_data: Dict,
        job_data: Dict,
        template_style: str = "modern"
    ) -> Dict:
        """
        Legacy single-prompt resume generation (fallback).

        Args:
            profile_data: User's LinkedIn profile data
            job_data: Job posting data
            template_style: Resume template style

        Returns:
            dict: Generated resume content
        """
        # Build the prompt for AI
        prompt = self._build_prompt(profile_data, job_data, template_style)

        # Call OpenRouter API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.BACKEND_URL,
            "X-Title": "ResumeSync"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert resume writer specializing in ATS-optimized resumes. You excel at matching candidate profiles to job requirements while maintaining authenticity and highlighting relevant achievements."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        print(f"Calling OpenRouter AI with model: {self.model}")
        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        ai_response = result["choices"][0]["message"]["content"]

        # Parse AI response into structured resume
        resume_content = self._parse_ai_response(ai_response, profile_data, job_data)

        return resume_content

    def _build_prompt(self, profile_data: Dict, job_data: Dict, template_style: str) -> str:
        """
        Build the AI prompt for resume generation.

        Args:
            profile_data: User profile data
            job_data: Job posting data
            template_style: Template style

        Returns:
            str: Formatted prompt
        """
        # Extract profile information
        full_name = profile_data.get("full_name", "")
        email = profile_data.get("email", "")
        headline = profile_data.get("headline", "")
        summary = profile_data.get("summary", "")
        experiences = profile_data.get("experiences", [])
        education = profile_data.get("education", [])
        skills = profile_data.get("skills", [])

        # Extract job information
        job_title = job_data.get("title", "")
        company = job_data.get("company", "")
        job_description = job_data.get("description", "")
        required_skills = job_data.get("skills", [])
        seniority_level = job_data.get("seniority_level", "")

        prompt = f"""Generate an ATS-optimized resume for the following candidate applying to a specific job.

**CANDIDATE PROFILE:**
Name: {full_name}
Email: {email}
Professional Headline: {headline}

Summary:
{summary}

Work Experience:
{json.dumps(experiences, indent=2)}

Education:
{json.dumps(education, indent=2)}

Skills:
{", ".join(skills) if isinstance(skills, list) else skills}

**TARGET JOB:**
Job Title: {job_title}
Company: {company}
Seniority Level: {seniority_level}

Job Description:
{job_description}

Required Skills (from job posting):
{", ".join(required_skills) if isinstance(required_skills, list) else required_skills}

**INSTRUCTIONS:**
1. Create a resume that is highly optimized for Applicant Tracking Systems (ATS)
2. Match the candidate's experience and skills to the job requirements
3. Emphasize relevant achievements and quantifiable results
4. Use keywords from the job description naturally throughout the resume
5. Reorganize and prioritize experiences to highlight the most relevant ones for this role
6. Keep the professional summary concise (3-4 lines) and tailored to the job
7. Only include skills that match the job requirements or are highly relevant
8. Use action verbs and concrete achievements
9. Format: {template_style} style

**OUTPUT FORMAT (JSON):**
Return the resume as a JSON object with the following structure:
{{
  "personal_info": {{
    "full_name": "...",
    "email": "...",
    "phone": "...",
    "location": "...",
    "linkedin": "..."
  }},
  "professional_summary": "...",
  "work_experience": [
    {{
      "title": "...",
      "company": "...",
      "location": "...",
      "start_date": "...",
      "end_date": "...",
      "achievements": [
        "Quantifiable achievement 1",
        "Quantifiable achievement 2",
        "..."
      ]
    }}
  ],
  "education": [
    {{
      "degree": "...",
      "school": "...",
      "field": "...",
      "graduation_date": "...",
      "gpa": "..." (optional),
      "honors": "..." (optional)
    }}
  ],
  "skills": {{
    "technical": ["skill1", "skill2", ...],
    "soft": ["skill1", "skill2", ...],
    "tools": ["tool1", "tool2", ...]
  }},
  "certifications": [
    {{
      "name": "...",
      "authority": "...",
      "date": "..."
    }}
  ]
}}

Return ONLY the JSON object, no additional text.
"""
        return prompt

    def _parse_ai_response(self, ai_response: str, profile_data: Dict, job_data: Dict) -> Dict:
        """
        Parse AI response into structured resume content.

        Args:
            ai_response: Raw AI response
            profile_data: Original profile data (fallback)
            job_data: Job data

        Returns:
            dict: Structured resume content
        """
        try:
            # Try to extract JSON from the response
            # Sometimes AI wraps JSON in markdown code blocks
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            elif "```" in ai_response:
                json_start = ai_response.find("```") + 3
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response.strip()

            resume_content = json.loads(json_str)

            # Validate and ensure all required fields exist
            if "personal_info" not in resume_content:
                resume_content["personal_info"] = {
                    "full_name": profile_data.get("full_name", ""),
                    "email": profile_data.get("email", ""),
                    "phone": profile_data.get("phone", ""),
                    "location": profile_data.get("location", "")
                }

            if "professional_summary" not in resume_content:
                resume_content["professional_summary"] = profile_data.get("summary", "")

            if "work_experience" not in resume_content:
                resume_content["work_experience"] = profile_data.get("experiences", [])

            if "education" not in resume_content:
                resume_content["education"] = profile_data.get("education", [])

            if "skills" not in resume_content:
                resume_content["skills"] = {
                    "technical": profile_data.get("skills", []),
                    "soft": [],
                    "tools": []
                }

            return resume_content

        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            print(f"AI Response: {ai_response}")

            # Fallback: return structured profile data
            return {
                "personal_info": {
                    "full_name": profile_data.get("full_name", ""),
                    "email": profile_data.get("email", ""),
                    "phone": profile_data.get("phone", ""),
                    "location": profile_data.get("location", "")
                },
                "professional_summary": profile_data.get("summary", ""),
                "work_experience": profile_data.get("experiences", []),
                "education": profile_data.get("education", []),
                "skills": {
                    "technical": profile_data.get("skills", []),
                    "soft": [],
                    "tools": []
                },
                "certifications": profile_data.get("certifications", [])
            }

    def analyze_match_score(self, profile_data: Dict, job_data: Dict) -> Dict:
        """
        Analyze how well the profile matches the job requirements.

        Args:
            profile_data: User profile data
            job_data: Job posting data

        Returns:
            dict: Match analysis with score and recommendations
        """
        # Extract skills from both
        profile_skills = set(str(s).lower() for s in profile_data.get("skills", []))
        job_skills = set(str(s).lower() for s in job_data.get("skills", []))

        # Calculate skill match
        matching_skills = profile_skills.intersection(job_skills)
        skill_match_score = len(matching_skills) / len(job_skills) * 100 if job_skills else 0

        missing_skills = job_skills - profile_skills

        return {
            "overall_score": round(skill_match_score, 2),
            "matching_skills": list(matching_skills),
            "missing_skills": list(missing_skills),
            "recommendations": self._generate_recommendations(skill_match_score, missing_skills)
        }

    def _generate_recommendations(self, score: float, missing_skills: set) -> List[str]:
        """Generate recommendations based on match score."""
        recommendations = []

        if score < 50:
            recommendations.append("Consider gaining experience in the missing key skills")
            recommendations.append("Highlight transferable skills in your application")
        elif score < 75:
            recommendations.append("You have a good foundation - emphasize your matching skills")
            recommendations.append("Consider mentioning willingness to learn missing skills")
        else:
            recommendations.append("Excellent match! Focus on showcasing your relevant achievements")

        if missing_skills:
            recommendations.append(f"Consider learning: {', '.join(list(missing_skills)[:3])}")

        return recommendations


def generate_tailored_resume(
    profile_data: Dict,
    job_data: Dict,
    template_style: str = "modern"
) -> Dict:
    """
    Convenience function to generate a tailored resume.

    Args:
        profile_data: User profile data
        job_data: Job posting data
        template_style: Template style

    Returns:
        dict: Generated resume content
    """
    generator = CVGenerator()
    return generator.generate_resume(profile_data, job_data, template_style)
