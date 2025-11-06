"""
AI-Powered Job Matching Service with Intelligent Caching

Risk Mitigation:
- OpenRouter API costs → Cache matching results by job description hash
- AI matching too slow → Parallel processing, use faster/cheaper models
- Poor matches → Multi-agent approach with validation
"""
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import redis
from cachetools import TTLCache
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..core.config import settings


class JobMatcher:
    """
    AI-powered job-profile matching with intelligent caching
    """

    def __init__(self):
        # Redis for distributed caching (across workers)
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_available = True
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️  Redis unavailable, using in-memory cache: {e}")
            self.redis_available = False

        # In-memory cache as fallback
        self.memory_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL

        # Initialize OpenRouter client with cost-optimized model
        # Using GPT-4o-mini for matching (much cheaper than Claude)
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",  # $0.15/1M tokens input, $0.60/1M output
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,  # Low temperature for consistent matching
            max_tokens=1000,  # Limit output tokens (cost control)
        )

    def _generate_cache_key(self, profile_data: Dict, job_description: str) -> str:
        """
        Generate cache key from profile and job description
        Uses hashing to handle long descriptions
        """
        # Create a deterministic hash of profile + job description
        profile_str = json.dumps(profile_data, sort_keys=True)
        combined = f"{profile_str}|{job_description}"
        return f"job_match:{hashlib.sha256(combined.encode()).hexdigest()}"

    def _get_cached_match(self, cache_key: str) -> Optional[Dict]:
        """Try to get cached match result"""
        # Try Redis first
        if self.redis_available:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    print("🎯 Cache HIT (Redis)")
                    return json.loads(cached)
            except Exception as e:
                print(f"Redis get error: {e}")

        # Fallback to memory cache
        if cache_key in self.memory_cache:
            print("🎯 Cache HIT (memory)")
            return self.memory_cache[cache_key]

        print("⚡ Cache MISS - will compute match")
        return None

    def _set_cached_match(self, cache_key: str, match_result: Dict):
        """Save match result to cache"""
        # Save to Redis (24 hour TTL)
        if self.redis_available:
            try:
                self.redis_client.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(match_result)
                )
            except Exception as e:
                print(f"Redis set error: {e}")

        # Also save to memory cache
        self.memory_cache[cache_key] = match_result

    async def match_job_to_profile(
        self,
        profile_data: Dict,
        job_data: Dict
    ) -> Dict:
        """
        Match a single job to a profile using AI

        Args:
            profile_data: User's LinkedIn profile (skills, experience, summary)
            job_data: Scraped job data (title, description, company)

        Returns:
            {
                "match_score": 85,  # 0-100
                "matching_skills": ["Python", "React"],
                "missing_skills": ["Kubernetes"],
                "experience_fit": "strong",
                "reasoning": "..."
            }
        """
        # Check cache first
        cache_key = self._generate_cache_key(profile_data, job_data.get('description', ''))
        cached_result = self._get_cached_match(cache_key)
        if cached_result:
            return cached_result

        # No cache - compute with AI
        print(f"🤖 Computing AI match for: {job_data.get('job_title', 'Unknown')[:50]}...")

        try:
            match_result = await self._compute_ai_match(profile_data, job_data)

            # Cache the result
            self._set_cached_match(cache_key, match_result)

            return match_result

        except Exception as e:
            print(f"❌ AI matching error: {str(e)}")
            # Return a fallback score based on keyword matching
            return self._fallback_keyword_match(profile_data, job_data)

    async def _compute_ai_match(self, profile_data: Dict, job_data: Dict) -> Dict:
        """
        Compute match score using AI (OpenRouter)
        """
        # Extract profile information
        profile_skills = profile_data.get('skills', [])
        profile_experience = profile_data.get('experiences', [])
        profile_summary = profile_data.get('summary', '')

        # Build experience summary
        experience_summary = ""
        if profile_experience:
            latest_experiences = profile_experience[:3]  # Last 3 jobs
            for exp in latest_experiences:
                title = exp.get('title', 'Unknown')
                company = exp.get('company', 'Unknown')
                experience_summary += f"- {title} at {company}\n"

        # Extract job information
        job_title = job_data.get('job_title', 'Unknown Position')
        job_description = job_data.get('description', '')[:3000]  # Limit to 3000 chars (cost control)
        company_name = job_data.get('company_name', 'Unknown Company')

        # Create AI prompt
        system_prompt = """You are an expert job matching AI with a progressive and encouraging approach. Analyze the candidate's profile and job description using this prioritized scoring:

PRIORITY ORDER (most to least important):
1. Technical Skills (40%) - Hard technical skills, tools, frameworks, languages
2. Soft Skills (25%) - Communication, leadership, teamwork, problem-solving
3. Experience (20%) - Years of experience, similar roles, project types
4. Industries/Domains (10%) - Industry knowledge, domain expertise
5. Other Factors (5%) - Remote work, languages, transverse skills, certifications

SCORING PHILOSOPHY - Be Progressive & Encouraging:
- 80-100: Strong match with most key skills, some learning is fine
- 60-79: Good match with core skills, missing some advanced requirements
- 40-59: Decent match with transferable skills, could grow into role
- 20-39: Partial match, has foundation but significant gaps
- 0-19: Poor match, fundamentally different field

VALUE TRANSFERABLE SKILLS: Cloud experience transfers between AWS/Azure/GCP. Backend skills transfer between languages. Leadership transfers across industries.

Return JSON:
{
  "match_score": <integer 0-100>,
  "matching_skills": [<list of technical + soft skills that match>],
  "missing_skills": [<only critical/required skills candidate lacks>],
  "experience_fit": "<one of: weak, moderate, strong, excellent>",
  "reasoning": "<2-3 sentences: highlight strengths first, then growth areas>"
}"""

        # Extract additional profile data
        technical_skills = profile_data.get('technical_skills', profile_skills)[:30]
        soft_skills = profile_data.get('soft_skills', [])[:15]
        industries = profile_data.get('industries', [])[:10]
        years_experience = profile_data.get('years_of_experience', 'Unknown')

        user_prompt = f"""CANDIDATE PROFILE:

Technical Skills: {', '.join(technical_skills) if technical_skills else 'No technical skills listed'}

Soft Skills: {', '.join(soft_skills) if soft_skills else 'Collaboration, Problem-solving, Communication (inferred from experience)'}

Years of Experience: {years_experience}

Industries/Domains: {', '.join(industries) if industries else 'Not specified'}

Recent Experience:
{experience_summary if experience_summary else 'No experience listed'}

Professional Summary: {profile_summary[:500] if profile_summary else 'No summary'}

---

JOB POSTING:
Title: {job_title}
Company: {company_name}

Description:
{job_description}

---

Analyze this match using the priority order (Technical Skills > Soft Skills > Experience > Industries > Other). Be progressive and encouraging. Return JSON only."""

        # Call OpenRouter API
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.agenerate([messages])
        response_text = response.generations[0][0].text.strip()

        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
            response_text = response_text.strip()

            match_data = json.loads(response_text)

            # Validate structure
            required_keys = ['match_score', 'matching_skills', 'missing_skills', 'experience_fit', 'reasoning']
            if not all(key in match_data for key in required_keys):
                raise ValueError("Missing required keys in AI response")

            # Ensure match_score is 0-100
            match_data['match_score'] = max(0, min(100, int(match_data['match_score'])))

            return match_data

        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️  Failed to parse AI response: {e}")
            print(f"Response was: {response_text[:200]}")
            # Fallback to keyword matching
            return self._fallback_keyword_match(profile_data, job_data)

    def _fallback_keyword_match(self, profile_data: Dict, job_data: Dict) -> Dict:
        """
        Progressive keyword-based matching as fallback when AI fails
        More encouraging scoring that values transferable skills
        """
        # Get all skills (technical + soft)
        technical_skills = set(skill.lower() for skill in profile_data.get('technical_skills', profile_data.get('skills', [])))
        soft_skills = set(skill.lower() for skill in profile_data.get('soft_skills', []))
        all_skills = technical_skills.union(soft_skills)

        job_description = (job_data.get('description', '') + ' ' + job_data.get('job_title', '')).lower()

        # Count matching skills (prioritize technical skills)
        matching_tech = [skill for skill in technical_skills if skill in job_description]
        matching_soft = [skill for skill in soft_skills if skill in job_description]
        all_matching = matching_tech + matching_soft

        # Progressive scoring - be more generous
        if not all_skills:
            match_score = 55  # Slightly positive if no skills listed
        else:
            # Base score from direct matches (up to 70%)
            base_score = min(70, int((len(all_matching) / max(len(all_skills), 1)) * 70))

            # Bonus points for having multiple matches (up to 20%)
            bonus = min(20, len(all_matching) * 4)

            # Experience bonus (up to 10%)
            exp_bonus = 10 if profile_data.get('years_of_experience', 0) > 0 else 5

            match_score = min(100, base_score + bonus + exp_bonus)

        # Determine experience fit based on score
        if match_score >= 75:
            exp_fit = "strong"
        elif match_score >= 55:
            exp_fit = "moderate"
        else:
            exp_fit = "weak"

        return {
            "match_score": match_score,
            "matching_skills": all_matching[:15],
            "missing_skills": [],
            "experience_fit": exp_fit,
            "reasoning": f"Found {len(all_matching)} matching skills. Progressive scoring applied: technical skills prioritized, transferable skills valued."
        }

    async def match_multiple_jobs(
        self,
        profile_data: Dict,
        jobs_data: List[Dict]
    ) -> List[Dict]:
        """
        Match multiple jobs in parallel (faster processing)

        Returns:
            List of jobs with match_details added
        """
        import asyncio

        print(f"🔄 Matching {len(jobs_data)} jobs against profile...")

        # Create tasks for parallel processing
        tasks = []
        for job in jobs_data:
            task = self.match_job_to_profile(profile_data, job)
            tasks.append(task)

        # Run all matches in parallel
        match_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results with jobs
        matched_jobs = []
        for job, match_result in zip(jobs_data, match_results):
            if isinstance(match_result, Exception):
                print(f"⚠️  Match failed for {job.get('job_title', 'Unknown')}: {match_result}")
                # Use fallback
                match_result = self._fallback_keyword_match(profile_data, job)

            # Add match details to job
            job['match_score'] = match_result['match_score']
            job['match_details'] = match_result
            matched_jobs.append(job)

        # Sort by match score (descending)
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)

        print(f"✅ Matching complete! Scores: {[j['match_score'] for j in matched_jobs[:5]]}")

        return matched_jobs

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_maxsize": self.memory_cache.maxsize,
            "redis_available": self.redis_available
        }

        if self.redis_available:
            try:
                info = self.redis_client.info('stats')
                stats['redis_keyspace_hits'] = info.get('keyspace_hits', 0)
                stats['redis_keyspace_misses'] = info.get('keyspace_misses', 0)
            except:
                pass

        return stats
