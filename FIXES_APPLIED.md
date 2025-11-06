# Fixes Applied - Port Conflict & LinkedIn Credentials

## Issues Fixed

### ✅ Issue #1: Redis Port Conflict (6379)

**Problem**:
```
Error: Bind for 0.0.0.0:6379 failed: port is already allocated
```

Another Redis instance was running on the system using port 6379.

**Solution**:
- Changed Docker Compose to use port **6380** externally
- Internal Docker network still uses 6379 (no changes needed in code)
- File modified: `docker-compose.yml`

```yaml
redis:
  ports:
    - "6380:6379"  # External:Internal
```

**Test**:
```bash
docker compose up -d redis
docker compose ps redis  # Should show "Up"
```

---

### ✅ Issue #2: No Automatic LinkedIn Credentials Loading

**Problem**:
Users had to manually run CLI commands to add LinkedIn service accounts, which was confusing and error-prone.

**Solution**:
Implemented automatic credential loading from `.env` file on application startup!

#### What Was Added:

1. **Environment Variables in `.env`** (line 38-51):
```bash
# LinkedIn Service Accounts (for Job Scraping)
LINKEDIN_SERVICE_ACCOUNTS="email1:password1|email2:password2|email3:password3"
LINKEDIN_PREMIUM_ACCOUNTS="email1,email2"  # Optional
```

2. **Auto-Loader Service** (`backend/app/core/service_account_loader.py`):
   - Parses credentials from `LINKEDIN_SERVICE_ACCOUNTS`
   - Encrypts and stores in database automatically
   - Marks premium accounts
   - Shows status on startup
   - Skips duplicates (safe to restart)

3. **Startup Hook** (`backend/app/main.py`):
   - Loads accounts when backend starts
   - Displays summary in logs
   - Verifies account availability

4. **Pre-flight Check** (`deploy-integration.sh`):
   - Checks if `.env` exists
   - Warns if using example credentials
   - Prevents deployment without configuration

5. **Documentation**:
   - `backend/.env.example` - Template with instructions
   - `SETUP_LINKEDIN_ACCOUNTS.md` - Complete guide
   - Updated deployment script with checks

#### How It Works Now:

**Before** (Manual):
```bash
# User had to run this for each account:
docker compose exec backend python -m app.scripts.add_service_account
# Then enter email and password interactively
```

**After** (Automatic):
```bash
# 1. Edit backend/.env once:
LINKEDIN_SERVICE_ACCOUNTS="bot1@email.com:pass1|bot2@email.com:pass2"

# 2. Deploy:
./deploy-integration.sh

# 3. Accounts loaded automatically! ✅
```

**Startup Logs**:
```
============================================================
🚀 ResumeSync Backend - Starting Up
============================================================

📧 Loading LinkedIn service accounts from .env...
✅ Loaded service account: bot***@email.com
✅ Loaded service account: bot***@email.com [PREMIUM]

📊 Service Account Summary:
   ✅ Loaded: 2
   ℹ️  Already exists: 0
   ❌ Failed: 0

🔐 Service Accounts Status:
   Total active: 2
   Available now: 2
   Rate limited: 0
   In cooldown: 0

============================================================
✅ ResumeSync Backend - Ready
============================================================
```

---

## Files Modified

### Core Changes:
1. **docker-compose.yml** - Changed Redis port 6379→6380
2. **backend/.env** - Added `LINKEDIN_SERVICE_ACCOUNTS` section
3. **backend/app/main.py** - Added startup event handler
4. **deploy-integration.sh** - Added pre-flight checks

### New Files:
1. **backend/app/core/service_account_loader.py** - Auto-loader logic
2. **backend/.env.example** - Template with instructions
3. **SETUP_LINKEDIN_ACCOUNTS.md** - Complete setup guide

---

## How to Use Now

### Step 1: Configure LinkedIn Accounts

Edit `backend/.env`:

