import asyncio
import json
import os
import random
from datetime import datetime
from camoufox.async_api import AsyncCamoufox
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LinkedInJobScraper:
    def __init__(self, job_title: str, location: str, headless: bool = True, max_jobs: int = 100):
        self.job_title = job_title
        self.location = location
        self.jobs_data = []
        self.headless = headless
        self.max_jobs = max_jobs

    async def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def scrape_jobs(self):
        """Main function to scrape LinkedIn jobs using Camoufox"""
        # Launch Camoufox browser with anti-detection features
        mode = "headless" if self.headless else "visible"
        print(f"Launching Camoufox browser ({mode} mode)...")
        async with AsyncCamoufox(
            headless=self.headless,
            humanize=True,  # Enable human-like cursor movements
            os='windows',   # Simulate Windows environment
        ) as browser:
            page = await browser.new_page()

            try:
                # Login to LinkedIn if credentials are provided
                await self._login(page)

                # Build LinkedIn job search URL
                search_url = self._build_search_url()
                print(f"Navigating to: {search_url}")

                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)

                # Handle potential login wall or consent
                await self._handle_initial_popups(page)

                # Debug: Take a screenshot to see what we're working with
                await page.screenshot(path="debug_screenshot.png")
                print("Screenshot saved to debug_screenshot.png")

                # Debug: Check page title and URL
                print(f"Current URL: {page.url}")
                print(f"Page title: {await page.title()}")

                page_num = 1
                max_pages = 40  # LinkedIn typically shows up to ~1000 results (25 per page)

                while page_num <= max_pages and len(self.jobs_data) < self.max_jobs:
                    print(f"\n--- Scraping page {page_num} ---")

                    # Wait for job listings to load with multiple selectors
                    print("Waiting for job listings to load...")
                    try:
                        await page.wait_for_selector('div.scaffold-layout__list, ul.jobs-search__results-list, div.jobs-search__results-list, ul.scaffold-layout__list-container', timeout=15000)
                        print("✓ Job listing container found")
                    except Exception as e:
                        print(f"✗ Could not find job listing container: {str(e)}")
                        # Debug: Print page content
                        html_content = await page.content()
                        with open("debug_page_content.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
                        print("Page HTML saved to debug_page_content.html for inspection")
                        break

                    # Try multiple selectors for job cards
                    print("Looking for job cards with various selectors...")
                    job_cards = await page.query_selector_all('li.jobs-search-results__list-item, div.job-search-card, li.scaffold-layout__list-item, div.base-card, li.jobs-search-results__list-item')

                    if not job_cards:
                        print("✗ No job cards found with standard selectors.")
                        print("Trying alternative selectors...")

                        # Try even more specific selectors
                        job_cards = await page.query_selector_all('li[class*="job"], div[class*="job-card"], ul[class*="jobs"] > li')

                        if not job_cards:
                            print("✗ Still no job cards found. Saving debug info...")
                            html_content = await page.content()
                            with open("debug_no_cards.html", "w", encoding="utf-8") as f:
                                f.write(html_content)
                            print("Page HTML saved to debug_no_cards.html for inspection")
                            break

                    print(f"✓ Found {len(job_cards)} job cards on page {page_num}")

                    # Process each job card
                    for idx, card in enumerate(job_cards):
                        # Stop if we've reached max jobs
                        if len(self.jobs_data) >= self.max_jobs:
                            print(f"\n✓ Reached max jobs limit ({self.max_jobs}). Stopping.")
                            return self.jobs_data

                        try:
                            job_data = await self._extract_job_data(page, card, idx + 1)
                            if job_data:
                                self.jobs_data.append(job_data)
                                print(f"  ✓ Scraped job {len(self.jobs_data)}: {job_data['title']}")

                                # Random delay between jobs to avoid detection
                                await self._random_delay(2.0, 4.0)
                        except Exception as e:
                            print(f"  ✗ Error scraping job {idx + 1}: {str(e)}")
                            # Check if browser is still alive
                            try:
                                await page.title()
                            except:
                                print(f"  ✗ Browser connection lost. Stopping scrape.")
                                return self.jobs_data
                            continue

                    # Try to go to next page
                    if not await self._go_to_next_page(page, page_num):
                        print("No more pages available.")
                        break

                    page_num += 1
                    # Random delay between pages to avoid detection
                    await self._random_delay(3.0, 5.0)

                print(f"\n✓ Scraping completed! Total jobs scraped: {len(self.jobs_data)}")

            except Exception as e:
                print(f"Error during scraping: {str(e)}")

            return self.jobs_data

    def _build_search_url(self) -> str:
        """Build LinkedIn job search URL with parameters"""
        base_url = "https://www.linkedin.com/jobs/search/"
        # URL encode the parameters
        job_title_encoded = self.job_title.replace(" ", "%20")
        location_encoded = self.location.replace(" ", "%20")

        url = f"{base_url}?keywords={job_title_encoded}&location={location_encoded}&f_AL=true"
        return url

    async def _handle_initial_popups(self, page):
        """Handle login prompts, consent dialogs, etc."""
        try:
            # Try to close any modal dialogs
            close_buttons = await page.query_selector_all('button[aria-label="Dismiss"], button[data-tracking-control-name="public_jobs_contextual-sign-in-modal_modal_dismiss"]')
            for button in close_buttons:
                try:
                    await button.click()
                    await asyncio.sleep(1)
                except:
                    pass
        except:
            pass

    async def _login(self, page):
        """Login to LinkedIn using credentials from .env file"""
        email = os.getenv('LINKEDIN_EMAIL')
        password = os.getenv('LINKEDIN_PASSWORD')

        if not email or not password:
            print("Warning: LinkedIn credentials not found in .env file")
            print("Proceeding without login (limited access to job listings)")
            return False

        if email == 'your_email@example.com' or password == 'your_password_here':
            print("Warning: Please update your LinkedIn credentials in the .env file")
            print("Proceeding without login (limited access to job listings)")
            return False

        try:
            print("Logging in to LinkedIn...")

            # Navigate to LinkedIn login page
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Fill in email
            email_input = await page.query_selector('input#username')
            if email_input:
                await email_input.fill(email)
                await asyncio.sleep(0.5)
            else:
                print("Error: Could not find email input field")
                return False

            # Fill in password
            password_input = await page.query_selector('input#password')
            if password_input:
                await password_input.fill(password)
                await asyncio.sleep(0.5)
            else:
                print("Error: Could not find password input field")
                return False

            # Click login button
            login_button = await page.query_selector('button[type="submit"]')
            if login_button:
                await login_button.click()
                await asyncio.sleep(5)  # Wait for login to complete
            else:
                print("Error: Could not find login button")
                return False

            # Check if login was successful
            # If we're redirected to the feed or if we can see the navigation bar, login succeeded
            current_url = page.url
            if 'feed' in current_url or 'checkpoint' in current_url:
                print("Login successful!")

                # Handle any post-login verification if needed
                if 'checkpoint' in current_url:
                    print("LinkedIn requires additional verification.")
                    print("Please complete the verification in the browser window.")
                    print("Waiting 30 seconds for manual verification...")
                    await asyncio.sleep(30)

                return True
            else:
                # Check if there's an error message
                error_elem = await page.query_selector('.alert-content, .form__label--error')
                if error_elem:
                    error_text = await error_elem.inner_text()
                    print(f"Login failed: {error_text}")
                else:
                    print("Login may have failed - please check credentials")
                return False

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    async def _extract_job_data(self, page, card, job_index: int) -> Dict:
        """Extract job data from a job card"""
        job_data = {
            "title": "",
            "company": "",
            "location": "",
            "description": "",
            "job_url": "",
            "posted_date": "",
            "scraped_at": datetime.now().isoformat()
        }

        try:
            # Click on the job card to load details using JavaScript (more reliable)
            print(f"  [{job_index}] Clicking job card...")
            try:
                await card.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.3, 0.7))  # Random delay before click
                await page.evaluate('(element) => element.click()', card)
                await asyncio.sleep(random.uniform(2.5, 4.0))  # Random wait for job details to load
            except Exception as e:
                print(f"  [{job_index}] Error clicking card: {str(e)}")
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
                        if text and len(text) > 3:  # Ensure it's not empty or too short
                            job_data["title"] = text
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
                            job_data["company"] = text
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
                            job_data["job_url"] = href
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
                # Wait for description to load
                print(f"  [{job_index}] Waiting for description...")
                await page.wait_for_selector('div.jobs-description__content, div.jobs-box__html-content, #job-details', timeout=8000)

                # Wait a bit more for content to fully render
                await asyncio.sleep(0.5)

                # Try to expand "Show more" button if present (optional, may not exist)
                try:
                    show_more_btn = await page.query_selector('button.show-more-less-html__button--more, button[aria-label*="Show more"], button[data-tracking-control-name*="see-more"]')
                    if show_more_btn:
                        is_visible = await show_more_btn.is_visible()
                        if is_visible:
                            await show_more_btn.click()
                            await asyncio.sleep(0.5)
                except:
                    pass  # "Show more" button may not exist, that's OK

                # Try multiple selectors for description (ordered by specificity)
                description_selectors = [
                    '#job-details',  # Most specific - the actual content div
                    'div.jobs-box__html-content',  # Container with full HTML content
                    'div.jobs-description__content',  # Description content wrapper
                    'div.jobs-details__main-content',  # Main content area
                    'div.show-more-less-html__markup',  # Alternative selector
                    'article.jobs-description',  # Article wrapper
                    'div.description__text',  # Alternative description container
                    'div[class*="jobs-description"]',  # Fallback pattern match
                ]

                for selector in description_selectors:
                    desc_elem = await page.query_selector(selector)
                    if desc_elem:
                        text = (await desc_elem.inner_text()).strip()
                        if text and len(text) > 100:  # Ensure it's a substantial description (increased from 50)
                            job_data["description"] = text
                            print(f"      ✓ Description extracted ({len(text)} chars) using selector: {selector}")
                            break

                if not job_data["description"]:
                    print(f"      ✗ Could not extract description from any selector")
                    # Debug: save HTML of the details panel
                    panel_html = await page.query_selector('div.jobs-details')
                    if panel_html:
                        panel_content = await page.evaluate('(element) => element.outerHTML', panel_html)
                        print(f"      Debug: Found jobs-details panel but no description content")

            except Exception as e:
                print(f"      Warning: Could not extract description - {str(e)}")

        except Exception as e:
            print(f"    Error extracting job data: {str(e)}")

        # Debug: Show what we extracted
        if job_data["title"]:
            print(f"      Extracted: {job_data['title'][:50]}... at {job_data['company']}")
            return job_data
        else:
            print(f"      ✗ Failed to extract title - skipping this job")
            return None

    async def _go_to_next_page(self, page, current_page: int) -> bool:
        """Navigate to the next page of results"""
        try:
            # LinkedIn uses pagination buttons
            next_button = await page.query_selector(f'button[aria-label="Page {current_page + 1}"], li[data-test-pagination-page-btn="{current_page + 1}"] button')

            if not next_button:
                # Try alternative next button selector
                next_button = await page.query_selector('button[aria-label="View next page"]')

            if next_button:
                await next_button.click()
                await asyncio.sleep(3)  # Wait for new page to load
                return True
            else:
                return False

        except Exception as e:
            print(f"Error navigating to next page: {str(e)}")
            return False

    def save_to_json(self, filename: str = None):
        """Save scraped jobs to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_jobs_{self.job_title.replace(' ', '_')}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Data saved to {filename}")
        return filename


async def main():
    """Main entry point"""
    print("=" * 60)
    print("LinkedIn Job Scraper with Camoufox")
    print("=" * 60)

    # Get user input
    job_title = input("\nEnter job title/position: ").strip()
    location = input("Enter location: ").strip()

    if not job_title or not location:
        print("Error: Both job title and location are required!")
        return

    # Configuration options
    headless_input = input("Run in headless mode? (y/n) [default: y]: ").strip().lower()
    headless = headless_input != 'n'

    max_jobs_input = input("Maximum jobs to scrape? [default: 100]: ").strip()
    max_jobs = int(max_jobs_input) if max_jobs_input.isdigit() else 100

    # Create scraper instance
    scraper = LinkedInJobScraper(job_title, location, headless=headless, max_jobs=max_jobs)

    # Start scraping
    print(f"\nSearching for '{job_title}' jobs in '{location}'...")
    print(f"Config: headless={headless}, max_jobs={max_jobs}")
    jobs = await scraper.scrape_jobs()

    # Save results
    if jobs:
        filename = scraper.save_to_json()
        print(f"\nTotal jobs scraped: {len(jobs)}")
        print(f"Output file: {filename}")
    else:
        print("\nNo jobs were scraped.")


if __name__ == "__main__":
    asyncio.run(main())
