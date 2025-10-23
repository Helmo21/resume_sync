# Apify LinkedIn Profile Scraper Integration

This document explains the Apify integration for scraping LinkedIn profiles to personalize resume summaries.

## Overview

The system now automatically scrapes LinkedIn profile data using the Apify API when users connect via OAuth. This data is used to personalize resume summaries and only scraped once per customer (unless the profile has been updated or 30+ days have passed).

## How It Works

### 1. OAuth Flow with Profile URL Capture

When a user connects their LinkedIn account:

1. **OAuth Callback** (`backend/app/api/auth.py:59-280`)
   - User authenticates via LinkedIn OAuth
   - System fetches basic profile data using LinkedIn API
   - System retrieves the user's vanity name (username) from LinkedIn API
   - Constructs profile URL: `https://www.linkedin.com/in/{vanityName}`
   - Stores profile URL in the `linkedin_profiles.profile_url` field

### 2. Automatic Apify Scraping

**For new users:**
- After OAuth completes and profile URL is captured
- System automatically triggers Apify scraping
- Complete profile data (experiences, education, skills) is fetched
- Data is stored in both structured fields and raw JSON (`apify_data` column)
- If Apify fails, falls back to basic OAuth data (non-blocking)

**For existing users:**
- System checks `last_synced_at` timestamp
- Only re-scrapes if profile is older than 30 days
- Otherwise, uses existing cached data
- Prevents unnecessary API calls and costs

### 3. Data Storage

Profile data is stored in the `linkedin_profiles` table:

```sql
-- New columns added
profile_url VARCHAR  -- LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
apify_data JSONB     -- Complete raw data from Apify scraper
```

Structured data is extracted and stored in:
- `headline` - Professional headline
- `summary` - About section
- `experiences` - Work history (JSONB array)
- `education` - Education history (JSONB array)
- `skills` - Skills list (JSONB array)
- `certifications` - Certifications (JSONB array)

## Setup Instructions

### 1. Get Apify API Token

