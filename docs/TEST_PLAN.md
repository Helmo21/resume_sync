# ResumeSync - Complete Testing Plan

## Overview
This document outlines all features and their test scenarios for the complete ResumeSync workflow.

---

## 1. AUTHENTICATION & USER MANAGEMENT

### Features:
- LinkedIn OAuth login flow
- JWT token generation and validation
- User creation and retrieval
- Session management

### Test Scenarios:
- [ ] T1.1: Create JWT token for existing user
- [ ] T1.2: Validate JWT token and extract user ID
- [ ] T1.3: Reject expired JWT token
- [ ] T1.4: Reject invalid JWT token
- [ ] T1.5: Get current user from valid token

### Test Files:
- `tests/test_auth.py`

---

## 2. PROFILE MANAGEMENT

### Features:
- Apify LinkedIn profile scraping
- Profile data storage (raw + structured)
- Profile retrieval
- Profile resync

### Test Scenarios:
- [ ] T2.1: Scrape LinkedIn profile with Apify (mocked)
- [ ] T2.2: Store profile data in database
- [ ] T2.3: Retrieve user profile from database
- [ ] T2.4: Update existing profile
- [ ] T2.5: Handle scraping errors gracefully
- [ ] T2.6: Validate profile data structure

### Test Files:
- `tests/test_profile.py`
- `tests/test_apify_scraper.py` (unit tests with mocks)

---

## 3. JOB SCRAPING

### Features:
- LinkedIn job URL scraping
- Job data extraction (title, company, description, skills)
- Job storage in database

### Test Scenarios:
- [ ] T3.1: Scrape job from LinkedIn URL (mocked)
- [ ] T3.2: Extract job title, company, description
- [ ] T3.3: Store job data in database
- [ ] T3.4: Retrieve job by ID
- [ ] T3.5: Handle invalid job URLs
- [ ] T3.6: Handle scraping failures

### Test Files:
- `tests/test_jobs.py`
- `tests/test_apify_scraper.py`

---

## 4. MULTI-AGENT AI RESUME GENERATION

### Features:
- **Agent 1**: ProfileAnalyzer - Extract key strengths, skills, experience level
- **Agent 2**: JobAnalyzer - Extract requirements, keywords, ATS terms
- **Agent 3**: MatchMaker - Match profile to job, select relevant content
- **Agent 4**: ContentWriter - Generate enhanced content with ATS optimization
- **Agent 5**: Reviewer - Validate quality and coherence

### Test Scenarios:
- [ ] T4.1: ProfileAnalyzer extracts correct insights from profile
- [ ] T4.2: JobAnalyzer extracts required skills and keywords
- [ ] T4.3: MatchMaker selects relevant experiences and skills
- [ ] T4.4: ContentWriter generates professional summary
- [ ] T4.5: ContentWriter generates job title variants
- [ ] T4.6: ContentWriter generates experience bullets (NOT paragraphs)
- [ ] T4.7: ContentWriter generates certifications (2-3)
- [ ] T4.8: ContentWriter generates projects (2-3)
- [ ] T4.9: ContentWriter generates languages
- [ ] T4.10: ContentWriter includes methodologies (GitOps, DevSecOps, SRE, Agile)
- [ ] T4.11: ContentWriter uses specific technical skills (not generic categories)
- [ ] T4.12: Reviewer validates coherence and quality
- [ ] T4.13: Full AI pipeline produces complete resume structure
- [ ] T4.14: Generated bullets start with action verbs
- [ ] T4.15: Generated bullets include metrics and outcomes

### Test Files:
- `tests/test_ai_agents.py`
- `tests/test_ai_integration.py` (full pipeline)

---

## 5. TEMPLATE SYSTEM

### Features:
- Template scanning from `/teamplate/` directory
- Template type detection
- Template metadata extraction

### Test Scenarios:
- [ ] T5.1: Scan and list all templates from directory
- [ ] T5.2: Detect template type (sales, accounting, technical, etc.)
- [ ] T5.3: Extract template metadata (name, path, type)
- [ ] T5.4: Handle missing templates directory
- [ ] T5.5: Handle empty templates directory

### Test Files:
- `tests/test_template_handler.py`

---

## 6. INTELLIGENT TEMPLATE MATCHING

### Features:
- Job analysis for template selection
- Template scoring based on job type
- Template selection with justification
- Select 2 best templates automatically

### Test Scenarios:
- [ ] T6.1: Analyze job and determine best template type
- [ ] T6.2: Score templates based on job keywords
- [ ] T6.3: Select 2 most relevant templates
- [ ] T6.4: Generate justification for each template choice
- [ ] T6.5: DevOps job selects technical/ATS templates
- [ ] T6.6: Sales job selects sales templates
- [ ] T6.7: Accounting job selects accounting templates

### Test Files:
- `tests/test_template_matcher.py`

---

## 7. DOCUMENT GENERATION

### Features:
- **PDF Generation**: Modern, ATS-friendly PDF with all sections
- **DOCX Generation**: ATS-optimized DOCX with standard formatting
- **New Sections**: Certifications, Projects, Languages
- **Bullet Points**: Work experience as bullets with action verbs
- **Header**: Job title variants, phone, email, location, LinkedIn, GitHub

