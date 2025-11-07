"""
Apify LinkedIn Profile Scraper Service
Uses Apify's LinkedIn Profile Scraper actor to fetch complete profile data
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import time
from apify_client import ApifyClient
from ..core.config import settings


class ApifyLinkedInScraper:
    """
    Service for scraping LinkedIn profiles using Apify API.
    Tries multiple actors with fallback support for reliability.
    """

    APIFY_API_URL = "https://api.apify.com/v2"

    # Multiple actor configurations with fallback support
    ACTOR_CONFIGS = [
        {
            "id": "dev_fusion/linkedin-profile-scraper",
            "name": "Dev Fusion LinkedIn Scraper",
            "input_format": "profileUrls"
        },
        {
            "id": "yZnhB5JewWf9xSmoM",
            "name": "LinkedIn Profile Scraper (ID)",
            "input_format": "startUrls"
        },
        {
            "id": "supreme_coder/linkedin-profile-scraper",
            "name": "Supreme Coder LinkedIn Scraper",
            "input_format": "linkedinUrls"
        }
    ]

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Apify scraper with API token.

        Args:
            api_token: Apify API token (defaults to settings.APIFY_API_TOKEN)
        """
        self.api_token = api_token or settings.APIFY_API_TOKEN
        if not self.api_token:
            raise ValueError("Apify API token not provided. Set APIFY_API_TOKEN environment variable.")

    def scrape_profile(self, profile_url: str, timeout: int = 180) -> Dict:
        """
        Scrape a LinkedIn profile using Apify with automatic fallback to different actors.

        Args:
            profile_url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
            timeout: Maximum time to wait for scraping to complete (seconds)

        Returns:
            dict: Complete profile data from Apify

        Raises:
            Exception: If scraping fails with all actors
        """
        print(f"\n⏳ Starting Apify scraping for: {profile_url}")
        print(f"   Trying {len(self.ACTOR_CONFIGS)} different actors with fallback...")

        # Initialize Apify client
        client = ApifyClient(self.api_token)

        last_error = None

        # Try each actor configuration
        for config in self.ACTOR_CONFIGS:
            actor_id = config["id"]
            actor_name = config["name"]
            input_format = config["input_format"]

            print(f"\n{'='*60}")
            print(f"Trying: {actor_name}")
            print(f"Actor ID: {actor_id}")
            print(f"{'='*60}")

            try:
                # Prepare input based on actor's expected format
                if input_format == "profileUrls":
                    actor_input = {
                        "profileUrls": [profile_url],
                        "proxy": {"useApifyProxy": True}
                    }
                elif input_format == "linkedinUrls":
                    actor_input = {
                        "linkedinUrls": [profile_url],
                        "proxy": {"useApifyProxy": True}
                    }
                elif input_format == "startUrls":
                    actor_input = {
                        "startUrls": [{"url": profile_url}]
                    }
                else:
                    actor_input = {
                        "startUrls": [{"url": profile_url}],
                        "proxyConfiguration": {"useApifyProxy": True}
                    }

                # Run the actor and wait for it to finish
                print(f"   Starting actor run...")
                run = client.actor(actor_id).call(run_input=actor_input, timeout_secs=timeout)

                print(f"   Run ID: {run['id']}")
                print(f"   Status: {run['status']}")

                # Check if run was successful
                if run['status'] != 'SUCCEEDED':
                    raise Exception(f"Apify run failed with status: {run['status']}")

                # Fetch results from the run's dataset
                dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

                if not dataset_items or len(dataset_items) == 0:
                    raise Exception("No profile data returned from Apify")

                profile_data = dataset_items[0]  # First result is the profile

                # Check if actor returned an error
                if 'error' in profile_data and profile_data.get('error'):
                    error_msg = profile_data.get('error')
                    print(f"⚠️  Actor returned error: {error_msg}")
                    raise Exception(f"Actor error: {error_msg}")

                # Validate that we got meaningful data
                if not profile_data.get('fullName') and not profile_data.get('experiences'):
                    print(f"⚠️  Data validation failed. Available keys: {list(profile_data.keys())[:20]}")
                    raise Exception("Profile data is empty or incomplete")

                print(f"\n✅ SUCCESS with {actor_name}!")
                print(f"   - Name: {profile_data.get('fullName', 'N/A')}")
                print(f"   - Headline: {profile_data.get('headline', 'N/A')}")
                print(f"   - Experiences: {len(profile_data.get('experiences', []))}")
                print(f"   - Education: {len(profile_data.get('educations', []))}")
                print(f"   - Connections: {profile_data.get('connections', 'N/A')}")

                return profile_data

            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(f"❌ Failed with {actor_name}: {error_msg[:200]}")
                continue

        # If we get here, all actors failed
        print(f"\n{'='*60}")
        print("❌ ALL ACTORS FAILED")
        print(f"{'='*60}")
        raise Exception(f"Failed to scrape profile with all {len(self.ACTOR_CONFIGS)} actors. Last error: {str(last_error)}")

    def parse_profile_data(self, apify_data: Dict) -> Dict:
        """
        Parse Apify profile data into our database format.
        Handles multiple data formats from different actors.

        Args:
            apify_data: Raw data from Apify scraper

        Returns:
            dict: Parsed profile data matching our LinkedInProfile model
        """
        # Extract and format experiences
        experiences = []

        # Try different experience field names
        raw_experiences = (apify_data.get("experiences") or
                          apify_data.get("positions") or
                          apify_data.get("experience") or [])

        for idx, exp in enumerate(raw_experiences):
            # DEBUG: Print raw experience data from Apify
            print(f"\n🔍 DEBUG - Raw Apify Experience #{idx + 1}:")
            print(f"   Full data: {exp}")

            # Handle different formats
            if isinstance(exp, dict):
                experience_entry = {
                    "title": exp.get("title") or exp.get("position") or "",
                    "company": exp.get("subtitle") or exp.get("companyName") or exp.get("company") or "",
                    "location": exp.get("location") or "",
                    "start_date": "",
                    "end_date": "",
                    "description": exp.get("description") or ""
                }

                # DEBUG: Print what we extracted
                print(f"   → Extracted company: {experience_entry['company']}")
                print(f"   → Available fields: title={exp.get('title')}, subtitle={exp.get('subtitle')}, companyName={exp.get('companyName')}, company={exp.get('company')}")

                # Parse date range
                date_range = exp.get("caption") or exp.get("dateRange") or ""

                # DEBUG: Print date parsing
                print(f"   → Raw date range: '{date_range}'")
                print(f"   → caption={exp.get('caption')}, dateRange={exp.get('dateRange')}")

                if " - " in date_range:
                    parts = date_range.split(" - ")
                    experience_entry["start_date"] = parts[0].strip()
                    experience_entry["end_date"] = parts[1].strip() if len(parts) > 1 else "Present"
                elif date_range:
                    experience_entry["start_date"] = date_range
                    experience_entry["end_date"] = "Present"

                # DEBUG: Print final parsed dates
                print(f"   → Final dates: {experience_entry['start_date']} - {experience_entry['end_date']}")

                experiences.append(experience_entry)

        # Extract and format education
        education = []

        # Try different education field names
        raw_education = (apify_data.get("educations") or
                        apify_data.get("schools") or
                        apify_data.get("education") or [])

        for edu in raw_education:
            if isinstance(edu, dict):
                education_entry = {
                    "school": edu.get("title") or edu.get("schoolName") or edu.get("school") or "",
                    "degree": edu.get("degree") or "",
                    "field": edu.get("fieldOfStudy") or edu.get("field") or "",
                    "start_date": "",
                    "end_date": "",
                    "description": edu.get("description") or ""
                }

                # Parse date range
                date_range = edu.get("caption") or edu.get("dateRange") or ""
                if " - " in date_range:
                    parts = date_range.split(" - ")
                    education_entry["start_date"] = parts[0].strip()
                    education_entry["end_date"] = parts[1].strip()
                elif date_range:
                    education_entry["graduation_year"] = date_range

                education.append(education_entry)

        # Extract skills (can be array of strings or array of objects)
        raw_skills = apify_data.get("skills") or []
        skills = []
        for skill in raw_skills:
            if isinstance(skill, str):
                skills.append(skill)
            elif isinstance(skill, dict):
                skills.append(skill.get("name") or skill.get("title") or "")

        # Extract certifications
        certifications = []
        for cert in apify_data.get("certifications") or []:
            if isinstance(cert, dict):
                certifications.append({
                    "name": cert.get("name") or cert.get("title") or "",
                    "authority": cert.get("authority") or cert.get("issuer") or "",
                    "date": cert.get("dateRange") or cert.get("date") or ""
                })

        # Extract profile photo URL (try different field names)
        photo_url = (
            apify_data.get("profilePicture") or
            apify_data.get("photoUrl") or
            apify_data.get("imageUrl") or
            apify_data.get("img") or
            apify_data.get("photo") or
            apify_data.get("profileImageUrl") or
            ""
        )

        return {
            "full_name": apify_data.get("fullName") or apify_data.get("name") or "",
            "headline": apify_data.get("headline") or "",
            "summary": apify_data.get("about") or apify_data.get("summary") or "",
            "location": apify_data.get("addressWithCountry") or apify_data.get("location") or "",
            "photo_url": photo_url,
            "profile_image_url": photo_url,  # Alias for compatibility
            "experiences": experiences,
            "education": education,
            "skills": skills,
            "certifications": certifications
        }

    def should_refresh_profile(self, last_synced_at: Optional[datetime], refresh_interval_days: int = 30) -> bool:
        """
        Determine if a profile should be refreshed based on last sync time.

        Args:
            last_synced_at: Last time profile was synced
            refresh_interval_days: Number of days before profile should be refreshed

        Returns:
            bool: True if profile should be refreshed
        """
        if not last_synced_at:
            return True

        time_since_sync = datetime.utcnow() - last_synced_at
        return time_since_sync > timedelta(days=refresh_interval_days)


