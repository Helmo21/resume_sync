"""
Multi-Agent AI System for Intelligent Resume Generation

This module implements a 5-agent system using LangChain for analyzing profiles,
matching them with job requirements, and generating tailored, ATS-optimized resumes.

Agents:
1. ProfileAnalyzer - Analyzes LinkedIn profile data
2. JobAnalyzer - Analyzes job posting requirements
3. MatchMaker - Matches profile to job and selects relevant content
4. ContentWriter - Generates tailored resume content
5. Reviewer - Validates quality and coherence
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..core.config import settings


# Pydantic models for structured outputs
class ProfileAnalysis(BaseModel):
    """Structured output from ProfileAnalyzer"""
    key_strengths: List[str] = Field(description="Top 5-7 key strengths and competencies")
    technical_skills: List[str] = Field(description="Technical skills identified")
    soft_skills: List[str] = Field(description="Soft skills identified")
    years_of_experience: int = Field(description="Total years of professional experience")
    career_level: str = Field(description="Career level: entry, mid, senior, lead, executive")
    domains: List[str] = Field(description="Professional domains/industries")


class JobAnalysis(BaseModel):
    """Structured output from JobAnalyzer"""
    required_skills: List[str] = Field(description="Skills explicitly required")
    preferred_skills: List[str] = Field(description="Skills that are nice-to-have")
    key_responsibilities: List[str] = Field(description="Main responsibilities of the role")
    qualifications: List[str] = Field(description="Required qualifications")
    ats_keywords: List[str] = Field(description="Important keywords for ATS optimization")
    seniority_level: str = Field(description="Required seniority level")


class ExperienceMatch(BaseModel):
    """Match score for a single experience"""
    experience_id: int = Field(description="Index of the experience")
    relevance_score: float = Field(description="Relevance score 0-100")
    matching_skills: List[str] = Field(description="Skills that match the job")
    reasons: List[str] = Field(description="Reasons for relevance")
    is_latest: bool = Field(description="Whether this is the latest experience")


class MatchAnalysis(BaseModel):
    """Structured output from MatchMaker"""
    overall_match_score: float = Field(description="Overall match percentage 0-100")
    selected_experiences: List[int] = Field(description="Indices of experiences to include")
    experience_matches: List[ExperienceMatch] = Field(description="Detailed match for each experience")
    selected_skills: List[str] = Field(description="Skills to include, prioritized by job match")
    selected_education: List[int] = Field(description="Indices of education to include")
    missing_skills: List[str] = Field(description="Skills required by job but not in profile")


class EnhancedContent(BaseModel):
    """Structured output from ContentWriter"""
    professional_summary: str = Field(description="2-3 SHORT sentence professional summary tailored to job, very impactful and quantified (MAXIMUM 2-3 sentences)")
    job_title_variants: List[str] = Field(description="3-4 job title variants/synonyms for ATS keyword matching (e.g., 'DevOps Engineer | Cloud Engineer | SRE | Platform Engineer')")
    enhanced_experiences: List[Dict[str, Any]] = Field(description="Enhanced experience descriptions with 2-4 CONCISE bullet points each (NOT paragraphs). Each experience should have 'title', 'company', 'dates', 'bullets' fields")
    skill_descriptions: Dict[str, Any] = Field(description="Enhanced skill descriptions (can be nested by category)")
    certifications: List[Dict[str, str]] = Field(description="1-2 MOST relevant certifications (existing or suggested as 'In Progress'). Format: name, issuer, date, status")
    projects: List[Dict[str, Any]] = Field(description="1-2 key projects with technologies and outcomes (OMIT if space constrained). Format: name, technologies, description, github_url (optional)")
    languages: List[Dict[str, str]] = Field(description="Language proficiency. Format: language, proficiency (Native/Fluent/Professional/Basic)")


class ReviewResult(BaseModel):
    """Structured output from Reviewer"""
    approved: bool = Field(description="Whether the resume is approved")
    coherence_check: bool = Field(description="No false dates or invented experiences")
    length_check: bool = Field(description="Fits on 1 page")
    quality_score: float = Field(description="Quality score 0-100")
    suggestions: List[str] = Field(description="Suggestions for improvement if not approved")


class MultiAgentResumeGenerator:
    """
    Multi-agent system for intelligent resume generation.
    Uses 5 specialized agents to analyze, match, and generate tailored resumes.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the multi-agent system.

        Args:
            api_key: OpenRouter API key (defaults to settings.OPENROUTER_API_KEY)
            model: Model to use (defaults to settings.OPENROUTER_MODEL)
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL

        if not self.api_key:
            raise ValueError("OpenRouter API key not provided")

        # Initialize LangChain ChatOpenAI with OpenRouter endpoint
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_tokens=4000,
            default_headers={
                "HTTP-Referer": settings.BACKEND_URL,
                "X-Title": "ResumeSync"
            }
        )

        # Initialize agents
        self.profile_analyzer = ProfileAnalyzerAgent(self.llm)
        self.job_analyzer = JobAnalyzerAgent(self.llm)
        self.matchmaker = MatchMakerAgent(self.llm)
        self.content_writer = ContentWriterAgent(self.llm)
        self.reviewer = ReviewerAgent(self.llm)

    def generate_resume(
        self,
        profile_data: Dict,
        job_data: Dict,
        max_iterations: int = 2
    ) -> Dict:
        """
        Generate an intelligent, tailored resume using the multi-agent system.

        Args:
            profile_data: LinkedIn profile data
            job_data: Job posting data
            max_iterations: Maximum iterations for reviewer feedback loop

        Returns:
            dict: Structured resume content with selections and enhancements
        """
        print("\n=== Starting Multi-Agent Resume Generation ===\n")

        # Agent 1: Analyze Profile
        print("Agent 1: ProfileAnalyzer - Analyzing profile...")
        profile_analysis = self.profile_analyzer.analyze(profile_data)
        print(f"  - Identified {len(profile_analysis.key_strengths)} key strengths")
        print(f"  - Career level: {profile_analysis.career_level}")
        print(f"  - Years of experience: {profile_analysis.years_of_experience}")

        # Agent 2: Analyze Job
        print("\nAgent 2: JobAnalyzer - Analyzing job posting...")
        job_analysis = self.job_analyzer.analyze(job_data)
        print(f"  - Required skills: {len(job_analysis.required_skills)}")
        print(f"  - ATS keywords identified: {len(job_analysis.ats_keywords)}")
        print(f"  - Seniority level: {job_analysis.seniority_level}")

        # Agent 3: Match Profile to Job
        print("\nAgent 3: MatchMaker - Matching profile to job...")
        match_analysis = self.matchmaker.match(
            profile_data,
            job_data,
            profile_analysis,
            job_analysis
        )
        print(f"  - Overall match score: {match_analysis.overall_match_score:.1f}%")
        print(f"  - Selected {len(match_analysis.selected_experiences)} experiences")
        print(f"  - Selected {len(match_analysis.selected_skills)} skills")

        # Agent 4: Generate Enhanced Content
        print("\nAgent 4: ContentWriter - Generating tailored content...")
        enhanced_content = self.content_writer.write(
            profile_data,
            job_data,
            match_analysis,
            profile_analysis,
            job_analysis
        )
        print(f"  - Generated professional summary ({len(enhanced_content.professional_summary)} chars)")
        print(f"  - Enhanced {len(enhanced_content.enhanced_experiences)} experiences")

        # Build initial resume
        resume_content = self._build_resume_structure(
            profile_data,
            job_data,
            match_analysis,
            enhanced_content
        )

        # Agent 5: Review and Validate
        iteration = 0
        while iteration < max_iterations:
            print(f"\nAgent 5: Reviewer - Validating resume (iteration {iteration + 1})...")
            review_result = self.reviewer.review(
                resume_content,
                profile_data,
                job_data,
                match_analysis
            )
            print(f"  - Quality score: {review_result.quality_score:.1f}/100")
            print(f"  - Coherence check: {'PASS' if review_result.coherence_check else 'FAIL'}")
            print(f"  - Length check: {'PASS' if review_result.length_check else 'FAIL'}")

            if review_result.approved:
                print("  - Resume APPROVED!")
                break
            else:
                print(f"  - Resume needs revision: {review_result.suggestions}")
                # In a real implementation, you would feed suggestions back to ContentWriter
                # For now, we'll accept the resume after max_iterations
                iteration += 1

        # Add metadata
        resume_content["match_score"] = match_analysis.overall_match_score
        resume_content["generation_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "model": self.model,
            "iterations": iteration + 1,
            "quality_score": review_result.quality_score if 'review_result' in locals() else 0
        }

        print("\n=== Resume Generation Complete ===\n")
        return resume_content

    def _build_resume_structure(
        self,
        profile_data: Dict,
        job_data: Dict,
        match_analysis: MatchAnalysis,
        enhanced_content: EnhancedContent
    ) -> Dict:
        """
        Build the final resume structure from agent outputs.

        Args:
            profile_data: Original profile data
            job_data: Job data
            match_analysis: Match analysis from MatchMaker
            enhanced_content: Enhanced content from ContentWriter

        Returns:
            dict: Structured resume content
        """
        # Personal info
        personal_info = {
            "full_name": profile_data.get("full_name", ""),
            "email": profile_data.get("email", ""),
            "phone": profile_data.get("phone", ""),
            "location": profile_data.get("location", ""),
            "linkedin": profile_data.get("profile_url", ""),
            "headline": profile_data.get("headline", ""),
            "job_title_variants": enhanced_content.job_title_variants,  # NEW: ATS job title variants
            "photo_url": profile_data.get("photo_url", ""),
            "profile_image_url": profile_data.get("profile_image_url", ""),
            "additional_links": profile_data.get("additional_links", [])
        }

        # Select and enhance experiences
        all_experiences = profile_data.get("experiences", [])
        selected_experiences = []
        for position, idx in enumerate(match_analysis.selected_experiences):
            if idx < len(all_experiences):
                exp = all_experiences[idx].copy()
                # Merge enhanced version by position (ContentWriter returns enhancements in same order)
                if position < len(enhanced_content.enhanced_experiences):
                    enhanced_exp = enhanced_content.enhanced_experiences[position]
                    # Add bullets from enhanced content (this is the new AI-generated content)
                    if 'bullets' in enhanced_exp:
                        exp['bullets'] = enhanced_exp['bullets']
                    # Keep legacy description/achievements support for backward compatibility
                    elif 'description' in enhanced_exp and enhanced_exp['description']:
                        exp['description'] = enhanced_exp['description']
                    elif 'achievements' in enhanced_exp:
                        exp['achievements'] = enhanced_exp['achievements']

                    # CRITICAL: Do NOT overwrite title, company, location, start_date, end_date
                    # These must remain from the original profile for accuracy
                    # Only merge fields that are safe to enhance (like bullets, description)
                selected_experiences.append(exp)

        # Select education
        all_education = profile_data.get("education", [])
        selected_education = []
        for idx in match_analysis.selected_education:
            if idx < len(all_education):
                selected_education.append(all_education[idx])

        # Build resume - use categorized skills if available
        skills_data = enhanced_content.skill_descriptions
        if isinstance(skills_data, dict) and any(skills_data.values()):
            # Use enhanced categorized skills from ContentWriter
            resume_skills = skills_data
        else:
            # Fallback to flat list
            resume_skills = {
                "technical": match_analysis.selected_skills[:15],  # Max 15 skills
                "soft": [],
                "tools": []
            }

        resume = {
            "personal_info": personal_info,
            "professional_summary": enhanced_content.professional_summary,
            "work_experience": selected_experiences,
            "education": selected_education,
            "skills": resume_skills,
            "certifications": enhanced_content.certifications,  # NEW: AI-generated certifications
            "projects": enhanced_content.projects,  # NEW: AI-generated projects
            "languages": enhanced_content.languages  # NEW: AI-generated languages
        }

        return resume


