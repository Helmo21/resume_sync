# Resume-to-Jobs Matching Feature - Technical Design

**Feature Goal**: Upload a resume and find the most relevant LinkedIn job postings that match the candidate's profile.

---

## 1. High-Level Architecture

```
┌─────────────────┐
│  User uploads   │
│     Resume      │
│  (PDF/DOCX)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           STEP 1: Resume Analysis (AI Agent)            │
│  - Extract personal info (name, email, location)        │
│  - Extract skills (technical + soft)                    │
│  - Identify job titles & seniority level                │
│  - Determine industries & domains                       │
│  - Infer preferences (remote, salary range, etc.)       │
│  - Extract years of experience                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Structured     │
         │ Search Profile │
         │ (JSON)         │
         └────────┬───────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│    STEP 2: LinkedIn Search Query Generation (AI)        │
│  - Generate optimal search keywords                     │
│  - Determine location filters                           │
│  - Set experience level filters                         │
│  - Define date range (e.g., last 7 days)                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│      STEP 3: LinkedIn Job Scraping (Apify/Scraper)      │
│  - Execute multiple searches (different keyword combos) │
│  - Scrape job listings (50-100 jobs)                    │
│  - Extract: title, company, location, description, etc. │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│   STEP 4: Job Matching & Scoring (Multi-Agent AI)       │
│  - Match each job against resume profile                │
│  - Calculate match score (0-100%)                       │
│  - Identify matching skills                             │
│  - Flag missing requirements                            │
│  - Rank jobs by relevance                               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│          STEP 5: Results Presentation                    │
│  - Top N jobs (sorted by match score)                   │
│  - Each job shows:                                      │
│    * Match percentage                                   │
│    * Matching skills                                    │
│    * Missing requirements                               │
│    * Estimated fit explanation                          │
│  - Filter/sort options                                  │
│  - One-click "Generate Resume" for selected job         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Technical Components

### 2.1 Resume Parser Service
**File**: `backend/app/services/resume_parser.py`

**Responsibilities**:
- Parse PDF/DOCX files
- Extract text content
- Handle various resume formats

**Libraries**:
- `pypdf2` (already installed) for PDFs
- `python-docx` (already installed) for DOCX
- `pdfplumber` (optional, better PDF parsing)

### 2.2 Resume Analyzer Agent (AI)
**File**: `backend/app/services/resume_analyzer_agent.py`

**Input**: Raw resume text
**Output**: Structured profile JSON

```json
{
  "personal_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "location": "San Francisco, CA",
    "phone": "+1234567890"
  },
  "professional_summary": "Senior software engineer with 7 years...",
  "target_roles": [
    "Senior Software Engineer",
    "Lead Developer",
    "Engineering Manager"
  ],
  "skills": {
    "technical": ["Python", "React", "AWS", "Docker"],
    "soft": ["Leadership", "Communication", "Problem-solving"]
  },
  "experience": {
    "years_total": 7,
    "seniority_level": "Senior",
    "industries": ["Tech", "SaaS", "E-commerce"]
  },
  "preferences": {
    "remote": true,
    "location_flexibility": "high",
    "estimated_salary_range": "$120k-$180k"
  },
  "education": [
    {
      "degree": "BS Computer Science",
      "institution": "University"
    }
  ]
}
```

### 2.3 Search Query Generator Agent (AI)
**File**: `backend/app/services/search_query_generator.py`

**Input**: Structured profile JSON
**Output**: LinkedIn search parameters

```json
{
  "search_queries": [
    {
      "keywords": "Senior Software Engineer Python React",
      "location": "San Francisco Bay Area",
      "experience_level": ["Mid-Senior level", "Director"],
      "date_posted": "past-week",
      "remote": true
    },
    {
      "keywords": "Lead Developer AWS Kubernetes",
      "location": "Remote",
      "experience_level": ["Mid-Senior level"],
      "date_posted": "past-week"
    }
  ],
  "max_results_per_query": 50
}
```

### 2.4 LinkedIn Job Scraper
**File**: `backend/app/services/linkedin_job_scraper.py`

**Options**:
- **Option A**: Use existing Apify LinkedIn scraper
- **Option B**: Build custom scraper with Selenium/Camoufox
- **Option C**: Use LinkedIn Job Search API (requires partnership)

**Recommended**: Option A (Apify) - already integrated

**Apify Actor**: `misceres/linkedin-jobs-search-scraper`

Parameters:
```python
{
  "keywords": "Senior Software Engineer",
  "location": "San Francisco",
  "remote": true,
  "datePosted": "past-week",
  "experienceLevel": ["3", "4"],  # Mid-Senior, Director
  "maxResults": 50
}
```

### 2.5 Job Matcher Agent (AI)
**File**: `backend/app/services/job_matcher_agent.py`

**Agent Type**: Similar to existing MatchMaker agent, but reversed

**Input**:
- User's resume profile
- Scraped job posting

**Output**: Match analysis
```json
{
  "job_id": "linkedin-job-123",
  "match_score": 87,
  "matching_skills": ["Python", "React", "AWS", "Docker"],
  "missing_requirements": ["Go", "GraphQL"],
  "experience_fit": "perfect",
  "location_fit": "remote_match",
  "salary_fit": "likely_match",
  "explanation": "Strong match. Your 7 years of Python and React experience align perfectly with the Senior Engineer role. Company uses similar tech stack (AWS, Docker). Missing: Go and GraphQL, but likely learnable.",
  "recommendation": "highly_recommended"
}
```

---

## 3. Database Schema

### New Table: `job_searches`
```sql
CREATE TABLE job_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,

    -- Uploaded resume
    uploaded_resume_url TEXT,
    parsed_resume_text TEXT,

    -- Analyzed profile
    analyzed_profile JSONB NOT NULL,

    -- Search parameters
    search_queries JSONB NOT NULL,

    -- Metadata
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    total_jobs_found INTEGER DEFAULT 0,
    total_jobs_matched INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### New Table: `matched_jobs`
