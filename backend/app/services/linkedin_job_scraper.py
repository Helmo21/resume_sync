"""
LinkedIn Job Scraper Service (Phase 4)
Uses Selenium to scrape job postings from LinkedIn feed based on search keywords.
"""
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


class LinkedInJobScraper:
    """Scraper for LinkedIn job posts using Selenium"""

    def __init__(self, headless: bool = True):
        """
        Initialize LinkedIn scraper.

        Args:
            headless: Run browser in headless mode (no UI)
        """
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Use chromium-driver from Docker image
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)

    def login(self, email: str, password: str) -> bool:
        """
        Login to LinkedIn with credentials.

        Args:
            email: LinkedIn email
            password: LinkedIn password

        Returns:
            True if login successful

        Raises:
            Exception: If login fails
        """
        if not self.driver:
            self._init_driver()

        try:
            # Navigate to LinkedIn login
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(2)

            # Find and fill email field
            email_field = self.driver.find_element(By.ID, 'username')
            email_field.clear()
            email_field.send_keys(email)

            # Find and fill password field
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.clear()
            password_field.send_keys(password)

            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            # Wait for login to complete (check for feed or challenge)
            time.sleep(5)

            # Check if we're on the feed page or got a security challenge
            current_url = self.driver.current_url

            if 'checkpoint' in current_url or 'challenge' in current_url:
                raise Exception("LinkedIn security challenge detected. Manual intervention required.")

            if 'feed' in current_url or 'linkedin.com' in current_url:
                print("✅ Login successful")
                return True
            else:
                raise Exception(f"Login may have failed. Current URL: {current_url}")

        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    def search_jobs(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn.

        Args:
            keywords: Search keywords (from resume analysis)
            location: Location filter
            remote_only: Only show remote jobs
            max_results: Maximum number of jobs to scrape

        Returns:
            List of job dictionaries

        Raises:
            Exception: If search fails
        """
        if not self.driver:
            raise Exception("Driver not initialized. Call login() first.")

        jobs = []

        try:
            # Build search query
            search_query = ' OR '.join(keywords[:5])  # Limit to top 5 keywords

            # Navigate to LinkedIn jobs search
            search_url = f'https://www.linkedin.com/jobs/search/?keywords={search_query}'

            if location:
                search_url += f'&location={location}'

            if remote_only:
                search_url += '&f_WT=2'  # LinkedIn remote filter

            print(f"🔍 Searching: {search_url}")
            self.driver.get(search_url)
            time.sleep(5)  # Increased wait time for page to fully load

            # Debug: Save page source and screenshot
            try:
                import os
                os.makedirs('/tmp/debug', exist_ok=True)
                with open('/tmp/debug/linkedin_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.driver.save_screenshot('/tmp/debug/linkedin_page.png')
                print("🔍 Debug: Saved page HTML and screenshot to /tmp/debug/")
            except Exception as e:
                print(f"⚠️  Debug save failed: {e}")

            # Check current URL (LinkedIn might redirect)
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}")

            # Wait for job listings to load - try multiple selectors
            job_list_found = False
            selectors_to_try = [
                (By.CLASS_NAME, 'jobs-search__results-list'),
                (By.CLASS_NAME, 'jobs-search-results-list'),
                (By.CSS_SELECTOR, 'ul.jobs-search__results-list'),
                (By.CSS_SELECTOR, 'div.jobs-search-results-list'),
                (By.CSS_SELECTOR, '[data-job-id]'),  # Any element with job ID
                (By.CSS_SELECTOR, '.jobs-search-results__list'),
                (By.CSS_SELECTOR, '.scaffold-layout__list'),
            ]

            for selector_type, selector_value in selectors_to_try:
                try:
                    print(f"🔍 Trying selector: {selector_type} = {selector_value}")
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"✅ Found jobs container with: {selector_value}")
                    job_list_found = True
                    break
                except TimeoutException:
                    continue

            if not job_list_found:
                print("⚠️  No job listings container found with any selector")
                print(f"📄 Page title: {self.driver.title}")
                return jobs

            # Scroll to load more jobs
            self._scroll_to_load_jobs()

            # Find all job cards - try multiple selectors
            job_card_selectors = [
                'li.jobs-search-results__list-item',
                'li[data-occludable-job-id]',
                'div.job-card-container',
                'div.jobs-search-results__list-item',
                'li.scaffold-layout__list-item',
                'div[data-job-id]',
                '.job-card-list__entity',
            ]

            job_cards = []
            for selector in job_card_selectors:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if job_cards:
                    print(f"📋 Found {len(job_cards)} job cards with selector: {selector}")
                    break
                else:
                    print(f"⚠️  No jobs found with selector: {selector}")

            if not job_cards:
                print("❌ No job cards found with any selector")
                return jobs

            for i, card in enumerate(job_cards[:max_results]):
                try:
                    job_data = self._extract_job_data(card, i)
                    if job_data:
                        jobs.append(job_data)
                        print(f"  ✓ Scraped: {job_data.get('job_title', 'Unknown')} at {job_data.get('company_name', 'Unknown')}")
                except Exception as e:
                    print(f"  ✗ Failed to extract job {i}: {str(e)}")
                    continue

            print(f"✅ Successfully scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            raise Exception(f"Job search failed: {str(e)}")

    def _scroll_to_load_jobs(self):
        """Scroll down to trigger lazy loading of more jobs"""
        try:
            for _ in range(3):  # Scroll 3 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
        except Exception:
            pass

    def _extract_job_data(self, card_element, index: int) -> Optional[Dict]:
        """
        Extract job data from a job card element.

        Args:
            card_element: Selenium WebElement for job card
            index: Index of card

        Returns:
            Dictionary with job data or None
        """
        try:
            # Click on card to load details
            card_element.click()
            time.sleep(2)

            # Extract job title
            job_title = None
            try:
                job_title_elem = card_element.find_element(By.CSS_SELECTOR, 'h3.base-search-card__title')
                job_title = job_title_elem.text.strip()
            except NoSuchElementException:
                pass

            # Extract company name
            company_name = None
            try:
                company_elem = card_element.find_element(By.CSS_SELECTOR, 'h4.base-search-card__subtitle')
                company_name = company_elem.text.strip()
            except NoSuchElementException:
                pass

            # Extract location
            location = None
            try:
                location_elem = card_element.find_element(By.CSS_SELECTOR, 'span.job-search-card__location')
                location = location_elem.text.strip()
            except NoSuchElementException:
                pass

            # Extract posted date
            posted_date = None
            try:
                date_elem = card_element.find_element(By.CSS_SELECTOR, 'time')
                posted_date = date_elem.get_attribute('datetime') or date_elem.text
            except NoSuchElementException:
                pass

            # Extract job URL
            job_url = None
            try:
                link_elem = card_element.find_element(By.CSS_SELECTOR, 'a.base-card__full-link')
                job_url = link_elem.get_attribute('href')
                # Clean URL (remove tracking parameters)
                if '?' in job_url:
                    job_url = job_url.split('?')[0]
            except NoSuchElementException:
                pass

            # Extract job description (from side panel)
            description = None
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.jobs-description__content')
                description = desc_elem.text.strip()
            except NoSuchElementException:
                pass

            # Check if remote
            is_remote = False
            if location:
                is_remote = 'remote' in location.lower()
            if description:
                is_remote = is_remote or 'remote' in description.lower()

            # Skip if essential data is missing
            if not job_title or not job_url:
                return None

            return {
                'linkedin_post_url': job_url,
                'job_title': job_title,
                'company_name': company_name,
                'location': location,
                'description': description[:5000] if description else None,  # Limit description length
                'posted_date': posted_date,
                'is_remote': is_remote,
                'employment_type': None,  # Can be extracted if available
                'seniority_level': None,  # Can be extracted if available
                'scraped_at': datetime.utcnow()
            }

        except Exception as e:
            print(f"    Error extracting job data: {str(e)}")
            return None

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
