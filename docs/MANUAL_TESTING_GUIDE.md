# ResumeSync Manual Testing Guide

## Overview
This guide provides step-by-step instructions to test the complete UI workflow after fixing the profile sync error.

**Fix Applied:** Removed the "Sync Profile" button from Dashboard that was causing 501 errors.

---

## Prerequisites

1. **Backend Running**: http://localhost:8000
2. **Frontend Running**: http://localhost:5173
3. **LinkedIn OAuth configured** with valid credentials
4. **Apify API key** configured in backend `.env`

---

## Test Workflow

### 1. Dashboard Load Test

**Objective:** Verify the Dashboard loads without the 501 profile sync error

**Steps:**
1. Open browser and navigate to: `http://localhost:5173`
2. Login with LinkedIn OAuth
3. Wait for Dashboard to load
4. Open browser DevTools (F12) and check Console tab

**Expected Result:**
- ✓ Dashboard loads successfully
- ✓ No 501 error in console
- ✓ Profile data is displayed (name, experience, skills, etc.)
- ✓ "Sync Profile" button is NOT present
- ✓ Only "Last synced" date is shown in profile section

**Failure Indicators:**
- ✗ 501 error appears in console
- ✗ "Sync Profile" button still visible
- ✗ Dashboard fails to load

---

### 2. Navigation Test

**Objective:** Verify navigation between pages works correctly

**Steps:**
1. From Dashboard, click "Generate Resume" card
2. Verify you're redirected to `/generate` page
3. Click browser back button
4. From Dashboard, click "Resume History" card
5. Verify you're redirected to `/history` page

**Expected Result:**
- ✓ Navigation works smoothly
- ✓ No errors in console
- ✓ Pages load correctly

---

### 3. Job Scraping Test

**Objective:** Test the complete job scraping workflow

**Test Job URL:**
```
https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4304103657
```

**Steps:**
1. Navigate to "Generate Resume" page
2. Paste the test job URL into the input field
3. Click "Scrape Job" button
4. Wait for scraping to complete (may take 30-60 seconds)
5. Check the job preview section

**Expected Result:**
- ✓ Scraping starts successfully
- ✓ Loading indicator appears
- ✓ Job preview displays with:
  - Job title
  - Company name
  - Location
  - Job description
  - Required skills
  - Employment type
- ✓ No errors in console

**Failure Indicators:**
- ✗ Scraping fails with error
- ✗ Job preview doesn't appear
- ✗ Timeout or network errors

---

### 4. Template Selection Test

**Objective:** Verify resume template selection works

**Steps:**
1. After successful job scraping, scroll to "Choose Template" section
2. Review available templates (Modern, Classic, Technical)
3. Click on each template to preview
4. Select one template (e.g., "Modern")

**Expected Result:**
- ✓ Templates are displayed with previews
- ✓ Clicking a template highlights it
- ✓ Template selection is saved
- ✓ "Generate Resume" button becomes enabled

---

### 5. Resume Generation Test

**Objective:** Test AI-powered resume generation

**Steps:**
1. With a job scraped and template selected, click "Generate Resume"
2. Wait for generation to complete (may take 15-30 seconds)
3. Review the generated resume preview

**Expected Result:**
- ✓ Generation starts successfully
- ✓ Loading indicator appears
- ✓ Resume preview displays with:
  - Your profile information
  - Tailored experience descriptions
  - Relevant skills highlighted
  - Professional formatting
- ✓ Download buttons (PDF/DOCX) appear
- ✓ No errors in console

**Failure Indicators:**
- ✗ Generation fails or times out
- ✗ Resume preview is empty or malformed
- ✗ AI service errors appear

---

### 6. Download Test

**Objective:** Verify resume downloads work correctly

**Steps:**
1. After successful resume generation, click "Download PDF"
2. Wait for download to start
3. Open the downloaded PDF file
4. Return to browser and click "Download DOCX"
5. Wait for download and open the DOCX file

**Expected Result:**
- ✓ PDF downloads successfully
- ✓ PDF opens correctly with proper formatting
- ✓ DOCX downloads successfully
- ✓ DOCX opens correctly in Word/LibreOffice
- ✓ Content matches the preview
- ✓ All sections are included

**Failure Indicators:**
- ✗ Download fails or file is corrupt
- ✗ Formatting is broken
- ✗ Content is missing or incomplete

