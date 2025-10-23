# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ResumeSync is an AI-powered resume generator that creates tailored resumes from LinkedIn profiles matched to specific job postings. The system uses a sophisticated **multi-agent AI architecture** with LangChain to intelligently analyze, match, and generate ATS-optimized resumes.

**Key principle**: Your actual LinkedIn profile is the foundation - the AI rewrites experiences to emphasize job-relevant aspects without fabricating information.

## Architecture

**Stack**:
- Backend: FastAPI (Python 3.10+) with async SQLAlchemy
- Frontend: React 18 + Vite + Tailwind CSS
- Database: PostgreSQL 15
- Cache: Redis 7
- AI: OpenRouter API (Claude 3.5 Sonnet via LangChain multi-agent system)
- Infrastructure: Docker Compose

**Multi-Agent System** (5 specialized agents):
1. ProfileAnalyzer - Extracts strengths and competencies from LinkedIn data
2. JobAnalyzer - Identifies requirements and ATS keywords from job postings
3. MatchMaker - Calculates relevance scores and selects best-fit experiences
4. ContentWriter - Generates tailored content while maintaining integrity
5. Reviewer - Validates quality, coherence, and 1-page constraint

See `backend/MULTIAGENT_IMPLEMENTATION.md` for complete details.

## Development Commands

### Start/Stop
```bash
# Start all services (recommended)
./START.sh

# OR manually
docker compose up -d

# Stop everything
docker compose down

# Reset everything including data
docker compose down -v
```

### Logs & Debugging
```bash
# View logs (use -f to follow)
docker compose logs -f backend
docker compose logs -f frontend

# Restart a service
docker compose restart backend

# Check health
curl http://localhost:8000/health
```

### Database
```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "description"

# Access database
docker compose exec db psql -U resumesync -d resumesync
```

### Testing
```bash
# Run all tests
docker compose exec backend pytest

# Run specific test file
docker compose exec backend pytest tests/test_auth.py

# Run with markers
docker compose exec backend pytest -m unit
docker compose exec backend pytest -m "not slow"

# Available markers: unit, integration, e2e, slow, ai, mock
```

**Slash commands**:
- `/test-fix` - Automated test/fix cycle until all tests pass
- `/autofix [description]` - Implement feature with automated test/fix loop

## Code Patterns & Conventions

### Backend (Python)

**Style**:
- Python 3.10+ with type hints
- PEP 8 style guide
- async/await for database operations
- Import order: stdlib → third-party → local (blank line separated)

**Adding API Endpoints**:
1. Create endpoint in `backend/app/api/[module].py`
2. Register router in `backend/app/main.py`
3. Add API client method in `frontend/src/services/api.js`

Example endpoint:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User

router = APIRouter()

