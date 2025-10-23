# LinkedIn Profile Scraping Solution

**Date**: 2025-10-15
**Issue**: LinkedIn OAuth only returns basic info (name, email), not full profile data
**Solution**: Created API scraper that attempts to fetch more data with access token

## The Problem

### What LinkedIn OAuth Gives Us

When a user authenticates with LinkedIn OAuth using the `openid profile email` scopes, LinkedIn only provides:

```json
{
  "sub": "linkedin_user_id",
  "name": "John Doe",
  "email": "john@example.com",
  "picture": "https://...",
  "locale": "en-US"
}
```

**Missing**: Experiences, education, skills, summary, headline

### What We Actually Need

For resume generation, we need:
- Professional headline
- Career summary
- Work experiences (title, company, dates, descriptions)
- Education (degrees, schools, graduation years)
- Skills list
- Certifications

## LinkedIn API Restrictions

### The Challenge

LinkedIn has **heavily restricted** access to profile data:

1. **Basic Profile** (`r_liteprofile`): ❌ Deprecated
2. **Full Profile** (`r_fullprofile`): ❌ Requires LinkedIn partnership
3. **Positions API** (`/v2/positions`): ❌ Requires special permissions
4. **Skills API**: ❌ Requires special permissions

### What's Actually Available

With standard OAuth (`openid profile email`):
- ✅ Basic info (name, email, picture)
- ✅ LinkedIn ID
- ❌ Headline
- ❌ Summary
- ❌ Experiences
- ❌ Education
- ❌ Skills

**Result**: We cannot fetch full profile data via LinkedIn API without a partnership agreement.

## Solutions Implemented

### Solution 1: LinkedIn API Scraper (Partial)

**File**: `linkedin_api_scraper.py`

This script attempts to use the LinkedIn API with the OAuth access token:

```python
class LinkedInProfileAPI:
    def get_basic_profile(self):
        """Get name, email (works)"""

    def get_profile_details(self):
        """Try to get headline (requires permissions)"""

    def get_positions(self):
        """Try to get experiences (requires permissions)"""
```

**Status**:
- ✅ Gets basic info (name, email)
- ⚠️  Headline/experiences require restricted permissions
- ❌ Most endpoints return 403 Forbidden

### Solution 2: Web Scraping with Selenium (Future)

Using the OAuth session to authenticate a headless browser and scrape the profile:

**Pros**:
- Can access full profile data
- Works with user's authenticated session

**Cons**:
- LinkedIn actively blocks automated scraping
- Violates LinkedIn Terms of Service
- Requires headless browser infrastructure
- Fragile (breaks when LinkedIn changes their HTML)

**Status**: Not recommended

### Solution 3: Manual Profile Completion (Interim)

Allow users to manually fill in their profile data in the app:

1. User logs in with LinkedIn (gets basic info)
2. User manually adds experiences, education, skills in a form
3. Data is stored in database
4. Used for resume generation

**Pros**:
- Guaranteed to work
- Users can add/edit data anytime
- No API restrictions
- Compliant with LinkedIn ToS

**Cons**:
- Requires manual input from users
- Extra friction in onboarding

**Status**: Best current solution

## Current Implementation

### What Happens Now

When a user logs in with LinkedIn:

1. **OAuth Flow** (`/api/auth/linkedin/callback`)
   ```python
   # Get access token
   access_token = exchange_code_for_token(code)

   # Get basic profile
   basic_profile = get_userinfo(access_token)

   # Try to scrape full profile
   try:
       full_profile = linkedin_api_scraper.scrape_linkedin_with_token(access_token)
       # Will get basic info only due to API restrictions
   except:
       # Fallback: Empty profile
       full_profile = {
           "headline": "",
           "summary": "",
           "experiences": [],
           "education": [],
           "skills": []
       }
   ```

2. **Store in Database**
   ```python
   linkedin_profile = LinkedInProfile(
       user_id=user.id,
       headline=full_profile.get("headline", basic_profile.get("name")),
       summary=full_profile.get("summary", ""),
       experiences=full_profile.get("experiences", []),
       education=full_profile.get("education", []),
       skills=full_profile.get("skills", [])
   )
   ```

