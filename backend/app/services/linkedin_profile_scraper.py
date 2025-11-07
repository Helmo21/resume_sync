"""
LinkedIn Profile Scraper using Camoufox with Service Account
Similar pattern to job scraper for reliability
"""
import asyncio
import time
from typing import Dict, Optional
from camoufox.async_api import AsyncCamoufox
from datetime import datetime


class LinkedInProfileScraper:
    """
    LinkedIn profile scraper using Camoufox with service account authentication
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape_profile(
        self,
        profile_url: str,
        email: str,
        password: str
    ) -> Dict:
        """
        Scrape a LinkedIn profile using Camoufox

        Args:
            profile_url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
            email: LinkedIn service account email
            password: LinkedIn service account password

        Returns:
            dict: Profile data with experiences, education, skills, etc.
        """
        print(f"\n🦊 Starting Camoufox profile scrape")
        print(f"   Profile: {profile_url}")
        print(f"   Account: {email}")

        async with AsyncCamoufox(
            headless=self.headless,
            humanize=True,  # Human-like movements
            os='windows',   # Simulate Windows
        ) as browser:
            page = await browser.new_page()

            try:
                # Step 1: Login
                await self._login(page, email, password)

                # Step 2: Navigate to profile
                print(f"\n📋 Navigating to profile...")
                await page.goto(profile_url, timeout=30000)
                await asyncio.sleep(3)  # Wait for page to fully load

                # Step 3: Scrape profile data
                profile_data = await self._scrape_profile_data(page, profile_url)

                print(f"\n✅ Profile scraping completed!")
                return profile_data

            except Exception as e:
                print(f"\n❌ Scraping failed: {e}")
                raise
            finally:
                await page.close()

    async def _login(self, page, email: str, password: str):
        """Login to LinkedIn"""
        print(f"\n🔐 Logging in to LinkedIn...")

        await page.goto("https://www.linkedin.com/login", timeout=30000)
        await asyncio.sleep(2)

        # Enter credentials
        await page.fill('input[id="username"]', email)
        await asyncio.sleep(0.5)
        await page.fill('input[id="password"]', password)
        await asyncio.sleep(0.5)

        # Click login
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)  # Wait for login

        # Check if login was successful
        current_url = page.url
        if "/checkpoint/challenge" in current_url:
            raise Exception("LinkedIn security challenge detected. Please verify the account manually.")
        elif "/login" in current_url:
            raise Exception("Login failed. Check credentials.")

        print("✓ Login successful")

    async def _scrape_profile_data(self, page, profile_url: str) -> Dict:
        """Scrape all profile data"""
        profile_data = {
            "profile_url": profile_url,
            "scraped_at": datetime.utcnow().isoformat(),
            "full_name": "",
            "headline": "",
            "location": "",
            "about": "",
            "experiences": [],
            "education": [],
            "skills": [],
            "connections": ""
        }

        try:
            # Full name - Try multiple selectors
            try:
                # Try selector 1: Standard heading
                name_elem = await page.query_selector('h1.text-heading-xlarge')
                if not name_elem:
                    # Try selector 2: Inside main section
                    name_elem = await page.query_selector('div.mt2.relative h1')
                if name_elem:
                    profile_data["full_name"] = (await name_elem.text_content()).strip()
                    print(f"✓ Name: {profile_data['full_name']}")
                else:
                    # Fallback: extract from URL
                    url_parts = profile_url.split('/in/')
                    if len(url_parts) > 1:
                        name_slug = url_parts[1].split('/')[0].split('?')[0]
                        # Convert slug to name (approximate)
                        profile_data["full_name"] = name_slug.replace('-', ' ').title()
                        print(f"✓ Name (from URL): {profile_data['full_name']}")
            except Exception as e:
                print(f"   ⚠️  Error getting name: {e}")
                pass

            # Headline
            try:
                headline_elem = await page.query_selector('div.text-body-medium')
                if headline_elem:
                    profile_data["headline"] = (await headline_elem.text_content()).strip()
                    print(f"✓ Headline: {profile_data['headline'][:50]}...")
            except:
                pass

            # Location
            try:
                location_elem = await page.query_selector('span.text-body-small.inline.t-black--light.break-words')
                if location_elem:
                    profile_data["location"] = (await location_elem.text_content()).strip()
                    print(f"✓ Location: {profile_data['location']}")
            except Exception as e:
                print(f"   ⚠️  Error getting location: {e}")
                pass

            # Connections
            try:
                conn_elem = await page.query_selector('span.t-black--light span.t-bold')
                if conn_elem:
                    profile_data["connections"] = (await conn_elem.text_content()).strip()
            except:
                pass

            # About section
            try:
                about_section = await page.query_selector('section:has(#about)')
                if about_section:
                    about_text = await about_section.query_selector('div.display-flex.ph5.pv3 span[aria-hidden="true"]')
                    if about_text:
                        profile_data["about"] = (await about_text.text_content()).strip()
                        print(f"✓ About: {len(profile_data['about'])} chars")
            except:
                pass

            # Experiences
            try:
                exp_section = await page.query_selector('section:has(#experience)')
                if exp_section:
                    exp_items = await exp_section.query_selector_all('li.artdeco-list__item')

                    for item in exp_items[:10]:  # Limit to 10 experiences
                        try:
                            exp_data = {}

                            # Title
                            title_elem = await item.query_selector('div[data-field="experience_company_logo"] span[aria-hidden="true"]')
                            if title_elem:
                                exp_data["title"] = (await title_elem.text_content()).strip()

                            # Company
                            company_elem = await item.query_selector('span.t-14.t-normal span[aria-hidden="true"]')
                            if company_elem:
                                exp_data["company"] = (await company_elem.text_content()).strip()

                            # Date range
                            date_elem = await item.query_selector('span.t-14.t-normal.t-black--light span[aria-hidden="true"]')
                            if date_elem:
                                date_text = (await date_elem.text_content()).strip()
                                if " - " in date_text:
                                    parts = date_text.split(" - ")
                                    exp_data["start_date"] = parts[0].strip()
                                    exp_data["end_date"] = parts[1].strip() if len(parts) > 1 else "Present"
                                else:
                                    exp_data["start_date"] = date_text
                                    exp_data["end_date"] = "Present"

                            # Location
                            location_elem = await item.query_selector('span.t-14.t-normal span[aria-hidden="true"]')
                            if location_elem:
                                exp_data["location"] = (await location_elem.text_content()).strip()

                            # Description
                            desc_elem = await item.query_selector('div.display-flex.full-width span[aria-hidden="true"]')
                            if desc_elem:
                                exp_data["description"] = (await desc_elem.text_content()).strip()

                            if exp_data.get("title") or exp_data.get("company"):
                                profile_data["experiences"].append(exp_data)

                        except Exception as e:
                            print(f"   ⚠️  Error parsing experience item: {e}")
                            continue

                    print(f"✓ Experiences: {len(profile_data['experiences'])}")
            except Exception as e:
                print(f"   ⚠️  Error scraping experiences: {e}")

            # Education (Formation)
            try:
                edu_section = await page.query_selector('section:has(#education)')
                if edu_section:
                    edu_items = await edu_section.query_selector_all('li.artdeco-list__item')

                    for item in edu_items[:10]:  # Limit to 10 education entries
                        try:
                            edu_data = {}

                            # School name - from the bold link
                            school_elem = await item.query_selector('div.hoverable-link-text.t-bold span[aria-hidden="true"]')
                            if school_elem:
                                school_text = (await school_elem.text_content()).strip()
                                # Clean up the text (remove HTML comments markers)
                                edu_data["school"] = school_text.replace('<!---->', '').strip()

                            # Degree - from t-14 t-normal span (first one after school)
                            degree_spans = await item.query_selector_all('span.t-14.t-normal span[aria-hidden="true"]')
                            if len(degree_spans) > 0:
                                degree_text = (await degree_spans[0].text_content()).strip()
                                edu_data["degree"] = degree_text.replace('<!---->', '').strip()

                            # Date range - from t-black--light span
                            date_elem = await item.query_selector('span.t-14.t-normal.t-black--light span[aria-hidden="true"]')
                            if date_elem:
                                date_text = (await date_elem.text_content()).strip()
                                edu_data["dates"] = date_text.replace('<!---->', '').strip()

                            if edu_data.get("school"):
                                profile_data["education"].append(edu_data)

                        except Exception as e:
                            print(f"   ⚠️  Error parsing education item: {e}")
                            continue

                    print(f"✓ Education: {len(profile_data['education'])}")
            except Exception as e:
                print(f"   ⚠️  Error scraping education: {e}")

            # Skills (Compétences)
            try:
                skills_section = await page.query_selector('section:has(#skills)')
                if skills_section:
                    # Get all skill items
                    skill_items = await skills_section.query_selector_all('li.artdeco-list__item')

                    for item in skill_items[:50]:  # Limit to 50 skills
                        try:
                            # Skill name is in the bold link
                            skill_elem = await item.query_selector('div.hoverable-link-text.t-bold span[aria-hidden="true"]')
                            if skill_elem:
                                skill_text = (await skill_elem.text_content()).strip()
                                # Clean up the text
                                skill_name = skill_text.replace('<!---->', '').strip()
                                if skill_name and skill_name not in profile_data["skills"]:
                                    profile_data["skills"].append(skill_name)
                        except Exception as e:
                            continue

                    print(f"✓ Skills: {len(profile_data['skills'])}")
            except Exception as e:
                print(f"   ⚠️  Error scraping skills: {e}")

        except Exception as e:
            print(f"\n❌ Error scraping profile data: {e}")
            raise

        return profile_data


async def scrape_linkedin_profile_with_account(
    profile_url: str,
    email: str,
    password: str,
    headless: bool = True
) -> Dict:
    """
    Convenience function to scrape a LinkedIn profile

    Args:
        profile_url: LinkedIn profile URL
        email: Service account email
        password: Service account password
        headless: Run in headless mode

    Returns:
        dict: Profile data
    """
    scraper = LinkedInProfileScraper(headless=headless)
    return await scraper.scrape_profile(profile_url, email, password)