### Test Scenarios:
- [ ] T7.1: Generate PDF with complete resume data
- [ ] T7.2: Generate DOCX with complete resume data
- [ ] T7.3: PDF includes job title variants in header
- [ ] T7.4: PDF displays experience as bullet points
- [ ] T7.5: PDF includes certifications section
- [ ] T7.6: PDF includes projects section
- [ ] T7.7: PDF includes languages section
- [ ] T7.8: DOCX includes all new sections
- [ ] T7.9: DOCX uses ATS-friendly formatting (no tables for content)
- [ ] T7.10: Skills section shows specific tools (not generic categories)
- [ ] T7.11: Files are created at specified output paths
- [ ] T7.12: Generated PDFs are valid and openable
- [ ] T7.13: Generated DOCX are valid and openable

### Test Files:
- `tests/test_document_generator.py`

---

## 8. RESUME OPTIONS ENDPOINT (Complete Workflow)

### Features:
- Full end-to-end workflow
- Scrape job → Analyze → Match templates → Generate 2 resumes
- Return preview URLs and download URLs

### Test Scenarios:
- [ ] T8.1: Complete workflow with valid job URL
- [ ] T8.2: Returns 2 resume options
- [ ] T8.3: Each option has PDF and DOCX URLs
- [ ] T8.4: Each option has template info and score
- [ ] T8.5: Each option has justification
- [ ] T8.6: Generated files exist at specified URLs
- [ ] T8.7: Handle job scraping failure gracefully
- [ ] T8.8: Handle AI generation failure gracefully
- [ ] T8.9: Handle template selection failure gracefully
- [ ] T8.10: Process completes within reasonable time (< 3 minutes)

### Test Files:
- `tests/test_api_resume_options.py`
- `tests/test_integration_full_workflow.py`

---

## 9. FILE STORAGE & SERVING

### Features:
- Save generated PDFs and DOCX to `/app/generated_resumes/`
- Serve files via static URLs
- Unique file naming (option_id + uuid + template_id)

### Test Scenarios:
- [ ] T9.1: Save PDF to correct directory
- [ ] T9.2: Save DOCX to correct directory
- [ ] T9.3: Files have unique names
- [ ] T9.4: Files are accessible via HTTP URLs
- [ ] T9.5: Handle disk space errors
- [ ] T9.6: Clean up old files if needed

### Test Files:
- `tests/test_file_storage.py`

---

## 10. ERROR HANDLING & EDGE CASES

### Test Scenarios:
- [ ] T10.1: Handle empty profile data
- [ ] T10.2: Handle missing job description
- [ ] T10.3: Handle API timeout (Apify)
- [ ] T10.4: Handle AI API failures (OpenRouter)
- [ ] T10.5: Handle invalid template paths
- [ ] T10.6: Handle missing user in database
- [ ] T10.7: Validate input data types
- [ ] T10.8: Handle concurrent requests

### Test Files:
- `tests/test_error_handling.py`

---

## TEST EXECUTION STRATEGY

### Phase 1: Unit Tests (Individual Components)
```bash
# Test each component in isolation
pytest tests/test_auth.py -v
pytest tests/test_profile.py -v
pytest tests/test_jobs.py -v
pytest tests/test_ai_agents.py -v
pytest tests/test_template_handler.py -v
pytest tests/test_template_matcher.py -v
pytest tests/test_document_generator.py -v
```

### Phase 2: Integration Tests (Component Interactions)
```bash
# Test components working together
pytest tests/test_ai_integration.py -v
pytest tests/test_api_resume_options.py -v
```

### Phase 3: End-to-End Tests (Full Workflow)
```bash
# Test complete user journey
pytest tests/test_integration_full_workflow.py -v
```

### Phase 4: Run All Tests
```bash
pytest tests/ -v --cov=app --cov-report=html
```

---

## TEST DATA

### Mock Profile Data
- `tests/fixtures/mock_profile.json` - Complete LinkedIn profile
- `tests/fixtures/mock_profile_minimal.json` - Minimal profile data

### Mock Job Data
- `tests/fixtures/mock_job_devops.json` - DevOps job posting
- `tests/fixtures/mock_job_sales.json` - Sales job posting
- `tests/fixtures/mock_job_accounting.json` - Accounting job posting

### Expected Outputs
- `tests/fixtures/expected_resume_structure.json` - Expected resume format
- `tests/fixtures/expected_ai_output.json` - Expected AI generation output

---

## TESTING TOOLS

- **pytest**: Test framework
- **pytest-cov**: Code coverage
- **pytest-mock**: Mocking library
- **pytest-asyncio**: Async testing
- **httpx**: HTTP client for API testing
- **faker**: Generate fake test data

---

## MOCKING STRATEGY

### External Services to Mock:
1. **Apify API** - Mock profile and job scraping
2. **OpenRouter API** - Mock AI responses
3. **File System** - Use temp directories for tests
4. **Database** - Use in-memory SQLite or test DB

### Why Mock?
- Tests run faster (no network calls)
- Tests are deterministic (no API failures)
- Tests don't cost money (no API usage)
- Tests can run offline

---

## CONTINUOUS INTEGRATION

### GitHub Actions Workflow (Future)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ -v --cov=app
```

---

## SUCCESS CRITERIA

### For Each Feature:
- ✅ All test scenarios pass
- ✅ Code coverage > 80%
- ✅ No critical bugs
- ✅ Performance within acceptable limits

### For Complete Workflow:
- ✅ Can generate 2 resume options from job URL
- ✅ All ATS optimizations present
- ✅ Files are generated correctly
- ✅ Process completes in < 3 minutes
- ✅ Error handling works for all failure cases