class ProfileAnalyzerAgent:
    """Agent 1: Analyzes LinkedIn profile data"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=ProfileAnalysis)

    def analyze(self, profile_data: Dict) -> ProfileAnalysis:
        """Analyze profile and extract key insights"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert career analyst. Analyze the LinkedIn profile data and extract key insights about the candidate's strengths, skills, and experience level.

{format_instructions}"""),
            ("user", """Analyze this LinkedIn profile:

Full Name: {full_name}
Headline: {headline}
Summary: {summary}

Experiences:
{experiences}

Education:
{education}

Skills:
{skills}

Extract:
1. Key strengths and competencies (5-7 most important)
2. Technical skills
3. Soft skills
4. Total years of professional experience
5. Career level (entry/mid/senior/lead/executive)
6. Professional domains/industries

Be precise and analytical.""")
        ])

        messages = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            full_name=profile_data.get("full_name", ""),
            headline=profile_data.get("headline", ""),
            summary=profile_data.get("summary", ""),
            experiences=json.dumps(profile_data.get("experiences", []), indent=2),
            education=json.dumps(profile_data.get("education", []), indent=2),
            skills=", ".join(profile_data.get("skills", []))
        )

        response = self.llm.invoke(messages)
        return self.parser.parse(response.content)


class JobAnalyzerAgent:
    """Agent 2: Analyzes job posting requirements"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=JobAnalysis)

    def analyze(self, job_data: Dict) -> JobAnalysis:
        """Analyze job posting and extract requirements"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert job requirement analyst. Analyze job postings and extract key requirements, skills, and ATS keywords.

{format_instructions}"""),
            ("user", """Analyze this job posting:

Job Title: {title}
Company: {company}
Seniority Level: {seniority_level}

Job Description:
{description}

Extract:
1. Required skills (explicitly mentioned as required/must-have)
2. Preferred skills (nice-to-have)
3. Key responsibilities
4. Qualifications needed
5. ATS keywords (important terms for applicant tracking systems)
6. Seniority level required

Be thorough and identify all relevant keywords.""")
        ])

        messages = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            title=job_data.get("title", ""),
            company=job_data.get("company", ""),
            seniority_level=job_data.get("seniority_level", ""),
            description=job_data.get("description", "")
        )

        response = self.llm.invoke(messages)
        return self.parser.parse(response.content)


