"""
AI Resume Analyzer Service
Analyzes uploaded resume text to extract searchable metadata for job matching.
"""
import json
from typing import Dict, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..core.config import settings


class ResumeAnalysisResult(BaseModel):
    """Structured output from resume analysis"""

    # Skills
    technical_skills: List[str] = Field(
        description="Technical skills (programming languages, frameworks, tools)"
    )
    soft_skills: List[str] = Field(
        description="Soft skills (leadership, communication, etc.)"
    )

    # Experience
    job_titles: List[str] = Field(
        description="Job titles/roles held (current and past)"
    )
    years_of_experience: int = Field(
        description="Total years of professional experience"
    )
    seniority_level: str = Field(
        description="Career level: entry, junior, mid, senior, lead, principal, executive"
    )

    # Domain
    industries: List[str] = Field(
        description="Industries/domains of experience (e.g., fintech, healthcare, e-commerce)"
    )

    # Job Search Preferences (inferred from resume)
    preferred_languages: List[str] = Field(
        description="Preferred work languages based on resume language and location (e.g., English, French, Spanish)"
    )
    remote_preference: str = Field(
        description="Inferred remote work preference: remote, hybrid, on-site, or flexible"
    )

    # Key Responsibilities (for matching)
    key_responsibilities: List[str] = Field(
        description="Common types of responsibilities/projects (for matching to job descriptions)"
    )

    # Search Keywords
    search_keywords: List[str] = Field(
        description="20-30 keywords optimized for LinkedIn job search (mix of skills, roles, domains)"
    )


class ResumeAnalyzer:
    """AI-powered resume analyzer using LangChain and OpenRouter"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the resume analyzer.

        Args:
            api_key: OpenRouter API key (defaults to settings.OPENROUTER_API_KEY)
            model: Model to use (defaults to settings.OPENROUTER_MODEL)
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL

        # Initialize LLM with OpenRouter
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            model=self.model,
            temperature=0.3,  # Lower temperature for more consistent extraction
        )

        # Setup output parser
        self.parser = PydanticOutputParser(pydantic_object=ResumeAnalysisResult)

    def analyze_resume(self, resume_text: str) -> Dict:
        """
        Analyze uploaded resume text to extract structured metadata.

        Args:
            resume_text: Raw text extracted from resume

        Returns:
            Dictionary with analyzed data

        Raises:
            Exception: If analysis fails
        """
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume analyzer and career counselor.
Your task is to analyze the provided resume text and extract structured information
that will be used to match the candidate with relevant job opportunities on LinkedIn.

Be accurate and objective. Only extract information that is clearly present in the resume.
Do not make assumptions or add information that isn't there.

For preferred_languages: Infer from the resume language itself and any location/education info.
For remote_preference: Make an educated guess based on recent roles (if they mention "remote", "distributed team", etc.)

{format_instructions}"""),
            ("user", """Analyze this resume and extract all relevant information:

RESUME TEXT:
{resume_text}

Remember to:
1. Extract ALL technical skills mentioned (languages, frameworks, tools, technologies)
2. List ALL job titles/roles (current and past positions)
3. Accurately calculate years of experience from dates
4. Identify industries/domains from company types and project descriptions
5. Generate 20-30 search keywords that would help find matching jobs on LinkedIn
6. Infer language preferences from resume language and location
7. For remote_preference, use "flexible" if not clearly indicated
""")
        ])

        # Format prompt with instructions
        formatted_prompt = prompt.format_messages(
            resume_text=resume_text,
            format_instructions=self.parser.get_format_instructions()
        )

        try:
            # Call LLM
            response = self.llm.invoke(formatted_prompt)

            # Parse response
            result = self.parser.parse(response.content)

            # Convert to dict and add metadata
            analysis_dict = result.dict()
            analysis_dict["analyzed_at"] = datetime.utcnow().isoformat()
            analysis_dict["model_used"] = self.model

            return analysis_dict

        except Exception as e:
            raise Exception(f"Resume analysis failed: {str(e)}")

    def generate_search_query(self, analysis_data: Dict) -> str:
        """
        Generate optimized LinkedIn search query from analysis data.

        Args:
            analysis_data: Result from analyze_resume()

        Returns:
            Search query string
        """
        # Combine job titles and key skills for search
        job_titles = analysis_data.get("job_titles", [])[:3]  # Top 3 titles
        top_skills = analysis_data.get("technical_skills", [])[:5]  # Top 5 skills

        # Build search query
        query_parts = []

        if job_titles:
            query_parts.append(" OR ".join([f'"{title}"' for title in job_titles]))

        if top_skills:
            query_parts.extend(top_skills[:3])  # Add top 3 skills

        # Add keywords like "hiring", "we're hiring"
        search_keywords = " ".join(query_parts[:5])  # Limit to avoid too long query

        return search_keywords