def scrape_linkedin_profile(profile_url: str, api_token: Optional[str] = None) -> Dict:
    """
    Convenience function to scrape a LinkedIn profile using Apify.

    Args:
        profile_url: LinkedIn profile URL
        api_token: Optional Apify API token (uses env var if not provided)

    Returns:
        dict: Complete profile data from Apify
    """
    scraper = ApifyLinkedInScraper(api_token)
    apify_data = scraper.scrape_profile(profile_url)
    return scraper.parse_profile_data(apify_data)


class ApifyLinkedInJobScraper:
    """
    Service for scraping LinkedIn job postings using Apify API.
    Uses the actor: 39xxtfNEwIEQ1hRiM
    """

    APIFY_API_URL = "https://api.apify.com/v2"
    JOB_ACTOR_ID = "39xxtfNEwIEQ1hRiM"  # LinkedIn Job Scraper actor

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Apify job scraper with API token.

        Args:
            api_token: Apify API token (defaults to settings.APIFY_API_TOKEN)
        """
        self.api_token = api_token or settings.APIFY_API_TOKEN
        if not self.api_token:
            raise ValueError("Apify API token not provided. Set APIFY_API_TOKEN environment variable.")

    def extract_job_id(self, job_url: str) -> str:
        """
        Extract job ID from LinkedIn job URL.

        Args:
            job_url: LinkedIn job URL (e.g., https://www.linkedin.com/jobs/view/4304103657)

        Returns:
            str: Job ID
        """
        import re
        # Match patterns like:
        # https://www.linkedin.com/jobs/view/4304103657
        # https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4304103657
        match = re.search(r'(?:view/|currentJobId=)(\d+)', job_url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract job ID from URL: {job_url}")

    def scrape_job(self, job_url: str, timeout: int = 120) -> Dict:
        """
        Scrape a LinkedIn job posting using Apify.

        Args:
            job_url: LinkedIn job URL or job ID
            timeout: Maximum time to wait for scraping to complete (seconds)

        Returns:
            dict: Complete job data from Apify

        Raises:
            Exception: If scraping fails or times out
        """
        # Extract job ID from URL
        job_id = self.extract_job_id(job_url)
        print(f"\n⏳ Starting Apify job scraping for ID: {job_id}")

        # Initialize Apify client
        client = ApifyClient(self.api_token)

        # Actor input
        actor_input = {
            "job_id": [job_id]
        }

        print(f"   Actor: {self.JOB_ACTOR_ID}")
        print(f"   Job ID: {job_id}")

        try:
            # Run the actor and wait for it to finish
            print(f"   Starting actor run...")
            run = client.actor(self.JOB_ACTOR_ID).call(run_input=actor_input, timeout_secs=timeout)

            print(f"   Run ID: {run['id']}")
            print(f"   Status: {run['status']}")

            # Check if run was successful
            if run['status'] != 'SUCCEEDED':
                raise Exception(f"Apify run failed with status: {run['status']}")

            # Fetch results from the run's dataset
            dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            if not dataset_items or len(dataset_items) == 0:
                raise Exception("No job data returned from Apify")

            job_data = dataset_items[0]  # First result is the job

            # Extract nested data
            job_info = job_data.get('job_info', {})
            company_info = job_data.get('company_info', {})

            print(f"✓ Job data retrieved:")
            print(f"   - Title: {job_info.get('title', 'N/A')}")
            print(f"   - Company: {company_info.get('name', 'N/A')}")
            print(f"   - Location: {job_info.get('location', 'N/A')}")
            print(f"   - Job Type: {job_info.get('employment_status', 'N/A')}")

            return job_data

        except Exception as e:
            print(f"❌ Apify job scraping error: {e}")
            raise Exception(f"Failed to scrape job with Apify: {str(e)}")

    def parse_job_data(self, apify_data: Dict) -> Dict:
        """
        Parse Apify job data into our database format.

        Args:
            apify_data: Raw data from Apify job scraper

        Returns:
            dict: Parsed job data matching our Job model
        """
        job_info = apify_data.get('job_info', {})
        company_info = apify_data.get('company_info', {})
        salary_info = apify_data.get('salary_info', {})
        apply_details = apify_data.get('apply_details', {})

        return {
            "job_id": job_info.get('job_id'),
            "title": job_info.get('title', ''),
            "company": company_info.get('name', ''),
            "location": job_info.get('location', ''),
            "description": job_info.get('description', ''),
            "employment_type": job_info.get('employment_status', ''),
            "seniority_level": job_info.get('seniority_level', ''),
            "industries": company_info.get('industries', []),
            "skills": job_info.get('skills', []),
            "salary_min": salary_info.get('min_salary'),
            "salary_max": salary_info.get('max_salary'),
            "salary_currency": salary_info.get('currency_code', 'USD'),
            "is_remote": job_info.get('is_remote_allowed', False),
            "application_url": apply_details.get('application_url', ''),
            "raw_data": apify_data
        }


def scrape_linkedin_job(job_url: str, api_token: Optional[str] = None) -> Dict:
    """
    Convenience function to scrape a LinkedIn job using Apify.

    Args:
        job_url: LinkedIn job URL or job ID
        api_token: Optional Apify API token (uses env var if not provided)

    Returns:
        dict: Complete job data from Apify
    """
    scraper = ApifyLinkedInJobScraper(api_token)
    apify_data = scraper.scrape_job(job_url)
    return scraper.parse_job_data(apify_data)


if __name__ == "__main__":
    """
    Test the Apify LinkedIn scraper.
    Usage: python -m app.services.apify_scraper <profile_url>
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.apify_scraper <profile_url>")
        print("\nExample:")
        print("  python -m app.services.apify_scraper https://www.linkedin.com/in/username")
        print("\nMake sure APIFY_API_TOKEN environment variable is set.")
        sys.exit(1)

    profile_url = sys.argv[1]

    try:
        profile_data = scrape_linkedin_profile(profile_url)
        print("\n" + "="*80)
        print("SCRAPED PROFILE DATA")
        print("="*80)
        import json
        print(json.dumps(profile_data, indent=2))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
