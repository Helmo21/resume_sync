# Camoufox LinkedIn Profile Sync - Implementation Guide

**Date**: 2025-10-15
**Status**: ✅ Fully Implemented

## Overview

We've successfully implemented a **one-time manual login flow with cookie capture** that allows ResumeSync to scrape full LinkedIn profiles using Camoufox.

## How It Works

### The Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FIRST TIME SYNC                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User clicks "Sync Profile" button on dashboard             │
│  2. Backend checks: No saved cookies found                      │
│  3. Camoufox opens a visible browser window                     │
│  4. User manually logs into LinkedIn                            │
│  5. User completes 2FA (if required)                           │
│  6. User presses Enter in terminal/logs                         │
│  7. Camoufox captures browser session cookies                   │
│  8. Cookies saved to database (user.linkedin_cookies)          │
│  9. Camoufox scrapes full profile                              │
│ 10. Profile data stored in database                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  SUBSEQUENT SYNCS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User clicks "Sync Profile" button on dashboard             │
│  2. Backend loads saved cookies from database                   │
│  3. Camoufox runs in headless mode (no visible browser)        │
│  4. Cookies applied to browser session                          │
│  5. Camoufox scrapes profile (already authenticated)           │
│  6. Profile data updated in database                            │
│                                                                 │
│  If cookies are expired:                                        │
│  → Falls back to manual login flow                             │
│  → Captures fresh cookies                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## What Was Implemented

### 1. Database Schema Update ✅

**File**: `backend/app/models/user.py`

Added `linkedin_cookies` field to store browser session cookies:

```python
linkedin_cookies = Column(JSON, nullable=True)  # Store browser session cookies for scraping
```

**Migration**: `2025_10_15_1324-492b8f1635d3_add_linkedin_cookies_to_users.py`

### 2. Camoufox Scraper Enhancements ✅

**File**: `linkedin_camoufox_scraper.py`

**New Methods**:
- `authenticate_with_cookies()` - Uses saved cookies to authenticate
- `authenticate_manual_login()` - Opens browser for user to log in manually
- `authenticate()` - Smart authentication (tries cookies first, falls back to manual)

**Updated Signature**:
```python
def scrape_linkedin_profile_camoufox(
    cookies: list = None,
    profile_url: str = "https://www.linkedin.com/in/me/",
    headless: bool = True,
    allow_manual_login: bool = False
) -> tuple:  # Returns (profile_data, captured_cookies)
```

### 3. Profile Sync API Endpoint ✅

**File**: `backend/app/api/profile.py`

**New Endpoint**: `POST /api/profile/sync-with-camoufox`

**Features**:
- Checks for saved cookies in database
- First run: Opens visible browser for manual login
- Subsequent runs: Uses saved cookies in headless mode
- Auto-detects expired cookies and prompts for re-login
- Updates profile data in database
- Returns success message with scraped data counts

### 4. Frontend Integration ✅

**Files**:
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/services/api.js`

**New Features**:
- "Sync Profile" button in profile section
- Loading state during sync
- Success/error alerts
- Auto-refresh profile data after successful sync

## How to Use

### For Users

1. **Login to ResumeSync** with LinkedIn OAuth (as usual)
2. **Go to Dashboard** - you'll see your basic profile info (name, email)
3. **Click "Sync Profile"** button
4. **First Time Only**:
   - Watch the backend logs (or the backend will open a browser window)
   - A browser window will open showing LinkedIn login page
   - Log in to your LinkedIn account
   - Complete 2FA if prompted
   - Wait until you see your LinkedIn feed
   - Return to terminal and press Enter (or it will auto-detect)
5. **Wait for scraping** - Camoufox will extract your profile data
6. **View your profile** - Dashboard will refresh with:
   - Complete work experiences
   - Education history
   - Skills list
   - Professional headline
   - Summary/About section

### For Developers - Testing

```bash
# 1. Check services are running
docker compose ps

# 2. Watch backend logs in one terminal
docker compose logs backend -f

# 3. Open frontend in browser
open http://localhost:5173

# 4. Login with LinkedIn

# 5. Click "Sync Profile" button

