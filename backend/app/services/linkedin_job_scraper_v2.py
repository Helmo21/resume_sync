"""
LinkedIn Job Scraper V2 - Dual Mode with Fallback
Primary: Camoufox (anti-detection, Firefox-based)
Fallback: Selenium (Chrome-based)

Risk Mitigation:
- Camoufox might not work in Docker → Automatic Selenium fallback
- LinkedIn blocks scraping → Multiple selector fallbacks, service account rotation
"""
import asyncio
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

# Camoufox (Primary)
from camoufox.async_api import AsyncCamoufox

# Selenium (Fallback)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class ScraperMode(Enum):
    CAMOUFOX = "camoufox"
    SELENIUM = "selenium"


class LinkedInJobScraperV2:
    """
    Advanced LinkedIn Job Scraper with automatic fallback
    """

    def __init__(self, headless: bool = True, max_jobs: int = 100):
        self.headless = headless
        self.max_jobs = max_jobs
        self.mode = None  # Will be set after first successful scrape

    async def scrape_jobs(
        self,
        email: str,
        password: str,
        job_title: str,
        location: str
    ) -> tuple[List[Dict], ScraperMode]:
        """
        Scrape jobs with automatic fallback

        Returns:
            (jobs_list, mode_used)
        """
        # Try Camoufox first (more reliable, anti-detection)
        try:
            print("🦊 Attempting scrape with Camoufox (anti-detection mode)...")
            jobs = await self._scrape_with_camoufox(email, password, job_title, location)
            print(f"✅ Camoufox succeeded! Scraped {len(jobs)} jobs")
            self.mode = ScraperMode.CAMOUFOX
            return jobs, ScraperMode.CAMOUFOX
        except Exception as e:
            print(f"⚠️  Camoufox failed: {str(e)}")
            print("🔄 Falling back to Selenium...")

            # Fallback to Selenium
            try:
                jobs = await self._scrape_with_selenium(email, password, job_title, location)
                print(f"✅ Selenium succeeded! Scraped {len(jobs)} jobs")
                self.mode = ScraperMode.SELENIUM
                return jobs, ScraperMode.SELENIUM
            except Exception as selenium_error:
                print(f"❌ Selenium also failed: {str(selenium_error)}")
                raise Exception(
                    f"Both scrapers failed. Camoufox: {str(e)}. Selenium: {str(selenium_error)}"
                )

    async def _scrape_with_camoufox(
        self,
        email: str,
        password: str,
        job_title: str,
        location: str
    ) -> List[Dict]:
        """Scrape using Camoufox (anti-detection browser)"""
        jobs_data = []

        async with AsyncCamoufox(
            headless=self.headless,
            humanize=True,  # Human-like cursor movements
            os='windows',   # Simulate Windows
        ) as browser:
            page = await browser.new_page()

            # Login
            await self._camoufox_login(page, email, password)

            # Build search URL
            job_title_encoded = job_title.replace(" ", "%20")
            location_encoded = location.replace(" ", "%20")
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title_encoded}&location={location_encoded}&f_AL=true"

            print(f"🔍 Searching: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            # Handle popups
            await self._handle_popups(page)

            # Scrape job cards with pagination
            page_num = 1
            max_pages = min(5, (self.max_jobs // 25) + 1)  # LinkedIn shows ~25 per page

            while page_num <= max_pages and len(jobs_data) < self.max_jobs:
                print(f"📄 Scraping page {page_num}...")

                # Wait for job listings
                await page.wait_for_selector(
                    'div.scaffold-layout__list, ul.jobs-search__results-list',
                    timeout=15000
                )

                # Get job cards with multiple selectors (LinkedIn changes these often)
                job_cards = await page.query_selector_all(
                    'li.jobs-search-results__list-item, '
                    'li.scaffold-layout__list-item, '
                    'div.job-search-card, '
                    'li[data-occludable-job-id]'
                )

                print(f"  Found {len(job_cards)} job cards")

                for idx, card in enumerate(job_cards):
                    if len(jobs_data) >= self.max_jobs:
                        break

                    try:
                        job_data = await self._extract_job_data_camoufox(page, card, idx)
                        if job_data:
                            jobs_data.append(job_data)
                            print(f"  ✓ Scraped: {job_data['job_title'][:50]}")

                            # Random delay (anti-detection)
                            await asyncio.sleep(random.uniform(2.0, 4.0))
                    except Exception as e:
                        print(f"  ✗ Error on job {idx}: {str(e)}")
                        continue

                # Try next page
                if not await self._go_to_next_page_camoufox(page, page_num):
                    break

                page_num += 1
                await asyncio.sleep(random.uniform(3.0, 5.0))

        return jobs_data

    async def _camoufox_login(self, page, email: str, password: str):
        """Login to LinkedIn with Camoufox"""
        print("🔐 Logging in with Camoufox...")
        await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Fill credentials
        email_input = await page.query_selector('input#username')
        if email_input:
            await email_input.fill(email)
            await asyncio.sleep(0.5)

        password_input = await page.query_selector('input#password')
        if password_input:
            await password_input.fill(password)
            await asyncio.sleep(0.5)

        # Submit
        login_button = await page.query_selector('button[type="submit"]')
        if login_button:
            await login_button.click()
            await asyncio.sleep(5)

        # Check for checkpoint
        current_url = page.url
        if 'checkpoint' in current_url or 'challenge' in current_url:
            raise Exception("LinkedIn security challenge detected")

        if 'feed' not in current_url and 'linkedin.com' not in current_url:
            raise Exception(f"Login may have failed. URL: {current_url}")

    async def _handle_popups(self, page):
        """Close any modal dialogs"""
        try:
            close_buttons = await page.query_selector_all(
                'button[aria-label="Dismiss"], '
                'button[data-tracking-control-name*="modal_dismiss"]'
            )
            for button in close_buttons:
                try:
                    await button.click()
                    await asyncio.sleep(1)
                except:
                    pass
        except:
            pass

    async def _extract_job_data_camoufox(self, page, card, index: int) -> Optional[Dict]:
        """Extract job data from Camoufox page - WORKING VERSION from test folder"""
        job_data = {
            "job_title": None,
            "company_name": None,
            "location": None,
            "description": None,
            "linkedin_post_url": None,
            "posted_date": None,
            "is_remote": False,
            "scraped_at": datetime.utcnow()
        }

        try:
            # Click on the job card to load details using JavaScript (more reliable)
            print(f"  [{index}] Clicking job card...")
            try:
                await card.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.3, 0.7))
                await page.evaluate('(element) => element.click()', card)
                await asyncio.sleep(random.uniform(2.5, 4.0))
            except Exception as e:
                print(f"  [{index}] Error clicking card: {str(e)}")
                return None

            # Extract job title - try multiple selectors
            try:
                title_selectors = [
                    'h3.base-search-card__title',
                    'a.base-card__full-link',
                    'h3[class*="job-card-list__title"]',
                    'a.job-card-list__title',
                    'div.base-card__title',
                    'span.sr-only',
                    'a[class*="job-card-container__link"] strong'
                ]
                for selector in title_selectors:
                    title_elem = await card.query_selector(selector)
                    if title_elem:
                        text = (await title_elem.inner_text()).strip()
                        if text and len(text) > 3:
                            job_data["job_title"] = text
                            break
            except Exception as e:
                print(f"      Error extracting title: {str(e)}")

            # Extract company name - try multiple selectors
            try:
                company_selectors = [
                    'h4.base-search-card__subtitle',
                    'a.hidden-nested-link',
                    'span.job-card-container__company-name',
                    'h4[class*="job-card-container__company-name"]',
                    'div.base-card__subtitle'
                ]
                for selector in company_selectors:
                    company_elem = await card.query_selector(selector)
                    if company_elem:
                        text = (await company_elem.inner_text()).strip()
                        if text:
                            job_data["company_name"] = text
                            break
            except Exception as e:
                print(f"      Error extracting company: {str(e)}")

            # Extract location - try multiple selectors
            try:
                location_selectors = [
                    'span.job-search-card__location',
                    'div.base-card__metadata span',
                    'span[class*="job-card-container__metadata-item"]',
                    'li.job-card-container__metadata-item'
                ]
                for selector in location_selectors:
                    location_elem = await card.query_selector(selector)
                    if location_elem:
                        text = (await location_elem.inner_text()).strip()
                        if text:
                            job_data["location"] = text
                            job_data["is_remote"] = 'remote' in text.lower()
                            break
            except Exception as e:
                print(f"      Error extracting location: {str(e)}")

            # Extract job URL - try multiple selectors
            try:
                url_selectors = [
                    'a.base-card__full-link',
                    'a[class*="job-card-container__link"]',
                    'a[href*="/jobs/view/"]'
                ]
                for selector in url_selectors:
                    link_elem = await card.query_selector(selector)
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            # Clean URL
                            clean_url = href.split('?')[0] if '?' in href else href
                            # Convert relative URL to absolute LinkedIn URL
                            if clean_url.startswith('/'):
                                clean_url = f"https://www.linkedin.com{clean_url}"
                            job_data["linkedin_post_url"] = clean_url
                            break
            except Exception as e:
                print(f"      Error extracting URL: {str(e)}")

            # Extract posted date
            try:
                date_elem = await card.query_selector('time.job-search-card__listdate, time')
                if date_elem:
                    job_data["posted_date"] = await date_elem.get_attribute('datetime') or (await date_elem.inner_text()).strip()
            except Exception as e:
                print(f"      Error extracting date: {str(e)}")

            # Extract job description from the details panel
            try:
                print(f"  [{index}] Waiting for description...")
                await page.wait_for_selector('div.jobs-description__content, div.jobs-box__html-content, #job-details', timeout=8000)
                await asyncio.sleep(0.5)

                # Try to expand "Show more" button if present
                try:
                    show_more_btn = await page.query_selector('button.show-more-less-html__button--more, button[aria-label*="Show more"], button[data-tracking-control-name*="see-more"]')
                    if show_more_btn:
                        is_visible = await show_more_btn.is_visible()
                        if is_visible:
                            await show_more_btn.click()
                            await asyncio.sleep(0.5)
                except:
                    pass

                # Try multiple selectors for description (ordered by specificity)
                description_selectors = [
                    '#job-details',
                    'div.jobs-box__html-content',
                    'div.jobs-description__content',
                    'div.jobs-details__main-content',
                    'div.show-more-less-html__markup',
                    'article.jobs-description',
                    'div.description__text',
                    'div[class*="jobs-description"]',
                ]

                for selector in description_selectors:
                    desc_elem = await page.query_selector(selector)
                    if desc_elem:
                        text = (await desc_elem.inner_text()).strip()
                        if text and len(text) > 100:
                            job_data["description"] = text[:5000]
                            print(f"      ✓ Description extracted ({len(text)} chars) using selector: {selector}")
                            break

                if not job_data["description"]:
                    print(f"      ✗ Could not extract description from any selector")

            except Exception as e:
                print(f"      Warning: Could not extract description - {str(e)}")

        except Exception as e:
            print(f"    Error extracting job data: {str(e)}")

        # Validate - only require title (like the working version)
        if job_data["job_title"]:
            print(f"      Extracted: {job_data['job_title'][:50]}... at {job_data['company_name']}")
            return job_data
        else:
            print(f"      ✗ Failed to extract title - skipping this job")
            return None

    async def _go_to_next_page_camoufox(self, page, current_page: int) -> bool:
        """Navigate to next page"""
        try:
            next_button = await page.query_selector(f'button[aria-label="Page {current_page + 1}"]')
            if not next_button:
                next_button = await page.query_selector('button[aria-label="View next page"]')

            if next_button:
                await next_button.click()
                await asyncio.sleep(3)
                return True
            return False
        except:
            return False

    async def _scrape_with_selenium(
        self,
        email: str,
        password: str,
        job_title: str,
        location: str
    ) -> List[Dict]:
        """Scrape using Selenium (fallback)"""
        print("🌐 Starting Selenium scraper...")

        # Run in asyncio executor to avoid blocking
        loop = asyncio.get_event_loop()
        jobs = await loop.run_in_executor(
            None,
            self._selenium_sync_scrape,
            email, password, job_title, location
        )
        return jobs

    def _selenium_sync_scrape(
        self,
        email: str,
        password: str,
        job_title: str,
        location: str
    ) -> List[Dict]:
        """Synchronous Selenium scrape (runs in executor)"""
        chrome_options = ChromeOptions()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)

        try:
            # Login
            driver.get('https://www.linkedin.com/login')
            time.sleep(2)

            driver.find_element(By.ID, 'username').send_keys(email)
            driver.find_element(By.ID, 'password').send_keys(password)
            driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
            time.sleep(5)

            # Check login
            if 'checkpoint' in driver.current_url or 'challenge' in driver.current_url:
                raise Exception("LinkedIn security challenge")

            # Search
            search_url = f'https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}&f_AL=true'
            driver.get(search_url)
            time.sleep(5)

            # Wait for results
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.jobs-search-results__list-item, li.scaffold-layout__list-item'))
            )

            # Scroll to load
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # Get cards
            job_cards = driver.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item, li.scaffold-layout__list-item')
            print(f"  Found {len(job_cards)} job cards with Selenium")

            jobs_data = []
            for i, card in enumerate(job_cards[:self.max_jobs]):
                try:
                    job_data = self._extract_selenium_job(driver, card, i)
                    if job_data:
                        jobs_data.append(job_data)
                        print(f"  ✓ Scraped: {job_data['job_title'][:50]}")
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    print(f"  ✗ Error: {str(e)}")
                    continue

            return jobs_data

        finally:
            driver.quit()

    def _extract_selenium_job(self, driver, card, index: int) -> Optional[Dict]:
        """Extract job data with Selenium"""
        try:
            card.click()
            time.sleep(2)

            job_data = {
                "job_title": None,
                "company_name": None,
                "location": None,
                "description": None,
                "linkedin_post_url": None,
                "posted_date": None,
                "is_remote": False,
                "scraped_at": datetime.utcnow()
            }

            # Extract fields
            try:
                job_data["job_title"] = card.find_element(By.CSS_SELECTOR, 'h3.base-search-card__title').text.strip()
            except NoSuchElementException:
                pass

            try:
                job_data["company_name"] = card.find_element(By.CSS_SELECTOR, 'h4.base-search-card__subtitle').text.strip()
            except NoSuchElementException:
                pass

            try:
                location_text = card.find_element(By.CSS_SELECTOR, 'span.job-search-card__location').text.strip()
                job_data["location"] = location_text
                job_data["is_remote"] = 'remote' in location_text.lower()
            except NoSuchElementException:
                pass

            try:
                link = card.find_element(By.CSS_SELECTOR, 'a.base-card__full-link')
                href = link.get_attribute('href')
                job_data["linkedin_post_url"] = href.split('?')[0] if '?' in href else href
            except NoSuchElementException:
                pass

            try:
                desc = driver.find_element(By.CSS_SELECTOR, 'div.jobs-description__content')
                job_data["description"] = desc.text.strip()[:5000]
            except NoSuchElementException:
                pass

            try:
                date_elem = card.find_element(By.CSS_SELECTOR, 'time')
                job_data["posted_date"] = date_elem.get_attribute('datetime') or date_elem.text
            except NoSuchElementException:
                pass

            if not job_data["job_title"] or not job_data["linkedin_post_url"]:
                return None

            return job_data

        except Exception as e:
            print(f"    Selenium extraction error: {str(e)}")
            return None