---

### 7. Resume History Test

**Objective:** Verify resume history and re-download functionality

**Steps:**
1. Navigate to "Resume History" page
2. Verify your generated resume appears in the list
3. Click on the resume to view details
4. Test downloading from history

**Expected Result:**
- ✓ All generated resumes are listed
- ✓ Resume details display correctly
- ✓ Download from history works
- ✓ Metadata is accurate (date, job title, company)

---

## Edge Cases to Test

### 8. Invalid Job URL

**Steps:**
1. Enter an invalid LinkedIn URL
2. Try to scrape

**Expected Result:**
- ✓ Validation error appears
- ✓ User-friendly error message
- ✓ No crash or console errors

### 9. Profile Data Refresh

**Steps:**
1. Logout and login again
2. Check if profile data is fresh

**Expected Result:**
- ✓ Profile syncs on login
- ✓ Latest data from LinkedIn appears
- ✓ No manual sync button needed

### 10. Multiple Jobs

**Steps:**
1. Scrape multiple different jobs
2. Generate resumes for each
3. Verify each is tailored differently

**Expected Result:**
- ✓ Each resume is uniquely tailored
- ✓ Skills match job requirements
- ✓ Experience descriptions are relevant

---

## Performance Checks

### 11. Load Times

Monitor and record:
- Dashboard load time: ___ seconds
- Job scraping time: ___ seconds
- Resume generation time: ___ seconds
- Download time: ___ seconds

**Acceptable Ranges:**
- Dashboard: < 2 seconds
- Job scraping: 30-90 seconds (external API)
- Resume generation: 15-45 seconds (AI processing)
- Downloads: < 3 seconds

### 12. Error Handling

Test error scenarios:
- Network disconnection during scraping
- API timeout
- Invalid authentication token
- Backend service down

**Expected Result:**
- ✓ User-friendly error messages
- ✓ No application crash
- ✓ Ability to retry
- ✓ Clear instructions for user

---

## Checklist Summary

- [ ] Dashboard loads without 501 error
- [ ] "Sync Profile" button removed
- [ ] Profile data displays correctly
- [ ] Navigation works between all pages
- [ ] Job scraping completes successfully
- [ ] Job preview displays all information
- [ ] Templates are selectable
- [ ] Resume generation completes
- [ ] Resume content is properly tailored
- [ ] PDF download works
- [ ] DOCX download works
- [ ] Downloaded files are properly formatted
- [ ] Resume history shows all resumes
- [ ] Re-download from history works
- [ ] Error handling is user-friendly
- [ ] No console errors during normal workflow

---

## Troubleshooting

### If Dashboard still shows 501 error:
1. Clear browser cache (Ctrl+F5)
2. Check frontend rebuild: `cd frontend && npm run build`
3. Restart frontend: `npm run dev`
4. Check browser console for specific error

### If job scraping fails:
1. Verify Apify API key in `backend/.env`
2. Check Apify account credits
3. Try a different job URL
4. Check backend logs: `docker logs resumesync-backend`

### If resume generation fails:
1. Verify OpenAI API key in `backend/.env`
2. Check OpenAI account credits
3. Verify profile data exists
4. Check backend logs for AI service errors

### If downloads don't work:
1. Check backend document generation service
2. Verify templates directory exists
3. Check file permissions
4. Try different browser

---

## Success Criteria

The fix is considered successful if:

1. **Primary Issue Resolved**: No 501 profile sync error on Dashboard
2. **Core Workflow Works**: End-to-end from job scraping to download
3. **No Regressions**: All existing features still work
4. **User Experience**: Smooth, intuitive workflow
5. **Error Handling**: Clear messages, no crashes

---

## Test Results

**Tested By:** _______________
**Date:** _______________
**Browser:** _______________
**OS:** _______________

**Overall Status:** ⬜ PASSED  ⬜ FAILED  ⬜ PARTIAL

**Notes:**
```
[Add any observations, issues, or suggestions here]
```

---

## Quick Test Command

For automated endpoint testing, run:
```bash
cd /home/antoine/Documents/dev/ResumeSync
python3 test_ui_workflow.py
```

This will verify:
- Frontend accessibility
- Backend API endpoints
- Dashboard fix implementation
- Available templates
- All core services running
