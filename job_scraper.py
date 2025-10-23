"""
Job Posting Scraper
Extracts job description and requirements from job posting URLs
Supports: LinkedIn, Indeed, and generic job pages
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional


def scrape_linkedin_job(url: str) -> Optional[Dict]:
    """Scrape job posting from LinkedIn."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract job details (LinkedIn's HTML structure)
        job_data = {
            "url": url,
            "company_name": None,
            "job_title": None,
            "location": None,
            "description": None,
            "requirements": None
        }

        # Try to extract title
        title_elem = soup.find('h1', class_='top-card-layout__title') or soup.find('h1')
        if title_elem:
            job_data["job_title"] = title_elem.get_text(strip=True)

        # Try to extract company
        company_elem = soup.find('a', class_='topcard__org-name-link') or soup.find('span', class_='topcard__flavor')
        if company_elem:
            job_data["company_name"] = company_elem.get_text(strip=True)

        # Try to extract location
        location_elem = soup.find('span', class_='topcard__flavor--bullet')
        if location_elem:
            job_data["location"] = location_elem.get_text(strip=True)

        # Try to extract description
        desc_elem = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
        if desc_elem:
            job_data["description"] = desc_elem.get_text(separator='\n', strip=True)

        return job_data

    except Exception as e:
        print(f"Error scraping LinkedIn job: {e}")
        return None


def scrape_indeed_job(url: str) -> Optional[Dict]:
    """Scrape job posting from Indeed."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        job_data = {
            "url": url,
            "company_name": None,
            "job_title": None,
            "location": None,
            "description": None,
            "requirements": None
        }

        # Extract title
        title_elem = soup.find('h1', class_='jobsearch-JobInfoHeader-title')
        if title_elem:
            job_data["job_title"] = title_elem.get_text(strip=True)

        # Extract company
        company_elem = soup.find('div', {'data-company-name': True})
        if company_elem:
            job_data["company_name"] = company_elem.get_text(strip=True)

        # Extract location
        location_elem = soup.find('div', {'data-testid': 'job-location'})
        if location_elem:
            job_data["location"] = location_elem.get_text(strip=True)

        # Extract description
        desc_elem = soup.find('div', id='jobDescriptionText')
        if desc_elem:
            job_data["description"] = desc_elem.get_text(separator='\n', strip=True)

        return job_data

    except Exception as e:
        print(f"Error scraping Indeed job: {e}")
        return None


def scrape_generic_job(url: str) -> Optional[Dict]:
    """Fallback: Try to scrape any job page generically."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract all text content
        text_content = soup.get_text(separator='\n', strip=True)

        job_data = {
            "url": url,
            "company_name": None,
            "job_title": None,
            "location": None,
            "description": text_content,
            "requirements": None
        }

        # Try to find title (usually in h1)
        h1 = soup.find('h1')
        if h1:
            job_data["job_title"] = h1.get_text(strip=True)

        return job_data

    except Exception as e:
        print(f"Error scraping job page: {e}")
        return None


def manual_input_job() -> Dict:
    """Fallback: Manually input job details."""
    print("\n" + "="*80)
    print("MANUAL JOB INPUT")
    print("="*80)
    print("Please paste the job details:\n")

    job_data = {
        "url": None,
        "company_name": input("Company Name: ").strip(),
        "job_title": input("Job Title: ").strip(),
        "location": input("Location (optional): ").strip() or None,
        "description": input("\nJob Description (paste full text):\n").strip(),
        "requirements": None
    }

    return job_data


def scrape_job(url: str) -> Optional[Dict]:
    """
    Non-interactive job scraper for API use.
    Returns job data or None if scraping fails.
    """
    if 'linkedin.com' in url:
        return scrape_linkedin_job(url)
    elif 'indeed.com' in url:
        return scrape_indeed_job(url)
    else:
        return scrape_generic_job(url)


def get_job_posting(url: Optional[str] = None) -> Dict:
    """
    Main function to get job posting data.
    Tries to scrape from URL, falls back to manual input if needed.
    """
    print("\n" + "="*80)
    print("STEP 2: GET JOB POSTING DATA")
    print("="*80)

    if not url:
        url = input("\nEnter job posting URL (or press Enter to manually input): ").strip()

    if not url:
        return manual_input_job()

    print(f"\n⏳ Scraping job from: {url}")

    # Determine which scraper to use based on URL
    job_data = None
    if 'linkedin.com' in url:
        print("   Detected: LinkedIn")
        job_data = scrape_linkedin_job(url)
    elif 'indeed.com' in url:
        print("   Detected: Indeed")
        job_data = scrape_indeed_job(url)
    else:
        print("   Detected: Generic job page")
        job_data = scrape_generic_job(url)

    # If scraping failed or incomplete data
    if not job_data or not job_data.get("description"):
        print("\n⚠️  Scraping failed or incomplete. Let's try manual input.")
        return manual_input_job()

    print("\n✓ Job data scraped successfully!")
    print(f"   Title: {job_data.get('job_title', 'N/A')}")
    print(f"   Company: {job_data.get('company_name', 'N/A')}")

    # Allow user to verify/edit
    edit = input("\nEdit any fields? (y/n): ").strip().lower()
    if edit == 'y':
        if input("Edit company? (y/n): ").strip().lower() == 'y':
            job_data["company_name"] = input("Company Name: ").strip()
        if input("Edit title? (y/n): ").strip().lower() == 'y':
            job_data["job_title"] = input("Job Title: ").strip()
        if input("Edit description? (y/n): ").strip().lower() == 'y':
            job_data["description"] = input("Job Description:\n").strip()

    return job_data


if __name__ == "__main__":
    # Test the scraper
    print("Job Scraper Test")
    job = get_job_posting()
    print("\n" + "="*80)
    print("JOB DATA:")
    print("="*80)
    print(f"Company: {job['company_name']}")
    print(f"Title: {job['job_title']}")
    print(f"Location: {job['location']}")
    print(f"\nDescription:\n{job['description'][:500]}...")
