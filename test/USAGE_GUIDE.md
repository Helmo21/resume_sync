# LinkedIn Job Scraper - Usage Guide

## 🚀 Quick Start - AUTO MODE (Recommended)

Scrape ALL jobs automatically with optimized configuration:

```bash
python3 parallel_scraper.py
```

**What happens:**
1. Enter job title (e.g., "DevOps")
2. Enter location (e.g., "France")
3. Press Enter for AUTO mode (default)
4. Scraper will:
   - Auto-detect total jobs available
   - Calculate optimal number of parallel sessions
   - Scrape EVERYTHING automatically
   - Save results to JSON file

**Example:**
```
Enter job title/position: DevOps
Enter location: France
Use AUTO mode? (y/n) [default: y]: [Press Enter]

✓ AUTO mode enabled
✓ Detected: 500+ jobs
✓ Configured: 3 parallel sessions, 196 jobs each
✓ Scraping ALL jobs...
```

---

## 📊 How AUTO Mode Works

### Auto-Detection
- Connects to LinkedIn search
- Detects total jobs available (or estimates)
- Returns total count

### Auto-Configuration Strategy

| Total Jobs | Sessions | Jobs/Session | Strategy |
|-----------|----------|--------------|----------|
| ≤ 50 | 1 | 60 | Single session |
| 51-200 | 2 | ~120 | Light parallel |
| 201-500 | 3 | ~196 | Medium parallel |
| 500+ | 5 | ~250 | Heavy parallel |

### Performance

- **Speed:** 10-15 jobs/minute
- **Efficiency:** ~4.7 seconds per job
- **Parallel boost:** +29% faster than single session

---

## 🎯 Single Scraper (Simple Mode)

For smaller searches or testing:

```bash
python3 linkedin_job_scraper.py
```

**Configuration:**
- Headless mode: Yes/No
- Max jobs: Any number

---

## 📁 Output Files

### JSON Format
```json
[
  {
    "title": "DevOps Engineer",
    "company": "Tech Corp",
    "location": "Paris, France",
    "description": "Full job description...",
    "job_url": "https://linkedin.com/jobs/...",
    "posted_date": "2025-11-05",
    "scraped_at": "2025-11-05T16:00:00"
  }
]
```

### File Naming
- Parallel: `linkedin_jobs_parallel_DevOps_20251105_160000.json`
- Single: `linkedin_jobs_DevOps_20251105_160000.json`

---

## ⚙️ Manual Configuration

For advanced users who want full control:

```bash
python3 parallel_scraper.py
# Choose: n (for manual mode)
# Enter: Number of sessions (e.g., 5)
# Enter: Jobs per session (e.g., 100)
```

**Use cases:**
- Specific target number of jobs
- Testing different configurations
- Maximizing speed vs safety tradeoff

---

## 🔧 Features

### ✅ Implemented
- **Auto-detection** of total jobs available
- **Auto-optimization** of session configuration
- **Parallel scraping** with multiple browsers
- **Headless mode** (runs in background)
- **Random delays** (anti-bot protection)
- **Deduplication** (removes duplicate jobs)
- **Graceful failure** (saves partial results)
- **Full descriptions** (~4000+ chars per job)

### 🎯 Anti-Bot Protection
- Random delays between jobs (2-4s)
- Random delays between pages (3-5s)
- Staggered session starts (5-15s)
- Human-like click patterns
- Browser fingerprint randomization

---

## 📈 Performance Metrics

### Test Results (DevOps in France)

**Single Session:**
- 30 jobs in 180 seconds
- 10 jobs/minute
- 100% success rate

**Parallel (2 sessions):**
- 40 jobs in 186 seconds
- 12.9 jobs/minute
- 100% success rate
- **29% faster!**

**AUTO Mode (3 sessions):**
- Target: 500+ jobs
- Expected: ~40-60 minutes for full scrape
- All jobs with descriptions

---

## 🚨 Troubleshooting

### Browser Closes Early
- **Cause:** LinkedIn anti-bot detection
- **Solution:** Increase delays, reduce sessions

### No Jobs Found
- **Cause:** Incorrect selectors or LinkedIn changes
- **Solution:** Check debug HTML files

### Description Not Extracted
- **Cause:** Selector mismatch
- **Solution:** Check `#job-details` selector in debug files

---

## 💡 Tips & Best Practices

### For Maximum Jobs
1. Use AUTO mode
2. Let it run uninterrupted
3. Don't move mouse over browser windows
4. Use headless mode

### For Speed
1. Use manual mode
2. Set 5+ parallel sessions
3. 100+ jobs per session
4. Note: Higher detection risk

### For Safety
1. Use AUTO mode (it's optimized)
2. Fewer sessions (2-3)
3. Longer delays
4. Multiple smaller runs

---

## 📝 Examples

### Example 1: Get ALL DevOps Jobs in France
```bash
python3 parallel_scraper.py
# DevOps
# France
# y (AUTO)
```

### Example 2: Quick Test (Manual)
```bash
python3 parallel_scraper.py
# Python Developer
# Paris
# n (Manual)
# 1 session
# 10 jobs
```

### Example 3: Aggressive Scraping
```bash
python3 parallel_scraper.py
# Software Engineer
# Remote
# n (Manual)
# 10 sessions
# 100 jobs each
```

---

## 🔐 Required Files

- `.env` - LinkedIn credentials (optional, for login)
- `linkedin_job_scraper.py` - Core scraper
- `parallel_scraper.py` - Parallel orchestrator

### .env Format
```
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

**Note:** Scraper works without login but may get fewer results.

---

## 🎓 Understanding the Output

### Success Indicators
```
✓ Job listing container found
✓ Found 25 job cards
✓ Description extracted (4360 chars)
✓ Scraped job 1: DevOps Engineer
```

### Warning Signs
```
✗ Could not find job listing container
✗ Browser connection lost
⚠ Could not detect total
```

### Completion
```
SESSION 1 COMPLETED: 196 jobs scraped
DEDUPLICATION COMPLETE
Total Jobs Scraped: 580
Output File: linkedin_jobs_parallel_DevOps_20251105.json
```

---

## 📊 What Gets Scraped

For each job:
- ✅ Job Title
- ✅ Company Name
- ✅ Location
- ✅ Full Description (complete text)
- ✅ Job URL
- ✅ Posted Date
- ✅ Scrape Timestamp

**Description Quality:**
- Average: 4000+ characters
- Includes: Requirements, responsibilities, benefits
- Format: Plain text (cleaned HTML)

---

## 🚀 Ready to Use!

Just run and let it do the work:
```bash
python3 parallel_scraper.py
```

The scraper will handle everything automatically! 🎉