3. **Result**
   - Basic info (name, email) is populated ✅
   - Other fields are empty ❌
   - User must manually complete profile

## Recommended Next Steps

### Option A: Manual Profile Form (Recommended)

Create a profile completion form where users can add their information:

**Pages to Add**:
1. `/profile/edit` - Form to add/edit experiences, education, skills
2. Show "Complete Your Profile" banner if profile is incomplete
3. Guide users through adding at least 2 experiences, 1 education

**Benefits**:
- Guaranteed to work
- Users have full control
- Can update anytime
- No API restrictions

### Option B: LinkedIn Profile Import Feature

Add a "Smart Import" feature:

1. User copies their LinkedIn profile URL
2. They paste entire profile text from LinkedIn
3. AI (OpenRouter) parses the text and extracts structured data
4. User reviews and confirms

**Benefits**:
- Faster than manual form
- Still user-initiated
- Uses AI we already have
- Compliant with ToS

### Option C: Request LinkedIn Partnership (Long-term)

Apply for LinkedIn Marketing Developer Platform access:

1. Go to https://www.linkedin.com/developers/
2. Apply for Marketing Developer Platform partnership
3. Wait for approval (can take months)
4. Get access to full Profile API

**Benefits**:
- Official API access
- Full profile data
- Reliable

**Cons**:
- Requires business verification
- Takes months to approve
- Not guaranteed to be accepted
- May have usage limits/costs

## Implementation Plan

### Phase 1: Manual Profile Form (This Week)

1. Create `/profile/edit` page with form
2. Add sections for:
   - Headline
   - Summary
   - Experiences (add/remove)
   - Education (add/remove)
   - Skills (add/remove)
3. Update dashboard to show "Complete Profile" if empty
4. Add profile completion progress indicator

### Phase 2: AI-Powered Import (Next Week)

1. Add "Import from Text" feature
2. User pastes their LinkedIn profile text
3. AI extracts structured data
4. User reviews and saves

### Phase 3: LinkedIn Partnership (Future)

1. Apply for partner access
2. Wait for approval
3. Implement proper API integration

## Testing the Current Implementation

### Test the API Scraper

```bash
# Get an access token from database
docker compose exec db psql -U resumesync -d resumesync \
  -c "SELECT linkedin_access_token FROM users LIMIT 1;"

# Test the scraper (will show API limitations)
docker compose exec backend python /app/legacy/linkedin_api_scraper.py "YOUR_TOKEN"
```

### Expected Output

```
⏳ Fetching LinkedIn profile via API...
✓ Profile data fetched (limited by API permissions)
⚠️ Could not fetch detailed profile: 403 Forbidden
⚠️ Could not fetch positions: 403 Forbidden

{
  "full_name": "John Doe",
  "email": "john@example.com",
  "headline": "John Doe",
  "summary": "",
  "experiences": [],
  "education": [],
  "skills": []
}
```

## Current Dashboard Behavior

After login:
1. Dashboard loads
2. Profile section shows basic info (name, email)
3. Experiences, education, skills are empty (or show test data if manually inserted)
4. User sees their basic LinkedIn info only

**To Fix**: Implement manual profile form (Phase 1)

## Conclusion

**Current State**:
- ✅ LinkedIn OAuth authentication works
- ✅ Basic profile info (name, email) is captured
- ❌ Full profile data (experiences, education, skills) is not accessible via API
- ✅ API scraper created but limited by LinkedIn restrictions
- ✅ Backend updated to attempt scraping on login

**Immediate Solution**:
- **Build manual profile form** so users can add their information
- Show "Complete Your Profile" prompt after login
- Guide users through adding experiences, education, and skills

**Long-term Solution**:
- Apply for LinkedIn partner access
- Meanwhile, provide great manual profile management experience

---

**Status**: Backend code updated, API scraper ready, waiting to implement manual profile form.
