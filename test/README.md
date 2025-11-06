# LinkedIn Job Scraper with Camoufox

A Python script that scrapes job descriptions from LinkedIn using Camoufox, an anti-detection browser built for web scraping.

## Features

- Automatic LinkedIn authentication using credentials from .env file
- Scrapes job title, company, location, description, URL, and posted date
- Automatically crawls through all pages of search results
- Outputs data in JSON format
- Uses Camoufox for enhanced privacy and anti-detection
- Rate limiting to avoid being blocked
- Handles login verification and 2FA prompts

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Camoufox will automatically download the browser on first run (no additional installation needed)

**Note:** Camoufox is an anti-detection browser built on Firefox that provides:
- Advanced fingerprint spoofing
- Human-like cursor movements
- Automatic device and OS rotation
- Enhanced privacy features to avoid bot detection

## Configuration

### Setting up LinkedIn Credentials

1. Create or edit the `.env` file in the project root directory:

```bash
# .env file
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password_here
```

2. Replace the placeholder values with your actual LinkedIn credentials:
   - `LINKEDIN_EMAIL`: Your LinkedIn email address
   - `LINKEDIN_PASSWORD`: Your LinkedIn password

**Important Security Notes:**
- Never commit the `.env` file to version control (it's already in `.gitignore`)
- Keep your credentials secure and private
- The script will work without credentials but will have limited access to job listings

### Creating a .gitignore file

To prevent accidentally committing your credentials, create a `.gitignore` file:

```bash
echo ".env" >> .gitignore
```

## Usage

### Basic Usage

Run the script and follow the prompts:

```bash
python linkedin_job_scraper.py
```

You'll be asked to input:
- Job title/position (e.g., "Software Engineer", "Data Scientist")
- Location (e.g., "San Francisco, CA", "Remote", "United States")

### Programmatic Usage

You can also use the scraper in your own Python code:

```python
import asyncio
from linkedin_job_scraper import LinkedInJobScraper

async def scrape_jobs():
    scraper = LinkedInJobScraper(
        job_title="Python Developer",
        location="New York, NY"
    )

    jobs = await scraper.scrape_jobs()
    scraper.save_to_json("my_jobs.json")

    return jobs

# Run the scraper
jobs = asyncio.run(scrape_jobs())
print(f"Scraped {len(jobs)} jobs")
```

## Output Format

The script generates a JSON file with the following structure:

```json
[
  {
    "title": "Senior Software Engineer",
    "company": "Tech Company Inc.",
    "location": "San Francisco, CA",
    "description": "Full job description text...",
    "job_url": "https://www.linkedin.com/jobs/view/123456789",
    "posted_date": "2024-01-15",
    "scraped_at": "2024-01-20T10:30:00"
  }
]
```

## Configuration

You can modify the following parameters in the script:

- `max_pages`: Maximum number of pages to scrape (default: 40)
- `headless`: Run browser in headless mode (default: False)
- Rate limiting delays in `asyncio.sleep()` calls

## Important Notes

### LinkedIn's Terms of Service

Be aware that web scraping may violate LinkedIn's Terms of Service. This script is for educational purposes only. Use responsibly and consider:

- LinkedIn's robots.txt and terms of service
- Rate limiting to avoid overloading servers
- Using official LinkedIn APIs when possible

### Anti-Bot Detection

LinkedIn has anti-bot measures. This script uses Camoufox to minimize detection:

- **Fingerprint Spoofing**: Automatically rotates device fingerprints
- **Human-like Behavior**: Simulates natural cursor movements with `humanize=True`
- **OS Simulation**: Emulates Windows environment to match real traffic
- **Rate Limiting**: Implements delays between requests
- **Runs in visible mode**: Allows manual intervention if needed

If you get blocked:
- Increase delay times between requests
- Use a VPN or different IP address
- Consider using LinkedIn's official API

### Authentication

The script now supports automatic login using credentials from the `.env` file:

- If credentials are provided, the script will automatically log in to LinkedIn
- If credentials are missing or invalid, the script will continue without login (limited access)
- The script handles 2FA and verification prompts by pausing and allowing manual completion

**Two-Factor Authentication (2FA):**
If your LinkedIn account has 2FA enabled:
1. The script will pause and display a message
2. Complete the 2FA verification manually in the browser window
3. The script will automatically continue after 30 seconds

## Troubleshooting

### Authentication Issues

**"Login failed" or "Could not find login button"**
- Verify your credentials in the `.env` file are correct
- Check if LinkedIn has updated their login page selectors
- Ensure you're not being rate-limited by LinkedIn

**Two-Factor Authentication not working**
- Make sure you complete the 2FA prompt within 30 seconds
- If you need more time, increase the sleep duration in `linkedin_job_scraper.py:183`

**"Please update your LinkedIn credentials"**
- You haven't replaced the placeholder values in `.env`
- Edit the `.env` file with your actual credentials

### "No job listings found"

- LinkedIn may be blocking automated access
- Try increasing delay times
- Check if the search URL is valid
- Ensure you're not rate-limited

### "Import error" or "Module not found"

Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

Camoufox will automatically download its browser on first run.

### Slow Performance

- Reduce the number of pages to scrape
- Increase concurrency (advanced)
- Use headless mode

## License

This project is for educational purposes only. Use at your own risk and in compliance with LinkedIn's Terms of Service.