```sql
CREATE TABLE matched_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_search_id UUID REFERENCES job_searches(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,

    -- Job details (from LinkedIn scraping)
    linkedin_job_id VARCHAR(255) UNIQUE,
    job_title VARCHAR(500),
    company_name VARCHAR(500),
    location VARCHAR(255),
    employment_type VARCHAR(100),
    seniority_level VARCHAR(100),
    description TEXT,
    requirements TEXT,
    job_url TEXT NOT NULL,

    -- Matching analysis
    match_score INTEGER,  -- 0-100
    matching_skills JSONB,
    missing_requirements JSONB,
    match_analysis JSONB,

    -- User actions
    is_saved BOOLEAN DEFAULT false,
    is_applied BOOLEAN DEFAULT false,
    notes TEXT,

    -- Timestamps
    posted_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. API Endpoints

### 4.1 Upload Resume & Start Search
```
POST /api/job-search/upload-resume
Content-Type: multipart/form-data

Body:
  - resume_file: File (PDF/DOCX)
  - search_preferences: JSON (optional overrides)
    {
      "location": "San Francisco",
      "remote_only": true,
      "max_results": 50
    }

Response:
{
  "job_search_id": "uuid",
  "status": "processing",
  "message": "Analyzing your resume and searching for jobs..."
}
```

### 4.2 Check Search Status
```
GET /api/job-search/{job_search_id}/status

Response:
{
  "job_search_id": "uuid",
  "status": "processing",  -- or "completed", "failed"
  "progress": {
    "step": "scraping_jobs",
    "current": 25,
    "total": 50
  },
  "analyzed_profile": {...},
  "jobs_found": 45,
  "jobs_matched": 25
}
```

### 4.3 Get Matched Jobs
```
GET /api/job-search/{job_search_id}/results
Query params:
  - min_score: 70 (optional)
  - sort_by: match_score | posted_date (default: match_score)
  - limit: 20 (default)

Response:
{
  "job_search_id": "uuid",
  "total_results": 45,
  "analyzed_profile": {
    "target_roles": ["Senior Software Engineer"],
    "key_skills": ["Python", "React", "AWS"]
  },
  "jobs": [
    {
      "id": "uuid",
      "linkedin_job_id": "123456",
      "job_title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "location": "Remote",
      "match_score": 92,
      "matching_skills": ["Python", "React", "AWS", "Docker"],
      "missing_requirements": ["Go"],
      "explanation": "Excellent match...",
      "job_url": "https://linkedin.com/jobs/view/123456",
      "posted_date": "2025-10-19"
    },
    ...
  ]
}
```

### 4.4 Save/Unsave Job
```
POST /api/job-search/matched-jobs/{job_id}/save
DELETE /api/job-search/matched-jobs/{job_id}/save
```

### 4.5 Generate Resume for Matched Job
```
POST /api/job-search/matched-jobs/{job_id}/generate-resume

Body:
{
  "template_id": "modern",
  "format": "pdf"
}

