# How to Set Up LinkedIn Service Accounts

## Why Do I Need This?

The job scraping feature needs LinkedIn accounts to search and scrape job postings. You cannot use the LinkedIn API directly for this purpose, so we use dedicated "scraping accounts" that log in and search like a normal user would.

**IMPORTANT**: Do NOT use your personal LinkedIn account for this! Create dedicated scraping accounts.

---

## Step 1: Create LinkedIn Accounts

You need **at least 2-3 LinkedIn accounts** for proper rotation and reliability.

### Option A: Use Temporary Email Services (Recommended)

1. **Go to a temporary email service**:
   - [TempMail](https://temp-mail.org/)
   - [Guerrilla Mail](https://www.guerrillamail.com/)
   - [10 Minute Mail](https://10minutemail.com/)

2. **Create new LinkedIn accounts**:
   - Use the temporary email as the LinkedIn email
   - Choose a strong password
   - Complete basic profile setup (name, headline, location)
   - Add a profile photo (stock photos work fine)
   - Connect with a few people (makes account look more legitimate)

3. **Repeat 2-3 times** to create multiple accounts

### Option B: Use Your Own Emails

If you have multiple email addresses (Gmail, Outlook, etc.):
1. Create new LinkedIn accounts with each email
2. Use different names (or slight variations)
3. Complete basic profiles

**Tip**: Gmail allows `+` aliases:
- `youremail+linkedin1@gmail.com`
- `youremail+linkedin2@gmail.com`
- All go to the same inbox!

---

## Step 2: Configure .env File

1. **Edit `backend/.env`** and find this section:

```bash
# LinkedIn Service Accounts
LINKEDIN_SERVICE_ACCOUNTS="scraper1@example.com:Password123!|scraper2@example.com:Password456!"
```

2. **Replace with your actual accounts**:

```bash
LINKEDIN_SERVICE_ACCOUNTS="linkedin_bot1@tempmail.com:MyPassword1!|linkedin_bot2@tempmail.com:MyPassword2!|linkedin_bot3@tempmail.com:MyPassword3!"
```

**Format**: `email:password|email2:password2|email3:password3`

**Example with 3 accounts**:
```bash
LINKEDIN_SERVICE_ACCOUNTS="john.smith.dev@gmail.com:SecurePass123!|jane.doe.tech@outlook.com:AnotherPass456!|dev.account@tempmail.com:ThirdPass789!"
```

3. **Optional: Mark premium accounts** (if you have LinkedIn Premium):

```bash
LINKEDIN_PREMIUM_ACCOUNTS="john.smith.dev@gmail.com,jane.doe.tech@outlook.com"
```

Premium accounts get used first and have better rate limits.

---

## Step 3: Test Your Setup

1. **Deploy the application**:

```bash
./deploy-integration.sh
```

2. **Check if accounts were loaded**:

```bash
docker compose logs backend | grep "Loaded service account"
```

You should see:
```
✅ Loaded service account: joh***@gmail.com
✅ Loaded service account: jan***@outlook.com
```

3. **Verify account availability**:

```bash
curl "http://localhost:8000/api/jobs/service-accounts/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response should show:
```json
{
  "total_active": 3,
  "available": 3,
  "rate_limited": 0,
  "in_cooldown": 0
}
```

---

## Tips for Long-Term Success

### Keep Accounts Active
- Log in manually once a week to keep accounts active
- Accept some connection requests
- LinkedIn may flag accounts that never interact

### Account Rotation
- The system automatically rotates between accounts
- Each account can make ~100 searches per day
- With 3 accounts = 300 searches/day capacity

### When Accounts Get Blocked
If LinkedIn detects automation:
1. Account enters 30-minute cooldown automatically
2. System switches to other available accounts
3. After cooldown, account is tried again

**Solution**: Add more accounts if you see frequent blocks

### Premium Accounts
If you have LinkedIn Premium on any account:
- Add it to `LINKEDIN_PREMIUM_ACCOUNTS`
- System will use it first
- Premium accounts have better rate limits

---

## Security Best Practices

### ✅ DO:
- Use dedicated accounts ONLY for scraping
- Use strong, unique passwords
- Keep `.env` file secure (never commit to git)
- Use temporary/burner email services
- Create realistic-looking profiles

### ❌ DON'T:
- Use your personal LinkedIn account
- Share account credentials
- Commit `.env` file to version control
- Use obviously fake profiles (empty, no photo)
- Scrape at excessive rates

---

## Troubleshooting

### "No service accounts available"

**Check 1**: Is `.env` configured correctly?
```bash
cat backend/.env | grep LINKEDIN_SERVICE_ACCOUNTS
```

Should show your actual emails, not `scraper1@example.com`

**Check 2**: Did accounts load on startup?
```bash
docker compose logs backend | grep "service account"
```

**Check 3**: Are accounts blocked/rate-limited?
```bash
curl "http://localhost:8000/api/jobs/service-accounts/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### "All accounts are rate limited"

You've hit the daily limit (100 requests/day per account).

**Solutions**:
1. Wait for daily reset (midnight UTC)
2. Add more accounts to `.env`
3. Increase `DAILY_REQUEST_LIMIT` in code (risky)

### "Account marked as failed - entering cooldown"

LinkedIn detected automation on that account.

**Solutions**:
1. System automatically enters 30-min cooldown
2. Other accounts will be used meanwhile
3. Log in manually to the account to "reset" it
4. If happens frequently, retire that account and create a new one

### "Login failed" or "Security challenge detected"

LinkedIn is asking for verification (CAPTCHA, 2FA, etc.)

**Solutions**:
1. Log in manually to that account in a browser
2. Complete any verification steps
3. Disable 2FA if enabled
4. Account should work again after manual login

---

## Example: Complete Setup

### 1. Create 3 LinkedIn Accounts

| Email | Password | Name | Status |
|-------|----------|------|--------|
| `dev_scraper1@tempmail.com` | `SecurePass1!` | John Developer | ✅ Active |
| `jobbot2@gmail.com` | `SecurePass2!` | Jane Techie | ✅ Active |
| `linkedinbot3@outlook.com` | `SecurePass3!` | Bob Coder | ✅ Active |

### 2. Configure .env

```bash
LINKEDIN_SERVICE_ACCOUNTS="dev_scraper1@tempmail.com:SecurePass1!|jobbot2@gmail.com:SecurePass2!|linkedinbot3@outlook.com:SecurePass3!"
```

### 3. Deploy

```bash
./deploy-integration.sh
```

### 4. Verify

```bash
docker compose logs backend | tail -20
```

Should see:
```
✅ Loaded service account: dev***@tempmail.com
✅ Loaded service account: job***@gmail.com
✅ Loaded service account: lin***@outlook.com

📊 Service Account Summary:
   ✅ Loaded: 3
   ℹ️  Already exists: 0
   ❌ Failed: 0

🔐 Service Accounts Status:
   Total active: 3
   Available now: 3
   Rate limited: 0
   In cooldown: 0
```

✅ **You're all set!** The system will automatically use and rotate these accounts.

---

## Need Help?

1. Check backend logs: `docker compose logs backend -f`
2. Review [QUICK_START.md](./QUICK_START.md) for testing
3. See [INTEGRATION_COMPLETE.md](./INTEGRATION_COMPLETE.md) for full docs

**Remember**: LinkedIn service accounts are the foundation of the job scraping feature. Take time to set them up properly!
