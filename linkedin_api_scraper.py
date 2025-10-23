"""
LinkedIn Profile Scraper via API
Uses OAuth access token to fetch complete profile data from LinkedIn API
"""

import requests
from typing import Dict, List, Optional
import json


class LinkedInProfileAPI:
    """
    LinkedIn Profile API client using OAuth access token.
    Fetches complete profile including experiences, education, and skills.
    """

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token: str):
        """
        Initialize with OAuth access token.

        Args:
            access_token: LinkedIn OAuth access token from authentication
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def get_basic_profile(self) -> Dict:
        """
        Get basic profile information (name, headline, etc.).
        Uses the /v2/userinfo endpoint (OpenID Connect).

        Returns:
            dict: Basic profile data
        """
        url = "https://api.linkedin.com/v2/userinfo"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_profile_details(self) -> Dict:
        """
        Get detailed profile information.
        Uses the /v2/me endpoint.

        Returns:
            dict: Detailed profile data
        """
        url = f"{self.BASE_URL}/me"
        params = {
            "projection": "(id,firstName,lastName,headline,vanityName,profilePicture)"
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_email(self) -> str:
        """
        Get user's primary email address.

        Returns:
            str: Email address
        """
        url = f"{self.BASE_URL}/emailAddress?q=members&projection=(elements*(handle~))"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        if 'elements' in data and len(data['elements']) > 0:
            return data['elements'][0]['handle~']['emailAddress']
        return None

    def get_positions(self) -> List[Dict]:
        """
        Get work experience/positions.
        Note: This requires the r_fullprofile permission which is restricted.

        Returns:
            list: List of position objects
        """
        # This endpoint requires additional permissions beyond basic profile
        # LinkedIn restricts access to detailed profile data
        url = f"{self.BASE_URL}/positions?q=memberPositions"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return self._parse_positions(data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("⚠️  Warning: Access to positions requires additional LinkedIn API permissions")
                return []
            raise

    def _parse_positions(self, data: Dict) -> List[Dict]:
        """Parse positions data from LinkedIn API response."""
        positions = []
        elements = data.get('elements', [])

        for element in elements:
            position = {
                "title": element.get('title'),
                "company": element.get('companyName'),
                "location": element.get('locationName'),
                "start_date": self._format_date(element.get('timePeriod', {}).get('startDate')),
                "end_date": self._format_date(element.get('timePeriod', {}).get('endDate')) if element.get('timePeriod', {}).get('endDate') else "Present",
                "description": element.get('description', '')
            }
            positions.append(position)

        return positions

    def _format_date(self, date_obj: Optional[Dict]) -> str:
        """Format LinkedIn date object to MM/YYYY string."""
        if not date_obj:
            return ""
        month = date_obj.get('month', 1)
        year = date_obj.get('year')
        return f"{month:02d}/{year}"

    def get_complete_profile(self) -> Dict:
        """
        Attempt to fetch complete profile data.
        Falls back gracefully if certain endpoints are restricted.

        Returns:
            dict: Complete profile structure
        """
        print("\n⏳ Fetching LinkedIn profile via API...")

        # Get basic info (this always works with openid scope)
        basic_info = self.get_basic_profile()

        profile = {
            "full_name": basic_info.get('name', ''),
            "email": basic_info.get('email', ''),
            "headline": basic_info.get('name', ''),  # Basic endpoint doesn't return headline
            "summary": "",
            "location": basic_info.get('locale', ''),
            "linkedin_id": basic_info.get('sub', ''),
            "picture": basic_info.get('picture', ''),
            "experiences": [],
            "education": [],
            "skills": [],
            "certifications": []
        }

        # Try to get detailed profile
        try:
            details = self.get_profile_details()
            if 'headline' in details:
                profile['headline'] = details.get('headline', '')
        except Exception as e:
            print(f"⚠️  Could not fetch detailed profile: {e}")

        # Try to get positions
        try:
            positions = self.get_positions()
            profile['experiences'] = positions
        except Exception as e:
            print(f"⚠️  Could not fetch positions: {e}")

        print("✓ Profile data fetched (limited by API permissions)")
        return profile


def scrape_linkedin_with_token(access_token: str) -> Dict:
    """
    Main function to scrape LinkedIn profile using OAuth access token.

    Args:
        access_token: LinkedIn OAuth access token

    Returns:
        dict: Profile data structure compatible with database
    """
    api = LinkedInProfileAPI(access_token)
    return api.get_complete_profile()


def scrape_with_selenium(access_token: str) -> Dict:
    """
    Alternative: Use Selenium to scrape LinkedIn profile with authenticated session.
    This can access more data but requires headless browser.

    Args:
        access_token: LinkedIn OAuth access token (used to authenticate browser)

    Returns:
        dict: Complete profile data
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    import time

    print("\n⏳ Scraping LinkedIn profile with Selenium...")

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Navigate to LinkedIn
        driver.get("https://www.linkedin.com")

        # Set authentication cookies using access token
        # Note: This is tricky - LinkedIn uses httpOnly cookies
        # We need to use the access token to make API calls instead

        # Alternative: Ask user to provide their profile URL and scrape public data
        driver.get("https://www.linkedin.com/in/me/")

        # Wait for profile to load
        wait = WebDriverWait(driver, 10)

        # Scrape profile data
        profile_data = {
            "full_name": "",
            "headline": "",
            "summary": "",
            "experiences": [],
            "education": [],
            "skills": []
        }

        # This approach is limited without proper authentication
        # LinkedIn detects and blocks automated scraping

        print("⚠️  Selenium scraping requires manual login or is blocked by LinkedIn")
        return profile_data

    finally:
        driver.quit()


if __name__ == "__main__":
    """
    Test the LinkedIn API scraper.
    Requires a valid OAuth access token.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python linkedin_api_scraper.py <access_token>")
        print("\nTo get an access token:")
        print("1. Log in to ResumeSync")
        print("2. Your access token is stored in the database")
        print("3. Or use the OAuth flow to get a new one")
        sys.exit(1)

    access_token = sys.argv[1]

    try:
        profile = scrape_linkedin_with_token(access_token)
        print("\n" + "="*80)
        print("LINKEDIN PROFILE DATA")
        print("="*80)
        print(json.dumps(profile, indent=2))

        # Save to file
        with open('linkedin_profile_scraped.json', 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"\n✓ Profile saved to linkedin_profile_scraped.json")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