class MatchMakerAgent:
    """Agent 3: Matches profile to job and selects relevant content"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=MatchAnalysis)

    def match(
        self,
        profile_data: Dict,
        job_data: Dict,
        profile_analysis: ProfileAnalysis,
        job_analysis: JobAnalysis
    ) -> MatchAnalysis:
        """Match profile to job and select most relevant content"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at matching candidate profiles to job requirements.

SELECTION RULES - CRITICAL FOR 1-PAGE CONSTRAINT:
1. Experiences:
   - Latest experience: ALWAYS include (mandatory)
   - Previous experiences: Include ONLY if HIGHLY relevant to the job (2-3 total max)
   - STRICT LIMIT: Maximum 2-3 experiences total (including latest)
   - Focus on quality over quantity - be VERY selective

2. Education:
   - Include only MOST RECENT or MOST RELEVANT degree (1-2 max)
   - If Bachelor → Master from same school, include both
   - Otherwise prioritize highest/most relevant degree

3. Skills:
   - Priority: Skills matching job requirements first
   - Then complementary relevant skills
   - Max 10-12 skills total
   - CRITICAL: Everything must fit on 1 page

{format_instructions}"""),
            ("user", """Match this profile to the job:

PROFILE ANALYSIS:
{profile_analysis}

JOB ANALYSIS:
{job_analysis}

