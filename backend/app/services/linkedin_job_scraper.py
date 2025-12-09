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
        max_results: int = 100,  # Increased from 20 to 100
        date_posted: str = 'week',  # 'day', 'week', 'month', 'any'
        experience_level: Optional[str] = None,  # 'entry', 'mid', 'senior', 'director', 'executive'
        job_type: Optional[str] = None,  # 'full_time', 'part_time', 'contract', 'temporary'
        sort_by: str = 'date'  # 'date' or 'relevance'
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn with advanced filters.

        Args:
            keywords: Search keywords (from resume analysis)
            location: Location filter
            remote_only: Only show remote jobs
            max_results: Maximum number of jobs to scrape
            date_posted: Filter by posting date ('day', 'week', 'month', 'any')
            experience_level: Filter by experience level
            job_type: Filter by employment type
            sort_by: Sort results by 'date' or 'relevance'

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

            # Build LinkedIn search URL with advanced filters
            search_url = self._build_search_url(
                keywords=search_query,
                location=location,
                remote_only=remote_only,
                date_posted=date_posted,
                experience_level=experience_level,
                job_type=job_type,
                sort_by=sort_by
            )

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

    def _build_search_url(
        self,
        keywords: str,
        location: Optional[str] = None,
        remote_only: bool = False,
        date_posted: str = 'week',
        experience_level: Optional[str] = None,
        job_type: Optional[str] = None,
        sort_by: str = 'date'
    ) -> str:
        """
        Build LinkedIn search URL with advanced filters.

        LinkedIn Filter Codes:
        - f_TPR: Time Posted Recently
          - r86400 = past 24 hours
          - r604800 = past week
          - r2592000 = past month
        - f_E: Experience Level
          - 1 = Internship
          - 2 = Entry level
          - 3 = Associate
          - 4 = Mid-Senior level
          - 5 = Director
          - 6 = Executive
        - f_JT: Job Type
          - F = Full-time
          - P = Part-time
          - C = Contract
          - T = Temporary
          - I = Internship
          - V = Volunteer
          - O = Other
        - f_WT: Workplace Type
          - 1 = On-site
          - 2 = Remote
          - 3 = Hybrid
        - sortBy: Sort order
          - DD = Date Descending (most recent)
          - R = Relevance
        """
        from urllib.parse import quote

        base_url = 'https://www.linkedin.com/jobs/search/'
        params = []

        # Keywords
        if keywords:
            params.append(f'keywords={quote(keywords)}')

        # Location
        if location:
            params.append(f'location={quote(location)}')

        # Date posted filter
        date_filters = {
            'day': 'r86400',
            'week': 'r604800',
            'month': 'r2592000',
            'any': ''
        }
        if date_posted in date_filters and date_filters[date_posted]:
            params.append(f'f_TPR={date_filters[date_posted]}')

        # Experience level filter
        experience_filters = {
            'entry': '2',
            'associate': '3',
            'mid': '3,4',
            'senior': '4,5',
            'director': '5',
            'executive': '6'
        }
        if experience_level and experience_level in experience_filters:
            params.append(f'f_E={experience_filters[experience_level]}')

        # Job type filter
        job_type_filters = {
            'full_time': 'F',
            'part_time': 'P',
            'contract': 'C',
            'temporary': 'T',
            'internship': 'I'
        }
        if job_type and job_type in job_type_filters:
            params.append(f'f_JT={job_type_filters[job_type]}')

        # Remote/Workplace type
        if remote_only:
            params.append('f_WT=2')

        # Sort by
        if sort_by == 'date':
            params.append('sortBy=DD')
        elif sort_by == 'relevance':
            params.append('sortBy=R')

        # Combine all parameters
        url = f"{base_url}?{'&'.join(params)}"
        return url

    def _scroll_to_load_jobs(self):
        """Scroll down to trigger lazy loading of more jobs"""
        try:
            print("📜 Scrolling to load more jobs...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for scroll_num in range(8):  # Increased from 3 to 8 scrolls
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Increased wait time from 1s to 2s

                # Check if new content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    # No new content, try clicking "Show more" button if exists
                    try:
                        show_more_buttons = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'button.infinite-scroller__show-more-button, button[aria-label*="Show more"], button.scaffold-finite-scroll__load-button'
                        )
                        if show_more_buttons:
                            show_more_buttons[0].click()
                            print(f"  ✓ Clicked 'Show more' button")
                            time.sleep(3)  # Wait for new jobs to load
                    except Exception:
                        pass

                last_height = new_height
                print(f"  ✓ Scroll {scroll_num + 1}/8 complete")

        except Exception as e:
            print(f"⚠️  Scrolling error: {e}")

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