Response:
{
  "resume_id": "uuid",
  "download_url": "/api/resumes/{resume_id}/download"
}
```

---

## 5. AI Agent Pipeline

### Agent 1: Resume Analyzer
**Model**: Claude 3.5 Sonnet
**Prompt Template**:
```
Analyze this resume and extract:
1. Personal information
2. Target job roles (what they're looking for)
3. All skills (technical and soft)
4. Years of experience and seniority level
5. Industries they've worked in
6. Inferred preferences (remote, location, etc.)

Resume text:
{resume_text}

Return structured JSON.
```

### Agent 2: Search Query Generator
**Model**: Claude 3.5 Sonnet or GPT-4o-mini
**Prompt Template**:
```
Based on this candidate profile, generate 3-5 optimal LinkedIn job search queries:

Profile:
{analyzed_profile}

For each query, specify:
- Keywords (job title + key skills)
- Location filters
- Experience level
- Other filters

Return structured JSON array of search queries.
```

### Agent 3: Job Matcher
**Model**: Claude 3.5 Sonnet
**Prompt Template**:
```
Compare this candidate's profile against this job posting:

Candidate Profile:
{analyzed_profile}

Job Posting:
{job_description}

Calculate:
1. Match score (0-100)
2. Matching skills
3. Missing requirements
4. Overall fit assessment
5. Recommendation (highly_recommended, recommended, maybe, not_recommended)

Return structured JSON.
```

---

## 6. Implementation Phases

### Phase 1: Resume Upload & Parsing (Week 1)
- [ ] Create resume upload endpoint
- [ ] Implement PDF/DOCX parser
- [ ] Store uploaded resumes (local or S3)
- [ ] Create `job_searches` table
- [ ] Basic error handling

### Phase 2: Resume Analysis AI Agent (Week 1-2)
- [ ] Create ResumeAnalyzerAgent
- [ ] Design prompt templates
- [ ] Test with various resume formats
- [ ] Validate extracted data quality
- [ ] Handle edge cases (non-standard resumes)

### Phase 3: Search Query Generation (Week 2)
- [ ] Create SearchQueryGenerator agent
- [ ] Generate optimal LinkedIn search parameters
- [ ] Support multiple query variations
- [ ] Test query quality

### Phase 4: LinkedIn Job Scraping (Week 2-3)
- [ ] Integrate Apify LinkedIn Jobs scraper
- [ ] Handle pagination & rate limits
- [ ] Deduplicate jobs across searches
- [ ] Store raw job data
- [ ] Create `matched_jobs` table

### Phase 5: Job Matching AI Agent (Week 3)
- [ ] Create JobMatcher agent
- [ ] Implement match scoring algorithm
- [ ] Generate explanations
- [ ] Rank and filter results
- [ ] Performance optimization (parallel matching)

### Phase 6: API & Frontend (Week 3-4)
- [ ] Create all API endpoints
- [ ] Build upload UI component
- [ ] Build results display (job cards with scores)
- [ ] Add filtering/sorting
- [ ] Integrate with existing resume generator

### Phase 7: Testing & Optimization (Week 4)
- [ ] End-to-end testing
- [ ] Performance testing (handle 50-100 jobs)
- [ ] UI/UX refinements
- [ ] Error handling improvements

---

## 7. Technical Challenges & Solutions

### Challenge 1: LinkedIn Scraping Rate Limits
**Problem**: LinkedIn may block excessive scraping
**Solutions**:
- Use Apify (they handle proxies & rate limits)
- Implement exponential backoff
- Cache results for 24 hours
- Limit to 50-100 jobs per search

### Challenge 2: AI Cost Management
**Problem**: Analyzing 50-100 jobs with AI is expensive
**Solutions**:
- Use cheaper model (GPT-4o-mini) for initial filtering
- Only use Claude 3.5 for top 20 candidates
- Batch requests when possible
- Cache match scores for duplicate jobs

### Challenge 3: Processing Time
**Problem**: Full pipeline may take 2-5 minutes
**Solutions**:
- Make it asynchronous (background job)
- Show progress bar to user
- Send email/notification when complete
- Allow user to browse partial results

### Challenge 4: Resume Format Variability
**Problem**: Resumes come in many formats
**Solutions**:
- Use robust PDF parser (pdfplumber)
- AI is good at handling unstructured text
- Provide manual override for key info
- Show extracted profile for user verification

---

## 8. Cost Estimation

### Per Search (50 jobs):
- Resume analysis: 1 AI call (~$0.01)
- Search query generation: 1 AI call (~$0.005)
- Job matching: 50 AI calls (~$0.50 - $1.00)
- LinkedIn scraping: ~$0.10 (Apify)

**Total per search**: ~$0.60 - $1.10

**Optimization**:
- Filter to top 20 jobs before AI matching: ~$0.25/search

---

## 9. User Experience Flow

```
1. User clicks "Find Jobs for My Resume"
2. Upload resume (PDF/DOCX) + set preferences
3. [Processing screen - 2-5 minutes]
   - "Analyzing your resume..."
   - "Searching LinkedIn for matching jobs..."
   - "Scoring job matches..."
4. Results page:
   - Shows analyzed profile summary
   - List of jobs sorted by match score
   - Each job card shows:
     * Company, title, location
     * Match score (92%)
     * Matching skills (badges)
     * Missing requirements
     * "Save" / "Generate Resume" buttons
5. Click "Generate Resume" → uses existing flow
```

---

## 10. Next Steps - What Do You Think?

**Questions for you:**
1. Does this architecture match your vision?
2. Any components you want to add/remove/modify?
3. Should we start with Phase 1, or do you want to prototype something first?
4. Any specific constraints (budget, timeline, priorities)?

**My Recommendations:**
- Start with Phases 1-2 (upload + analyze) to validate the concept
- Use Apify for LinkedIn scraping (easiest)
- Make it async from the start (better UX)
- Show top 20 jobs by default (avoid overwhelming users)

Let's discuss and refine this design together!