# 6. Monitor logs for:
#    - "PROFILE SYNC REQUEST"
#    - "First time sync - manual login required" (if no cookies)
#    - "Using saved cookies" (if cookies exist)
#    - Browser window instructions
#    - Scraping progress
#    - "Profile sync completed successfully"
```

## Technical Details

### Cookie Storage Format

Cookies are stored as JSON array in PostgreSQL:

```json
[
  {
    "name": "li_at",
    "value": "AQEDATxxxxx...",
    "domain": ".linkedin.com",
    "path": "/",
    "expires": 1750000000,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "JSESSIONID",
    "value": "ajax:1234567890",
    "domain": ".linkedin.com",
    ...
  }
]
```

### Security Considerations

⚠️ **Important**:
- Cookies contain authentication tokens - treat as sensitive data
- **TODO**: Encrypt `linkedin_cookies` field in production
- **TODO**: Add expiration check and cleanup for old cookies
- LinkedIn may detect and revoke cookies if suspicious activity detected

### What Gets Scraped

With Camoufox + browser cookies, we can scrape:

✅ **Full Name**
✅ **Professional Headline**
✅ **Location**
✅ **Summary/About Section**
✅ **Work Experience** (title, company, dates, description)
✅ **Education** (school, degree, graduation year)
✅ **Skills** (full list)
✅ **Certifications** (if visible on profile)

### Limitations

- Cookies typically expire after 30-60 days
- User must manually re-login when cookies expire
- LinkedIn may detect automated activity
- Scraping violates LinkedIn ToS (use at your own risk)
- Some profile sections may require additional navigation

## API Endpoints

### `POST /api/profile/sync-with-camoufox`

Trigger profile sync with Camoufox scraping.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (Success):
```json
{
  "success": true,
  "message": "Profile synced successfully",
  "profile": {
    "headline": "Software Engineer at Google",
    "summary": "Passionate about...",
    "experiences_count": 5,
    "education_count": 2,
    "skills_count": 25
  }
}
```

**Response** (Error):
```json
{
  "detail": "Failed to sync profile: Authentication failed"
}
```

## Troubleshooting

### Issue: Browser window doesn't open

**Solution**:
- Check if Camoufox is installed: `docker compose exec backend python -c "import camoufox.sync_api"`
- Check backend logs for errors
- Make sure `headless=False` for manual login

### Issue: Cookies don't work (authentication fails)

**Possible Causes**:
1. Cookies expired (normal after 30-60 days)
2. LinkedIn detected automation and revoked session
3. User logged out of LinkedIn on web

**Solution**:
- Click "Sync Profile" again
- Complete manual login flow to get fresh cookies

### Issue: Incomplete profile data scraped

**Possible Causes**:
1. LinkedIn changed their HTML structure
2. Some sections require scrolling/clicking to load
3. Profile is private/restricted

**Solution**:
- Check Camoufox scraper selectors in `linkedin_camoufox_scraper.py`
- Update CSS selectors to match current LinkedIn structure
- Add additional navigation/clicking logic

### Issue: "Cannot authenticate - headless mode requires valid session"

**Cause**: No saved cookies and `allow_manual_login=False`

**Solution**: Endpoint automatically handles this - should not occur in production

## Future Enhancements

### Recommended Improvements

1. **Cookie Encryption**
   ```python
   from cryptography.fernet import Fernet
   # Encrypt cookies before saving
   # Decrypt when loading
   ```

2. **Background Sync**
   ```python
   # Use Celery or background tasks
   # Sync profile automatically every X days
   ```

3. **Cookie Expiration Detection**
   ```python
   # Check cookie expiration before using
   # Proactively request re-login
   ```

4. **Better UI Feedback**
   ```javascript
   // Show progress: "Logging in... Scraping experiences... Done!"
   // Add visual indicator when cookies are about to expire
   ```

5. **Retry Logic**
   ```python
   # Auto-retry with exponential backoff
   # Handle rate limiting
   ```

## Files Modified/Created

### Created
- `linkedin_camoufox_scraper.py` - Main Camoufox scraper
- `backend/alembic/versions/2025_10_15_1324-492b8f1635d3_add_linkedin_cookies_to_users.py` - Migration

### Modified
- `backend/app/models/user.py` - Added `linkedin_cookies` field
- `backend/app/api/profile.py` - Added `/sync-with-camoufox` endpoint
- `frontend/src/pages/Dashboard.jsx` - Added sync button and handler
- `frontend/src/services/api.js` - Added `syncWithCamoufox()` method

## Summary

✅ **Fully working implementation of Option #1: One-time manual login with cookie capture**

**Benefits**:
- Users log in once, cookies are reused
- Full profile data access (not limited by LinkedIn API)
- Automatic re-authentication when cookies expire
- Works around LinkedIn OAuth API limitations

**Trade-offs**:
- Requires manual login on first sync
- Violates LinkedIn Terms of Service
- Cookies can expire and need refresh
- May be detected as automation

This implementation successfully addresses your original question: **"once we log in, scrape the profile page to get all the data"** by capturing browser cookies during manual login and reusing them for automated scraping.