PROFILE EXPERIENCES:
{experiences}

PROFILE EDUCATION:
{education}

PROFILE SKILLS:
{skills}

Calculate:
1. Overall match score (0-100%)
2. Relevance score for each experience
3. Which experiences to include (always include latest + relevant ones)
4. Which education to include (always include latest + different domains)
5. Which skills to include (prioritize job matches, max 15)
6. What skills are missing

Be selective - only include what truly supports the application.""")
        ])

        messages = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            profile_analysis=profile_analysis.json(),
            job_analysis=job_analysis.json(),
            experiences=json.dumps(profile_data.get("experiences", []), indent=2),
            education=json.dumps(profile_data.get("education", []), indent=2),
            skills=", ".join(profile_data.get("skills", []))
        )

        response = self.llm.invoke(messages)
        return self.parser.parse(response.content)


class ContentWriterAgent:
    """Agent 4: Generates tailored resume content"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=EnhancedContent)

    def write(
        self,
        profile_data: Dict,
        job_data: Dict,
        match_analysis: MatchAnalysis,
        profile_analysis: ProfileAnalysis,
        job_analysis: JobAnalysis
    ) -> EnhancedContent:
        """Generate enhanced, tailored resume content"""

        # Get selected experiences
        all_experiences = profile_data.get("experiences", [])
        selected_experiences = [
            all_experiences[idx] for idx in match_analysis.selected_experiences
            if idx < len(all_experiences)
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume writer. Generate compelling, tailored resume content.

ENHANCEMENT RULES:
✅ ALLOWED:
- "Expert in React" even if intermediate
- "Strong proficiency in Python" even if used moderately
- Emphasizing achievements and responsibilities
- Making descriptions more impactful
- INFERRING responsibilities from job title when description is missing

❌ NOT ALLOWED:
- "5+ years experience" if only 2 years real
- Inventing experiences that don't exist
- False dates or companies
- Lying about actual experience

CRITICAL INSTRUCTION FOR MISSING DESCRIPTIONS:
Many experiences will have EMPTY or VERY SHORT descriptions. When this happens, you MUST:
1. Analyze the job title, company, and dates
2. Look at the candidate's summary and headline for context
3. Review the target job requirements to understand what to emphasize
4. Generate a detailed, narrative description based on:
   - Industry-standard responsibilities for that role
   - Technologies mentioned in the candidate's summary
   - Skills that align with the target job
   - Realistic achievements for someone at that career level

Example:
- Input: title="DevOps", company="Vizzia", dates="Oct 2023 - Present", description=""
- Context: Candidate summary mentions "AWS, Cloud, Infrastructure as Code, DevOps"
- Target job: requires "cloud infrastructure, CI/CD, automation"
- Output: "Cloud Platform Engineer responsible for designing and optimizing critical cloud infrastructures using AWS. Led implementation of Infrastructure as Code practices, automated deployment pipelines, and DevOps workflows. Focused on distributed systems architecture, performance optimization, and scalability across production environments."

{format_instructions}"""),
            ("user", """Generate tailored resume content:

JOB TARGET:
Title: {job_title}
Company: {job_company}
Required Skills: {required_skills}
Key Responsibilities: {key_responsibilities}
Job Description: {job_description}

CANDIDATE PROFILE:
Name: {full_name}
Headline: {headline}
Summary: {summary}
Key Strengths: {key_strengths}
Career Level: {career_level}
Years of Experience: {years_of_experience}

SELECTED EXPERIENCES TO ENHANCE:
{selected_experiences}

SELECTED SKILLS:
{selected_skills}

Generate:
1. Job Title Variants (3-4 synonyms for ATS keyword matching)
   - Generate 3-4 job title variants that match the candidate's skills and the target job
   - Include synonyms and related titles
   - Example: "DevOps Engineer | Cloud Engineer | SRE | Platform Engineer"
   - Example: "Software Developer | Full Stack Engineer | Backend Developer"
   - These will be displayed in the header to maximize ATS keyword matches

2. Professional summary (2-3 SHORT SENTENCES MAXIMUM, VERY IMPACTFUL and QUANTIFIED)
   - START with job title variants: "DevOps Engineer | Cloud Engineer | SRE with 4+ years..."
   - Use candidate's summary as a base and enhance it
   - Include ONE specific metric or achievement (e.g., "0 to 100+ cities", "€15M fundraising")
   - Naturally include 2-3 key methodologies (Agile, DevOps, CI/CD)
   - Highlight expertise and unique value proposition
   - Keep VERY CONCISE - maximum 2-3 sentences
   - Align with target job requirements

3. Enhanced descriptions for each experience - CRITICAL: USE BULLET POINTS, NOT PARAGRAPHS
   ⚠️ **CRITICAL: PRESERVE EXACT VALUES FROM ORIGINAL PROFILE**
   - You MUST use the EXACT company names, locations, and dates from the candidate's profile
   - DO NOT modify, shorten, or change company names in any way
   - DO NOT change date formats or ranges
   - DO NOT add or remove location information
   - These fields are FACTUAL and must remain unchanged

   Example of what NOT to do:
   ❌ Original: "Vizzia Technologies" → Generated: "Vizzia" (WRONG - shortened company name)
   ❌ Original: "Oct 2023 - Present" → Generated: "2023 - Present" (WRONG - changed date format)
   ❌ Original: "Paris, France" → Generated: "France" (WRONG - removed city)

   ✅ Correct approach:
   - Copy EXACT company name: "Vizzia Technologies"
   - Copy EXACT dates: "Oct 2023 - Present"
   - Copy EXACT location: "Paris, France"
   - ONLY generate NEW content for the "bullets" field

   - For EACH experience, generate 2-4 CONCISE BULLET POINTS (NOT narrative paragraphs)
   - CRITICAL: For 1-page resumes, prefer 2-3 bullets per experience
   - Start each bullet with a strong ACTION VERB:
     * Creation: Architected, Designed, Developed, Built, Implemented, Created, Engineered
     * Leadership: Led, Spearheaded, Directed, Managed, Coordinated, Drove
     * Improvement: Optimized, Enhanced, Improved, Streamlined, Automated, Reduced
     * Analysis: Analyzed, Evaluated, Assessed, Diagnosed, Investigated
     * Delivery: Delivered, Deployed, Launched, Executed, Completed, Shipped
   - Include QUANTIFIED METRICS in each bullet (%, numbers, time savings, scale)
   - Mention SPECIFIC TECHNOLOGIES in each bullet
   - Show BUSINESS IMPACT (uptime, cost savings, revenue, efficiency)
   - Keep bullets VERY concise (1 line max, 2 lines if critical)
   - If description is empty: INFER from title, company, candidate's summary, and target job

   Example format (bullets array in each experience) - NOTE: Use EXACT values from input:
   {{
     "title": "DevOps Engineer",
     "company": "Vizzia Technologies",
     "location": "Paris, France",
     "start_date": "Oct 2023",
     "end_date": "Present",
     "bullets": [
       "Architected and deployed CI/CD pipelines using Azure DevOps and Jenkins, reducing release cycles by 70%",
       "Managed AWS cloud infrastructure supporting 100+ microservices with 99.99% uptime",
       "Automated infrastructure provisioning with Terraform and Ansible, cutting deployment time by 75%"
     ]
   }}

4. Certifications (1-2 MOST relevant certifications ONLY)
   - If candidate has certifications in profile, include ONLY the most relevant ones
   - If missing or insufficient, suggest 1-2 relevant certifications as "In Progress" or "Planned"
   - Choose certifications that align BEST with target job and candidate's skills
   - Examples: AWS Certified Solutions Architect, CKA, Terraform Associate, Azure Administrator, Google Cloud Professional, etc.
   - Format: {{"name": "AWS Certified Solutions Architect", "issuer": "Amazon Web Services", "date": "2025", "status": "In Progress"}}

5. Projects (1-2 key projects ONLY - OMIT if space constrained)
   - ONLY include if critical to the application
   - Infer from work experience what projects the candidate likely worked on
   - OR suggest relevant projects based on their skills and target job
   - Include specific technologies used
   - Add quantified outcomes and business impact
   - If candidate has GitHub links in profile, you can reference them
   - Format example: {{"name": "CI/CD Pipeline Automation", "technologies": ["Jenkins", "Docker", "Kubernetes"], "description": "Automated deployment pipeline reducing release time by 75%", "github_url": ""}}

6. Languages (language proficiency)
   - Infer languages from candidate's location, education, and profile
   - Always include native language based on location
   - Include English if working in tech (very common requirement)
   - Include any other languages mentioned in profile or education
   - Format examples: {{"language": "French", "proficiency": "Native"}}, {{"language": "English", "proficiency": "Fluent"}}
   - Proficiency levels: Native, Fluent, Professional, Intermediate, Basic

7. Skills - CRITICAL REQUIREMENT FOR TECHNICAL SPECIFICITY:
   ❌ DO NOT use generic categories like:
      - "Operating Systems"
      - "Version Control"
      - "Cloud Computing"
      - "Databases"
      - "Programming Languages"

   ✅ INSTEAD, use SPECIFIC tools, technologies, and versions:
      - "Linux (Manjaro, Ubuntu 22.04, CentOS), Windows Server 2019/2022"
      - "Git, GitHub, GitLab, Bitbucket"
      - "AWS (EC2, S3, Lambda, RDS, CloudFormation), Azure (VMs, Storage, Functions, DevOps)"
      - "PostgreSQL 14+, MySQL 8.0, MongoDB 6.0, Redis"
      - "Python 3.11, JavaScript (Node.js, React), Go 1.21"

   SKILL CATEGORIZATION RULES:
   - Organize by domain (e.g., "DevOps & Automation", "Cloud & Infrastructure", "Development", "Methodologies")
   - ALWAYS include a "Methodologies" category with: Agile, Scrum, GitOps, DevSecOps, SRE, CI/CD, Infrastructure as Code (IaC), Observability
   - Each skill value should list SPECIFIC tools/technologies, separated by commas
   - Include versions when relevant and known
   - Prefer listing multiple specific tools over broad categories
   - Align with target job's tech stack when possible
   - Example categories:
     * "DevOps & Automation": "Jenkins, Azure DevOps, GitHub Actions, GitLab CI, Ansible, Puppet"
     * "Cloud & Infrastructure": "AWS (EC2, S3, Lambda, RDS), Azure (VMs, Functions), GCP (Compute Engine)"
     * "Containers & Orchestration": "Docker, Kubernetes, Docker Compose, Helm, AKS, EKS"
     * "Methodologies": "Agile, Scrum, GitOps, DevSecOps, SRE, CI/CD, Infrastructure as Code"

IMPORTANT:
- Make the summary and descriptions VERY attractive, quantified, and impactful.
- When descriptions are missing, INFER detailed content based on role + candidate's background + target job
- Use metrics, numbers, and business outcomes whenever possible.
- Align generated content with the target job requirements.
- For skills: BE EXTREMELY SPECIFIC - list actual tools, not categories!
- Think like you're selling the candidate's expertise.""")
        ])

        messages = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            job_title=job_data.get("title", ""),
            job_company=job_data.get("company", ""),
            job_description=job_data.get("description", "")[:1000],  # First 1000 chars for context
            required_skills=", ".join(job_analysis.required_skills),
            key_responsibilities=", ".join(job_analysis.key_responsibilities),
            full_name=profile_data.get("full_name", ""),
            headline=profile_data.get("headline", ""),
            summary=profile_data.get("summary", ""),
            key_strengths=", ".join(profile_analysis.key_strengths),
            career_level=profile_analysis.career_level,
            years_of_experience=profile_analysis.years_of_experience,
            selected_experiences=json.dumps(selected_experiences, indent=2),
            selected_skills=", ".join(match_analysis.selected_skills)
        )

        response = self.llm.invoke(messages)
        return self.parser.parse(response.content)


class ReviewerAgent:
    """Agent 5: Reviews and validates resume quality"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=ReviewResult)

    def review(
        self,
        resume_content: Dict,
        profile_data: Dict,
        job_data: Dict,
        match_analysis: MatchAnalysis
    ) -> ReviewResult:
        """Review resume for quality, coherence, and 1-page fit"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a resume quality reviewer. Check for coherence, authenticity, and proper formatting.

VALIDATION CHECKS:
1. Coherence: No false dates, no invented experiences
2. Length: MUST fit on 1 page (STRICT: ~450-500 words max, including all sections)
3. Quality: Professional, tailored, ATS-optimized
4. Authenticity: Experience claims match original profile

CRITICAL: Be STRICT about length. If word count exceeds 500, mark length_check as FALSE.

{format_instructions}"""),
            ("user", """Review this resume:

GENERATED RESUME:
{resume_content}

ORIGINAL PROFILE (for verification):
{original_profile}

Verify:
1. No false information (dates, companies, experiences match original)
2. Fits on 1 page (word count check)
3. Quality score (0-100)
4. Coherence and professionalism
5. Approval or suggestions for improvement""")
        ])

        # Estimate word count
        word_count = (
            len(resume_content.get("professional_summary", "").split()) +
            sum(len(str(exp).split()) for exp in resume_content.get("work_experience", [])) +
            sum(len(str(edu).split()) for edu in resume_content.get("education", []))
        )

        messages = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            resume_content=json.dumps(resume_content, indent=2),
            original_profile=json.dumps({
                "experiences": profile_data.get("experiences", []),
                "education": profile_data.get("education", [])
            }, indent=2)
        )

        response = self.llm.invoke(messages)
        review = self.parser.parse(response.content)

        # Override length check based on word count (STRICT: 500 words max for 1-page fit)
        review.length_check = word_count <= 500

        return review


# Convenience function
def generate_intelligent_resume(
    profile_data: Dict,
    job_data: Dict,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Dict:
    """
    Generate an intelligent, tailored resume using multi-agent system.

    Args:
        profile_data: LinkedIn profile data
        job_data: Job posting data
        api_key: OpenRouter API key (optional)
        model: Model to use (optional)

    Returns:
        dict: Structured resume content
    """
    generator = MultiAgentResumeGenerator(api_key=api_key, model=model)
    return generator.generate_resume(profile_data, job_data)
