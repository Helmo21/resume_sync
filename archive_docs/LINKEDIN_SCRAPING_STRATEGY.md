# LinkedIn Profile Scraping Strategy

**Date**: 2025-10-15
**Issue**: Need to scrape full LinkedIn profile data after OAuth login
**Your Insight**: "Once we log in, scrape the profile page to get all the data, why we stop using Camoufox?"

## The Core Problem

### What You're Right About
Yes! Once a user authenticates via LinkedIn OAuth, we **should** be able to access their profile data. The question is: **how?**

### The Challenge
LinkedIn OAuth provides an **access token**, but this token alone doesn't:
1. Give us browser session cookies (can't use Selenium to scrape as logged-in user)
2. Grant API access to full profile without proper scopes

## Three Approaches

### Approach 1: OAuth Scopes (API Access) ⭐ BEST
**How it works**: Request proper OAuth scopes to access LinkedIn Profile API

**Updated Implementation**:
```python
# OLD (only basic info)
scope = "openid profile email"

# NEW (request profile access)
scope = "openid profile email w_member_social"
```

**LinkedIn Scopes Available**:
- `openid` - Basic OpenID Connect
- `profile` - Basic profile info (name)
- `email` - Email address
- `w_member_social` - Read/write member's profile (THIS IS KEY!)
- `r_basicprofile` - Basic profile (deprecated)
- `r_liteprofile` - Light profile (deprecated)

**With proper scope**, the access token can call:
- `/v2/me` - Detailed profile
- `/v2/people` - Person data
- Various profile endpoints

**Status**: ✅ **IMPLEMENTED** - Updated auth.py to request `w_member_social`

**Next Step**:
1. User logs out
2. User logs in again (will see new permission request)
3. LinkedIn will ask: "Allow ResumeSync to access your profile?"
4. User accepts
5. Backend gets access token with proper scope
6. Can now call LinkedIn API endpoints for full profile

### Approach 2: Selenium with Manual Login
**How it works**: Use Selenium but require manual login first time

**Flow**:
1. Open Selenium browser (headless or visible)
2. Navigate to LinkedIn login
3. User manually logs in (or bot autofills saved credentials)
4. Once logged in, browser has session cookies
5. Navigate to /in/me/ (user's profile)
6. Scrape all profile data
7. Store cookies for future use

**Pros**:
- Can access ALL profile data (not limited by API)
- Works with any LinkedIn account
- No API partnership needed

**Cons**:
- Requires manual login step
- Violates LinkedIn ToS (automated scraping)
- LinkedIn actively detects and blocks bots
- Fragile (breaks when LinkedIn changes HTML)

**Status**: ⚠️ Selenium scraper created but needs manual auth

### Approach 3: RapidAPI LinkedIn Profile API
**How it works**: Use third-party LinkedIn scraping API

**Services**:
- RapidAPI LinkedIn Profile Scraper (~$0.01 per profile)
- Proxycurl (~$0.01 per profile)
- Others

**Pros**:
- Instant access
- No LinkedIn partnership needed
- Maintained by third party

**Cons**:
- Costs money per scrape
- Still violates LinkedIn ToS (they do the scraping)
- May get rate limited/blocked

**Status**: Not implemented (not recommended)

## Recommended Solution: Update OAuth Scopes

### Step 1: Verify App Has Correct Permissions

Go to LinkedIn Developer Portal:
1. Visit https://www.linkedin.com/developers/apps
2. Open your app ("786pnicdqzc6yz")
3. Go to "Products" tab
4. Check if "Profile API" or "Sign In with LinkedIn using OpenID Connect" is enabled
5. Request additional products if needed:
   - **Marketing Developer Platform** (full profile access)
   - **Compliance API** (if available)

### Step 2: Update OAuth Scope (DONE)

Backend now requests: `openid profile email w_member_social`

### Step 3: Update LinkedIn API Scraper

The `linkedin_api_scraper.py` needs to use the new endpoints available with `w_member_social` scope:

```python
def get_detailed_profile_with_scope(access_token: str) -> Dict:
    """
    Get detailed profile using w_member_social scope.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    # Try various endpoints that may be available
    endpoints_to_try = [
        "/v2/me",
        "/v2/people/(id:{person_id})",
        "/v2/positions",
        "/v2/educations",
        "/v2/skills"
    ]

    profile_data = {}

    for endpoint in endpoints_to_try:
        try:
            response = requests.get(
                f"https://api.linkedin.com{endpoint}",
                headers=headers
            )
            if response.status_code == 200:
                profile_data[endpoint] = response.json()
        except:
            continue

    return profile_data
```

### Step 4: Test

```bash
# 1. Logout of ResumeSync
# 2. Login again with LinkedIn
# 3. LinkedIn will ask for new permission: "Access your profile data"
# 4. Accept
# 5. Backend logs should show profile scraping success
docker compose logs backend -f
```

## Why OAuth Token ≠ Browser Session

This is the key insight:

**OAuth Access Token**:
- Used for API calls
- Sent in `Authorization: Bearer TOKEN` header
- Server-to-server communication

**Browser Session Cookies**:
- Used for web browsing
- Sent automatically with browser requests
- Set by login form submission

**LinkedIn's OAuth doesn't give you session cookies** - it gives you an API token. To scrape with Selenium, you'd need the actual session cookies (li_at, JSESSIONID, etc.), which OAuth doesn't provide.

## Current Status

### What's Implemented
✅ OAuth scope updated to `w_member_social`
✅ API scraper with multiple endpoints
✅ Selenium scraper (structure, needs auth solution)
✅ Fallback handling in auth callback

### What Needs Testing
⚠️ Logout and login again to get new scope
⚠️ Check what LinkedIn API endpoints are now accessible
⚠️ Verify profile data is actually scraped

### If w_member_social Still Doesn't Work

**Option A**: Apply for Marketing Developer Platform
- Go to https://www.linkedin.com/developers/
- Apply for partner access
- Wait for approval (weeks to months)

**Option B**: Build manual profile form
- User manually inputs their work experience
- User manually inputs education
- User manually inputs skills
- Store in database

**Option C**: AI-powered import
- User copies their entire LinkedIn profile text
- AI extracts structured data
- User reviews and saves

## Testing the Current Implementation

### Test 1: Check Available Scopes
```bash
# After logging in, check what scopes were granted
docker compose exec db psql -U resumesync -d resumesync \
  -c "SELECT linkedin_id, linkedin_access_token FROM users LIMIT 1;"

# Test the token
TOKEN="<token_from_database>"
curl -H "Authorization: Bearer $TOKEN" \
  https://api.linkedin.com/v2/me
```

### Test 2: Try Scraping
```bash
# Run the API scraper
docker compose exec backend python /app/legacy/linkedin_api_scraper.py "<your_token>"
```

### Test 3: Check Backend Logs
```bash
# Login again and watch logs
docker compose logs backend -f

# Look for:
# ✓ LinkedIn profile scraped successfully
# or
# ⚠️ Could not scrape full profile: 403 Forbidden
```

## Camoufox Alternative

You mentioned Camoufox - it's a Firefox fork for scraping. It could work if:

1. We can somehow transfer the OAuth token to browser cookies
2. Or we implement a "Connect LinkedIn" flow that opens a real browser
3. User logs in manually in that browser
4. We capture and save the session cookies
5. Use those cookies with Camoufox for future scrapes

**Implementation**:
```python
# After OAuth, open a browser for one-time manual login
def get_linkedin_cookies():
    driver = Firefox()  # or Camoufox
    driver.get("https://www.linkedin.com/login")

    # Wait for user to login manually
    input("Press Enter after you've logged in to LinkedIn...")

    # Get cookies
    cookies = driver.get_cookies()

    # Save cookies to database
    save_cookies(user_id, cookies)

    driver.quit()

# Later, use saved cookies for scraping
def scrape_with_saved_cookies(user_id):
    cookies = load_cookies(user_id)
    driver = Firefox()
    driver.get("https://www.linkedin.com")

    for cookie in cookies:
        driver.add_cookie(cookie)

    driver.get("https://www.linkedin.com/in/me/")
    # Now scrape
```

## Conclusion

**Your insight is correct**: We should scrape the profile after authentication.

**The solution**: Request proper OAuth scopes (`w_member_social`) to access LinkedIn Profile API endpoints.

**Status**: Implementation done, needs testing with re-login to get new permissions.

**Fallback**: If API access still restricted, build manual profile form as interim solution.

---

**Next Actions**:
1. Restart backend: `docker compose restart backend`
2. Logout and login again to get new scope
3. Check logs to see if profile scraping works
4. If still fails → build manual profile form