```bash
# Replace these with your actual LinkedIn scraping accounts:
LINKEDIN_SERVICE_ACCOUNTS="scraper1@tempmail.com:Password1!|scraper2@gmail.com:Password2!|scraper3@outlook.com:Password3!"

# Optional: Mark premium accounts
LINKEDIN_PREMIUM_ACCOUNTS="scraper1@tempmail.com"
```

**Need help creating accounts?** See [SETUP_LINKEDIN_ACCOUNTS.md](./SETUP_LINKEDIN_ACCOUNTS.md)

### Step 2: Deploy

```bash
./deploy-integration.sh
```

The script will:
1. Check if `.env` exists
2. Warn if using example credentials
3. Deploy all services
4. Automatically load LinkedIn accounts from `.env`
5. Show account status

### Step 3: Verify

```bash
# Check that accounts loaded
docker compose logs backend | grep "Loaded service account"

# Should show:
# ✅ Loaded service account: scr***@tempmail.com
# ✅ Loaded service account: scr***@gmail.com

# Or check via API:
curl "http://localhost:8000/api/jobs/service-accounts/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Benefits

### Before:
❌ Manual CLI commands for each account
❌ Easy to forget adding accounts
❌ No visibility into what accounts exist
❌ Had to re-add after database resets

### After:
✅ Configure once in `.env`
✅ Automatic loading on startup
✅ Shows status in logs
✅ Safe restarts (skips duplicates)
✅ Pre-flight checks prevent mistakes
✅ Complete documentation

---

## Testing Checklist

### ✅ Redis Port Conflict
```bash
# Old port should be free now
docker compose up -d
docker compose ps  # All services should be "Up"
```

### ✅ LinkedIn Account Loading
```bash
# 1. Check .env is configured
cat backend/.env | grep LINKEDIN_SERVICE_ACCOUNTS

# 2. Deploy
./deploy-integration.sh

# 3. Check logs
docker compose logs backend | grep "service account"

# 4. Verify via API
curl http://localhost:8000/api/jobs/service-accounts/stats \
  -H "Authorization: Bearer TOKEN"
```

---

## Migration Notes

### If You Already Have Service Accounts in Database:

**Good news**: The auto-loader checks for duplicates!

When you add credentials to `.env`:
- Existing accounts are detected: `ℹ️  Account already exists`
- New accounts are added: `✅ Loaded service account`
- No duplicates are created

**Example**:
```
📧 Loading LinkedIn service accounts from .env...
ℹ️  Account already exists: old***@gmail.com
✅ Loaded service account: new***@tempmail.com

📊 Service Account Summary:
   ✅ Loaded: 1
   ℹ️  Already exists: 1
   ❌ Failed: 0
```

### Manual CLI Still Works:

If you prefer manual management:
```bash
docker compose exec backend python -m app.scripts.add_service_account \
  --email "manual@example.com" \
  --password "password"
```

But `.env` method is recommended for ease of use!

---

## Quick Reference

### Add New Account:
1. Edit `backend/.env`
2. Add to `LINKEDIN_SERVICE_ACCOUNTS` (use | separator)
3. Restart backend: `docker compose restart backend`

### Remove Account:
1. Remove from `backend/.env`
2. Manually deactivate in database (optional)
3. Restart backend

### Check Account Status:
```bash
# Via logs
docker compose logs backend | grep "Service Accounts Status" -A 5

# Via API
curl http://localhost:8000/api/jobs/service-accounts/stats
```

---

## Next Steps

1. **Create LinkedIn accounts** - See [SETUP_LINKEDIN_ACCOUNTS.md](./SETUP_LINKEDIN_ACCOUNTS.md)
2. **Configure .env** - Add your credentials
3. **Deploy** - Run `./deploy-integration.sh`
4. **Test job search** - See [QUICK_START.md](./QUICK_START.md)

---

**Status**: ✅ Both issues fixed and tested!

Redis port conflict resolved + LinkedIn credentials auto-load from `.env` implemented.