1. Sign up at [Apify Console](https://console.apify.com/)
2. Navigate to [Account > Integrations](https://console.apify.com/account/integrations)
3. Copy your API token

### 2. Configure Environment

Add to your `.env` file:

```bash
APIFY_API_TOKEN=your_apify_api_token_here
```

### 3. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This will add the `profile_url` and `apify_data` columns to the `linkedin_profiles` table.

### 4. Restart Backend

```bash
docker-compose restart backend
```

## Files Created/Modified

### New Files

1. **`backend/app/services/apify_scraper.py`**
   - Main Apify integration service
   - `ApifyLinkedInScraper` class for scraping profiles
   - `scrape_profile()` - Triggers Apify actor and waits for results
   - `parse_profile_data()` - Converts Apify data to our format
   - `should_refresh_profile()` - Determines if profile needs updating

2. **`backend/alembic/versions/2025_10_16_0000-add_profile_url_and_apify_data.py`**
   - Database migration for new columns
   - Adds `profile_url` and `apify_data` to `linkedin_profiles` table

3. **`APIFY_INTEGRATION.md`** (this file)
   - Documentation for the integration

### Modified Files

1. **`backend/app/models/profile.py`**
   - Added `profile_url` field (String)
   - Added `apify_data` field (JSONB)

2. **`backend/app/api/auth.py`**
   - Updated OAuth callback to fetch vanity name from LinkedIn API
   - Constructs and stores profile URL
   - Automatically triggers Apify scraping for new users
   - Implements 30-day refresh logic for existing users
   - Added `datetime` import

3. **`backend/app/core/config.py`**
   - Added `APIFY_API_TOKEN` configuration field

4. **`backend/.env.example`**
   - Added Apify API token example with documentation

## Usage

### Automatic Scraping (Recommended)

Scraping happens automatically during OAuth:

1. User clicks "Connect with LinkedIn"
2. User authorizes the application
3. System captures profile URL and triggers Apify scraping
4. Profile data is stored and ready for resume personalization

No manual intervention needed!

### Manual Scraping (Optional)

You can also trigger manual scraping via API (to be implemented):

```python
# Example: Trigger manual profile refresh
from app.services.apify_scraper import ApifyLinkedInScraper

scraper = ApifyLinkedInScraper()
profile_url = "https://www.linkedin.com/in/username"
apify_data = scraper.scrape_profile(profile_url)
parsed_data = scraper.parse_profile_data(apify_data)
```

### Testing the Scraper

Test the scraper standalone:

```bash
cd backend
python -m app.services.apify_scraper https://www.linkedin.com/in/username
```

This will scrape the profile and output the results to the console and save to `linkedin_profile_scraped.json`.

## Apify Actor Details

**Actor ID:** `yZnhB5JewWf9xSmoM`
**Actor Name:** LinkedIn Profile Scraper
**Documentation:** https://console.apify.com/actors/yZnhB5JewWf9xSmoM

### Input Format

```json
{
  "startUrls": [
    {"url": "https://www.linkedin.com/in/username"}
  ]
}
```

### Output Format (Example)

```json
{
  "fullName": "John Doe",
  "headline": "Software Engineer at Tech Company",
  "summary": "Experienced software engineer...",
  "location": "San Francisco, CA",
  "positions": [
    {
      "title": "Senior Software Engineer",
      "companyName": "Tech Company",
      "location": "San Francisco, CA",
      "dateRange": "Jan 2020 - Present",
      "description": "Leading development of..."
    }
  ],
  "schools": [
    {
      "schoolName": "University Name",
      "degree": "Bachelor of Science",
      "fieldOfStudy": "Computer Science",
      "dateRange": "2015 - 2019"
    }
  ],
  "skills": ["JavaScript", "Python", "React", "Node.js"],
  "certifications": [
    {
      "name": "AWS Certified Developer",
      "authority": "Amazon Web Services",
      "dateRange": "Issued Jan 2021"
    }
  ]
}
```

## Refresh Logic

Profiles are refreshed based on these rules:

1. **New users:** Always scraped immediately after OAuth
2. **Existing users:**
   - If `last_synced_at` is NULL → Scrape
   - If `last_synced_at` > 30 days ago → Scrape
   - If `last_synced_at` < 30 days ago → Skip (use cached data)

This prevents unnecessary API calls and keeps costs low while ensuring data is reasonably fresh.

You can adjust the refresh interval by modifying the `refresh_interval_days` parameter in `auth.py:245`:

```python
should_refresh = scraper.should_refresh_profile(
    linkedin_profile.last_synced_at,
    refresh_interval_days=30  # Change this value
)
```

## Error Handling

The system gracefully handles Apify failures:

- If Apify scraping fails, the OAuth flow continues with basic LinkedIn API data
- User can still use the application with limited profile data
- Errors are logged but don't block authentication
- Failed scrapes can be retried later via manual sync endpoint

## Cost Considerations

**Apify Pricing:**
- LinkedIn Profile Scraper uses compute units based on usage
- Free tier: $5 credit/month (~50-100 profiles)
- Paid plans available for higher volume

**Cost Optimization:**
- Only scrape once per user (unless profile is updated)
- 30-day refresh interval prevents excessive scraping
- Graceful fallback to basic API data if Apify fails

## Using Profile Data for Personalization

The scraped profile data can be accessed in resume generation:

```python
from app.models.profile import LinkedInProfile

# Get user's profile
linkedin_profile = db.query(LinkedInProfile).filter(
    LinkedInProfile.user_id == user_id
).first()

# Access structured data
experiences = linkedin_profile.experiences
education = linkedin_profile.education
skills = linkedin_profile.skills
summary = linkedin_profile.summary

# Or access raw Apify data
apify_data = linkedin_profile.apify_data

# Use this data to personalize the resume summary
# Example: Include top skills, most recent role, etc.
```

## Troubleshooting

### Apify scraping fails with "API token not provided"

**Solution:** Make sure `APIFY_API_TOKEN` is set in your `.env` file and restart the backend.

### Profile URL is not being captured

**Solution:** The LinkedIn API might not return `vanityName` for some users. In this case, the profile URL will be `None` and Apify scraping will be skipped. The user will still have basic OAuth data.

### Scraping takes too long

**Solution:** The default timeout is 120 seconds. You can increase it by modifying the `timeout` parameter in `scrape_profile()` calls.

### Migration fails

**Solution:** Make sure you're running the migration from the correct directory:

```bash
cd backend
alembic upgrade head
```

If you get conflicts, check that the revision IDs match in the migration file.

## Next Steps

1. **Add manual sync endpoint:** Allow users to manually trigger profile refresh
2. **Add webhook support:** Listen for Apify actor completion instead of polling
3. **Background job processing:** Move Apify scraping to background jobs (Celery/Redis)
4. **Profile comparison:** Detect when profile has meaningfully changed before re-scraping
5. **Analytics dashboard:** Show scraping stats, costs, success rates

## Support

For issues or questions:
- Apify Documentation: https://docs.apify.com/
- Actor Issues: https://console.apify.com/actors/yZnhB5JewWf9xSmoM/issues
- ResumeSync Issues: Create an issue in the project repository
