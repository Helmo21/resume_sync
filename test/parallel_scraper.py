"""
Parallel LinkedIn Job Scraper
Launches multiple scraping sessions in parallel to maximize performance
"""

import asyncio
import json
from datetime import datetime
from linkedin_job_scraper import LinkedInJobScraper
from typing import List, Dict
import random


class ParallelLinkedInScraper:
    def __init__(self, job_title: str, location: str, num_sessions: int = None, jobs_per_session: int = None):
        self.job_title = job_title
        self.location = location
        self.num_sessions = num_sessions
        self.jobs_per_session = jobs_per_session
        self.all_jobs = []
        self.total_jobs_available = None

    async def detect_total_jobs(self) -> int:
        """Detect total number of jobs available from LinkedIn search"""
        from camoufox.async_api import AsyncCamoufox

        print(f"\n{'='*60}")
        print("DETECTING TOTAL JOBS AVAILABLE...")
        print(f"{'='*60}\n")

        try:
            async with AsyncCamoufox(headless=True, humanize=True, os='windows') as browser:
                page = await browser.new_page()

                # Build search URL
                job_title_encoded = self.job_title.replace(" ", "%20")
                location_encoded = self.location.replace(" ", "%20")
                url = f"https://www.linkedin.com/jobs/search/?keywords={job_title_encoded}&location={location_encoded}&f_AL=true"

                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # Try to find results count
                try:
                    # LinkedIn shows results like "1,234 results"
                    results_text = await page.query_selector('text=/\\d+.*results/')
                    if results_text:
                        text = await results_text.inner_text()
                        # Extract number from text like "1,234 results"
                        import re
                        match = re.search(r'([\d,]+)', text)
                        if match:
                            total = int(match.group(1).replace(',', ''))
                            print(f"✓ Found {total} total jobs available\n")
                            return total
                except:
                    pass

                # Fallback: count job cards on first page and estimate
                job_cards = await page.query_selector_all('li.scaffold-layout__list-item')
                if job_cards:
                    # LinkedIn typically shows 25 jobs per page, max ~1000 jobs (40 pages)
                    estimated = len(job_cards) * 40  # Conservative estimate
                    print(f"⚠ Could not find exact count. Estimating {estimated} jobs based on {len(job_cards)} per page\n")
                    return estimated

                print(f"⚠ Could not detect total. Using default estimate of 500 jobs\n")
                return 500

        except Exception as e:
            print(f"✗ Error detecting total jobs: {str(e)}")
            print(f"⚠ Using default estimate of 500 jobs\n")
            return 500

    def auto_configure(self, total_jobs: int):
        """Automatically configure optimal number of sessions and jobs per session"""
        print(f"\n{'='*60}")
        print("AUTO-CONFIGURING SCRAPING STRATEGY...")
        print(f"{'='*60}\n")

        # Strategy based on total jobs available
        if total_jobs <= 50:
            # Small search: 1 session
            self.num_sessions = 1
            self.jobs_per_session = total_jobs + 10  # Add buffer
        elif total_jobs <= 200:
            # Medium search: 2-3 sessions
            self.num_sessions = 2
            self.jobs_per_session = (total_jobs // 2) + 20
        elif total_jobs <= 500:
            # Large search: 3-5 sessions
            self.num_sessions = 3
            self.jobs_per_session = (total_jobs // 3) + 30
        else:
            # Very large search: 5-8 sessions
            # Cap at reasonable numbers to avoid overwhelming LinkedIn
            self.num_sessions = min(5, (total_jobs // 100) + 1)
            self.jobs_per_session = (total_jobs // self.num_sessions) + 50

        print(f"Total Jobs Available: {total_jobs}")
        print(f"Optimal Configuration:")
        print(f"  - Parallel Sessions: {self.num_sessions}")
        print(f"  - Jobs per Session: {self.jobs_per_session}")
        print(f"  - Total Target: {self.num_sessions * self.jobs_per_session} jobs")
        print(f"{'='*60}\n")

    async def scrape_session(self, session_id: int, start_delay: float = 0) -> List[Dict]:
        """Run a single scraping session"""
        # Add random start delay to avoid simultaneous requests
        if start_delay > 0:
            await asyncio.sleep(start_delay)

        print(f"\n{'='*60}")
        print(f"SESSION {session_id} STARTING")
        print(f"Target: {self.jobs_per_session} jobs")
        print(f"{'='*60}\n")

        try:
            scraper = LinkedInJobScraper(
                job_title=self.job_title,
                location=self.location,
                headless=True,
                max_jobs=self.jobs_per_session
            )

            jobs = await scraper.scrape_jobs()

            print(f"\n{'='*60}")
            print(f"SESSION {session_id} COMPLETED: {len(jobs)} jobs scraped")
            print(f"{'='*60}\n")

            return jobs
        except Exception as e:
            print(f"\n✗ SESSION {session_id} FAILED: {str(e)}\n")
            return []

    def deduplicate_jobs(self, jobs_list: List[List[Dict]]) -> List[Dict]:
        """Remove duplicate jobs based on job URL or title+company"""
        seen = set()
        unique_jobs = []

        for jobs in jobs_list:
            for job in jobs:
                # Create unique identifier
                job_id = job.get('job_url') or f"{job.get('title')}_{job.get('company')}_{job.get('location')}"

                if job_id not in seen:
                    seen.add(job_id)
                    unique_jobs.append(job)

        print(f"\n{'='*60}")
        print(f"DEDUPLICATION COMPLETE")
        print(f"Total scraped: {sum(len(j) for j in jobs_list)}")
        print(f"Unique jobs: {len(unique_jobs)}")
        print(f"Duplicates removed: {sum(len(j) for j in jobs_list) - len(unique_jobs)}")
        print(f"{'='*60}\n")

        return unique_jobs

    async def scrape_parallel(self) -> List[Dict]:
        """Run multiple scraping sessions in parallel"""
        print(f"\n{'#'*60}")
        print(f"PARALLEL LINKEDIN SCRAPER")
        print(f"{'#'*60}")
        print(f"Job Title: {self.job_title}")
        print(f"Location: {self.location}")
        print(f"{'#'*60}\n")

        # Auto-detect and configure if not manually set
        if self.num_sessions is None or self.jobs_per_session is None:
            total_jobs = await self.detect_total_jobs()
            self.total_jobs_available = total_jobs
            self.auto_configure(total_jobs)
        else:
            print(f"Using manual configuration:")
            print(f"  - Parallel Sessions: {self.num_sessions}")
            print(f"  - Jobs per Session: {self.jobs_per_session}")
            print(f"  - Total Target: {self.num_sessions * self.jobs_per_session} jobs\n")

        # Create tasks for parallel execution with staggered start times
        tasks = []
        for i in range(self.num_sessions):
            # Stagger starts by 5-15 seconds to avoid detection
            start_delay = random.uniform(5, 15) * i
            task = self.scrape_session(i + 1, start_delay)
            tasks.append(task)

        # Run all sessions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and get valid results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"✗ Session {i+1} raised exception: {result}")
            elif result:
                valid_results.append(result)

        # Deduplicate and combine results
        if valid_results:
            unique_jobs = self.deduplicate_jobs(valid_results)
            self.all_jobs = unique_jobs
            return unique_jobs

        return []

    def save_results(self, filename: str = None) -> str:
        """Save all scraped jobs to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_jobs_parallel_{self.job_title.replace(' ', '_')}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_jobs, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"✓ RESULTS SAVED")
        print(f"File: {filename}")
        print(f"Total Jobs: {len(self.all_jobs)}")
        print(f"{'='*60}\n")

        return filename


async def main():
    """Main entry point for parallel scraper"""
    print("\n" + "="*60)
    print("PARALLEL LINKEDIN JOB SCRAPER - AUTO MODE")
    print("="*60 + "\n")

    # Get user input
    job_title = input("Enter job title/position: ").strip()
    location = input("Enter location: ").strip()

    if not job_title or not location:
        print("Error: Both job title and location are required!")
        return

    # Configuration - AUTO by default, optional manual override
    print("\n" + "-"*60)
    print("CONFIGURATION MODE")
    print("-"*60)
    print("AUTO mode: Automatically detect total jobs and optimize sessions")
    print("MANUAL mode: You specify sessions and jobs per session")
    print("-"*60)

    mode = input("Use AUTO mode? (y/n) [default: y]: ").strip().lower()

    if mode == 'n':
        # Manual configuration
        num_sessions_input = input("Number of parallel sessions? [default: 3]: ").strip()
        num_sessions = int(num_sessions_input) if num_sessions_input.isdigit() else 3

        jobs_per_session_input = input("Jobs per session? [default: 100]: ").strip()
        jobs_per_session = int(jobs_per_session_input) if jobs_per_session_input.isdigit() else 100

        scraper = ParallelLinkedInScraper(
            job_title=job_title,
            location=location,
            num_sessions=num_sessions,
            jobs_per_session=jobs_per_session
        )
    else:
        # AUTO mode - scraper will auto-detect and configure
        print("\n✓ AUTO mode enabled - will detect total jobs and optimize configuration\n")
        scraper = ParallelLinkedInScraper(
            job_title=job_title,
            location=location,
            num_sessions=None,  # Will be auto-configured
            jobs_per_session=None  # Will be auto-configured
        )

    # Start parallel scraping
    start_time = datetime.now()
    jobs = await scraper.scrape_parallel()
    end_time = datetime.now()

    # Save results
    if jobs:
        filename = scraper.save_results()

        # Print summary
        duration = (end_time - start_time).total_seconds()
        print(f"\n{'#'*60}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'#'*60}")
        print(f"Total Jobs Scraped: {len(jobs)}")
        print(f"Jobs with Descriptions: {sum(1 for j in jobs if j.get('description'))}")
        print(f"Total Time: {duration:.1f} seconds")
        print(f"Average: {duration/len(jobs):.1f} seconds per job")
        print(f"Output File: {filename}")
        print(f"{'#'*60}\n")
    else:
        print("\n✗ No jobs were scraped.\n")


if __name__ == "__main__":
    asyncio.run(main())