@router.get("/endpoint")
async def get_data(
    user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Endpoint description with return type documented."""
    try:
        # Logic here
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Database Migrations Workflow**:
1. Modify models in `backend/app/models/`
2. Generate migration: `docker compose exec backend alembic revision --autogenerate -m "description"`
3. Review generated file in `backend/alembic/versions/`
4. Apply migration: `docker compose exec backend alembic upgrade head`
5. Commit both model change and migration file

### Frontend (React)

**Style**:
- Functional components with hooks only (no class components)
- Arrow functions for components
- File naming: PascalCase for components (e.g., `LoginPage.jsx`)
- React files with JSX: `.jsx` extension (not `.js`)
- API calls: Always in `services/api.js`, never directly in components

**File Extensions**:
- Components with JSX: `.jsx`
- Pure logic hooks: `.js`
- Backend Python: `.py`

## Critical Rules

### Never Do This
1. **Never use OpenAI API directly** - Use OpenRouter (configured in `.env`)
2. **Never scrape LinkedIn on every resume generation** - Profile stored in DB after OAuth
3. **Never hardcode API keys** - Always use environment variables
4. **Never commit `.env` files** - They're in `.gitignore`
5. **Never use `docker-compose` (v1)** - Use `docker compose` (v2)
6. **Never create class-based React components** - Use functional components only
7. **Never skip database migrations** - Use Alembic for schema changes
8. **Never fabricate profile data** - Multi-agent system maintains integrity (no false years of experience, invented skills, or fake companies)

### Always Do This
1. Use Docker Compose for all development
2. Check logs before assuming something works
3. Run migrations after model changes
4. Use JWT authentication for protected endpoints
5. Return structured JSON from all API endpoints
6. Handle errors gracefully with proper HTTP status codes
7. Use multi-agent system for resume generation (default in `CVGenerator`)

## Resume Generation Flow

**Critical - Never break this flow**:
```
1. User authenticated via JWT
2. Get LinkedIn profile from DB (NOT from LinkedIn API)
3. Scrape job posting from URL (via Apify or fallback scraper)
4. Pass both to multi-agent AI system:
   - ProfileAnalyzer extracts competencies
   - JobAnalyzer identifies requirements
   - MatchMaker selects relevant experiences (always includes latest)
   - ContentWriter generates tailored content
   - Reviewer validates quality and 1-page constraint
5. Generate resume JSON with match score
6. Create PDF/DOCX with selected template
7. Save to database
8. Return download URL
```

## AI Configuration

**OpenRouter with LangChain**:
- Base URL: `https://openrouter.ai/api/v1`
- API Key: `OPENROUTER_API_KEY` in `backend/.env`
- Default Model: `anthropic/claude-3.5-sonnet`
- Cost per resume: ~$0.05-0.15
- Generation time: ~30-55 seconds

**Multi-Agent System**:
- Implementation: `backend/app/services/ai_resume_agent.py`
- Integration: `backend/app/services/cv_generator.py` (use_multi_agent=True by default)
- Fallback: Automatically uses legacy single-prompt if multi-agent fails
- Enhancement rules: Can enhance descriptions (e.g., "Expert in React") but never fabricate experiences or years

**Change Model**:
```bash
# In backend/.env
OPENROUTER_MODEL=openai/gpt-4o-mini  # Cheapest ($0.001/resume)
# OR
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Best quality ($0.02/resume)
```

## Directory Structure

```
ResumeSync/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (auth, profile, resumes, jobs)
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── services/     # Business logic
│   │   │   ├── ai_resume_agent.py      # Multi-agent system
│   │   │   ├── cv_generator.py         # Resume generation orchestrator
│   │   │   ├── document_generator.py   # PDF/DOCX creation
│   │   │   ├── apify_scraper.py        # Job scraping
│   │   │   ├── template_handler.py     # Template processing
│   │   │   └── template_matcher.py     # Template selection
│   │   └── main.py       # FastAPI app entry
│   ├── alembic/          # Database migrations
│   ├── tests/            # Pytest tests with fixtures
│   ├── legacy/           # Legacy MVP scripts (mounted from root)
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env              # Environment variables (NOT in git)
├── frontend/
│   ├── src/
│   │   ├── pages/        # Page components (.jsx)
│   │   ├── components/   # Reusable components
│   │   ├── services/     # API client (api.js)
│   │   ├── hooks/        # React hooks (useAuth.jsx)
│   │   └── main.jsx      # React entry
│   └── package.json
├── teamplate/            # DOCX resume templates
├── docker-compose.yml
├── START.sh              # Startup script
├── .cursorrules          # Cursor AI rules (reference for best practices)
└── *.md                  # Documentation
```

## Environment Variables

Required in `backend/.env`:
```bash
# Authentication
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/auth/linkedin/callback
SECRET_KEY=your_jwt_secret  # Generate: openssl rand -hex 32

# AI Model
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Database (auto-configured in Docker)
DATABASE_URL=postgresql://resumesync:resumesync@db:5432/resumesync
DATABASE_URL_ASYNC=postgresql+asyncpg://resumesync:resumesync@db:5432/resumesync

# Frontend
FRONTEND_URL=http://localhost:5173
```

## Testing Strategy

**Pytest Configuration** (`backend/pytest.ini`):
- Test markers: unit, integration, e2e, slow, ai, mock
- Coverage tracking enabled
- Verbose output with short tracebacks

**Test Organization**:
- `tests/conftest.py` - Shared fixtures (database, test client, mock data)
- `tests/fixtures/` - Test data fixtures
- `tests/test_*.py` - Test modules

**Debugging Checklist**:
```bash
# Backend not responding?
docker compose logs backend

# Frontend blank page?
docker compose logs frontend
# Check browser console (F12)

# Database connection error?
docker compose ps  # Check if db is healthy

# OpenRouter API error?
# Check https://openrouter.ai/activity
# Verify OPENROUTER_API_KEY in backend/.env

# Multi-agent generation failing?
# Check backend logs for specific agent errors
# System will fallback to legacy generation
```

## Known Issues & Workarounds

1. **LinkedIn OAuth**: Requires real LinkedIn Developer App credentials
2. **Job Scraping**: Some sites block bots - uses Apify with fallback to BeautifulSoup
3. **Docker Volumes**: If node_modules issues, rebuild: `docker compose up --build -d`
4. **Port Conflicts**: If ports 8000/5173/5432 in use, change in `docker-compose.yml`
5. **Reviewer Agent**: Can be overly strict, may need tuning in production

## Access Points

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432 (user: resumesync, db: resumesync)
- Redis: localhost:6379

## Legacy Files

Root-level `*.py` files are legacy MVP scripts, mounted to `/app/legacy/` in backend container:
- `job_scraper.py` - Job posting scraper
- `linkedin_scraper_final.py` - LinkedIn profile scraper
- `openai_generator.py` - AI resume generator (replaced by multi-agent)
- `pdf_generator.py` - PDF/DOCX creator

**These are for reference only** - active implementation is in `backend/app/services/`.
