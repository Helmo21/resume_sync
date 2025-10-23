# ResumeSync

<div align="center">

**AI-Powered Resume Generator for Job Applications**

Transform your LinkedIn profile into ATS-optimized, tailored resumes for any job posting.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## Overview

ResumeSync uses a sophisticated **multi-agent AI architecture** to create tailored, professional resumes from your LinkedIn profile matched to specific job postings. The system intelligently analyzes, matches, and generates ATS-optimized resumes while maintaining the integrity of your actual experience.

### Key Principle
Your actual LinkedIn profile is the foundation. The AI rewrites your experiences to emphasize job-relevant aspects **without fabricating information**.

---

## Features

### Core Capabilities
- **LinkedIn OAuth Integration** - One-time authentication and profile sync
- **Intelligent Job Scraping** - Extract requirements from any job URL (LinkedIn, Indeed, etc.)
- **Multi-Agent AI System** - 5 specialized agents for professional resume generation
- **ATS Optimization** - Keyword matching and formatting for Applicant Tracking Systems
- **Multiple Formats** - Export as PDF or DOCX
- **Resume History** - Access and download all previously generated resumes
- **Professional Templates** - Multiple customizable resume templates

### Multi-Agent Architecture
1. **ProfileAnalyzer** - Extracts strengths and competencies from LinkedIn data
2. **JobAnalyzer** - Identifies requirements and ATS keywords from job postings
3. **MatchMaker** - Calculates relevance scores and selects best-fit experiences
4. **ContentWriter** - Generates tailored content while maintaining integrity
5. **Reviewer** - Validates quality, coherence, and 1-page constraint

See `docs/MULTIAGENT_IMPLEMENTATION.md` for complete technical details.

---

## Architecture

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | FastAPI | Python 3.10+ |
| Frontend | React + Vite | React 18 |
| Database | PostgreSQL | 15 |
| Cache | Redis | 7 |
| AI Engine | OpenRouter API | Claude 3.5 Sonnet |
| Infrastructure | Docker Compose | v2 |
| Styling | Tailwind CSS | 3.x |

### System Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │ ───> │   FastAPI    │ ───> │ PostgreSQL  │
│  Frontend   │ <─── │   Backend    │ <─── │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├──> Redis Cache
                            │
                            ├──> OpenRouter AI (Multi-Agent)
                            │
                            └──> Apify Job Scraper
```

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose v2** installed
- **LinkedIn Developer App** credentials ([Create one here](https://www.linkedin.com/developers/))
- **OpenRouter API** key ([Get it here](https://openrouter.ai/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ResumeSync.git
   cd ResumeSync
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```

   Edit `backend/.env` with your credentials:
   ```bash
   # LinkedIn OAuth
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

   # OpenRouter AI
   OPENROUTER_API_KEY=sk-or-v1-your_key_here
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

   # JWT Secret (generate with: openssl rand -hex 32)
   SECRET_KEY=your_generated_secret_key
   ```

3. **Start the application**
   ```bash
   ./START.sh
   ```

   Or manually:
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

---

## Usage

### Basic Workflow

1. **Authenticate with LinkedIn**
   - Click "Sign in with LinkedIn"
   - Your profile is scraped and stored (one-time process)

2. **Generate a Resume**
   - Enter a job posting URL
   - Select a resume template
   - Click "Generate Resume"
   - AI processes in ~30-55 seconds

3. **Download & Use**
   - Download as PDF or DOCX
   - Review AI-generated content
   - Apply to the job with confidence

4. **Access History**
   - View all previously generated resumes
   - Re-download or regenerate as needed

### How It Works

```
LinkedIn Profile (Stored) + Job URL
         ↓
    Job Scraping (Apify)
         ↓
   Multi-Agent AI System
    ├─ ProfileAnalyzer
    ├─ JobAnalyzer
    ├─ MatchMaker
    ├─ ContentWriter
    └─ Reviewer
         ↓
  Tailored Resume JSON
         ↓
  PDF/DOCX Generation
         ↓
    Download Ready!
```

---

## Development

### Project Structure

```
ResumeSync/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   │   ├── auth.py        # LinkedIn OAuth & JWT
│   │   │   ├── profile.py     # Profile management
│   │   │   ├── jobs.py        # Job scraping
│   │   │   └── resumes.py     # Resume generation
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Settings
│   │   │   ├── database.py    # SQLAlchemy setup
│   │   │   └── security.py    # JWT & auth
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── job.py
│   │   │   └── resume.py
│   │   ├── services/          # Business logic
│   │   │   ├── ai_resume_agent.py      # Multi-agent system
│   │   │   ├── cv_generator.py         # Resume orchestrator
│   │   │   ├── document_generator.py   # PDF/DOCX creation
│   │   │   ├── apify_scraper.py        # Job scraping
│   │   │   ├── template_handler.py     # Template processing
│   │   │   └── template_matcher.py     # Template selection
│   │   └── main.py            # FastAPI app entry
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite
│   ├── legacy/                # Legacy MVP scripts (reference)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable UI components
│   │   ├── services/         # API client
│   │   ├── hooks/            # React hooks (useAuth)
│   │   └── main.jsx          # React entry
│   └── package.json
├── teamplate/                # DOCX resume templates
├── docs/                     # Documentation
├── archive_docs/             # Historical documentation
├── docker-compose.yml        # Service orchestration
├── START.sh                  # Startup script
└── README.md
```

### Common Development Commands

```bash
# Start all services
./START.sh

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart a service
docker compose restart backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Access PostgreSQL database
docker compose exec db psql -U resumesync -d resumesync

# Run tests
docker compose exec backend pytest

# Run specific tests
docker compose exec backend pytest tests/test_auth.py -v

# Stop all services
docker compose down

# Reset everything (including data)
docker compose down -v
```

### Testing

The project includes a comprehensive test suite with markers:

```bash
# Run all tests
docker compose exec backend pytest

# Run by marker
docker compose exec backend pytest -m unit        # Unit tests only
docker compose exec backend pytest -m integration # Integration tests
docker compose exec backend pytest -m "not slow"  # Skip slow tests

# Available markers: unit, integration, e2e, slow, ai, mock
```

See `docs/TESTING_GUIDE.md` for comprehensive testing documentation.

---

## Configuration

### Environment Variables

All configuration is done via `backend/.env`:

```bash
# Database (auto-configured for Docker)
DATABASE_URL=postgresql://resumesync:resumesync@db:5432/resumesync
DATABASE_URL_ASYNC=postgresql+asyncpg://resumesync:resumesync@db:5432/resumesync

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/auth/linkedin/callback

# Apify (Job Scraping)
APIFY_API_TOKEN=your_apify_token  # Optional, has fallback scraper

# OpenRouter AI
OPENROUTER_API_KEY=sk-or-v1-your_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# AWS S3 (Optional - for production PDF storage)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=resumesync-pdfs

# Frontend
FRONTEND_URL=http://localhost:5173

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development
```

### AI Model Selection

ResumeSync uses OpenRouter to access 100+ AI models. Recommended options:

| Model | Cost per Resume | Quality | Use Case |
|-------|----------------|---------|----------|
| `openai/gpt-4o-mini` | ~$0.001 | Good | Development/Testing |
| `anthropic/claude-3.5-sonnet` | ~$0.05-0.15 | Excellent | Production (Default) |
| `openai/gpt-4-turbo` | ~$0.05 | Excellent | Premium quality |

Change in `backend/.env`:
```bash
OPENROUTER_MODEL=openai/gpt-4o-mini
```

---

## Troubleshooting

### Frontend Issues

**Blank page or errors:**
```bash
# Check logs
docker compose logs frontend --tail 50

# Common fix: Rebuild frontend
docker compose up --build -d frontend

# Check browser console (F12) for errors
```

### Backend Issues

**API not responding:**
```bash
# Check logs
docker compose logs backend --tail 50

# Restart backend
docker compose restart backend

# Check health endpoint
curl http://localhost:8000/health
```

### Database Issues

**Connection errors:**
```bash
# Check if PostgreSQL is running
docker compose ps

# Restart database
docker compose restart db

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
```

### Authentication Issues

**LinkedIn OAuth fails:**
- Verify credentials in `backend/.env`
- Ensure redirect URI matches: `http://localhost:8000/api/auth/linkedin/callback`
- Check LinkedIn Developer Console for app settings
- Verify app has correct OAuth permissions

**JWT token errors:**
- Generate new `SECRET_KEY`: `openssl rand -hex 32`
- Clear browser cookies/localStorage
- Check token expiration settings

### AI Generation Issues

**OpenRouter API errors:**
- Check API key in `backend/.env`
- Visit https://openrouter.ai/activity for usage
- Verify account has sufficient credits
- Check model name is correct

**Multi-agent generation failing:**
- Check backend logs for specific agent errors
- System automatically falls back to legacy generation
- Verify OpenRouter model supports required context length

---

## API Documentation

Full interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/linkedin` | GET | Initiate LinkedIn OAuth |
| `/api/auth/linkedin/callback` | GET | LinkedIn OAuth callback |
| `/api/profile/sync` | POST | Sync LinkedIn profile |
| `/api/jobs/scrape` | POST | Scrape job posting |
| `/api/resumes/generate` | POST | Generate tailored resume |
| `/api/resumes/` | GET | List user's resumes |
| `/api/resumes/{id}/download` | GET | Download resume file |

---

## Security Considerations

- Never commit `.env` files (already in `.gitignore`)
- Generate strong `SECRET_KEY` for production: `openssl rand -hex 32`
- LinkedIn tokens are stored in database (encrypt in production)
- Use HTTPS in production
- Review CORS settings before deploying
- Rotate API keys regularly
- Use environment-specific configurations

---

## Production Deployment

### Recommended Stack
- **Hosting**: AWS EC2, DigitalOcean, or similar
- **Database**: AWS RDS PostgreSQL or managed PostgreSQL
- **Storage**: AWS S3 for resume files
- **CDN**: CloudFront for static assets
- **Domain**: Custom domain with SSL (Let's Encrypt)

### Deployment Checklist
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database URL
- [ ] Set up AWS S3 for file storage
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Review security headers
- [ ] Set up CI/CD pipeline

---

## Documentation

Additional documentation available in `docs/`:

- `MULTIAGENT_IMPLEMENTATION.md` - Multi-agent system architecture
- `TESTING_GUIDE.md` - Comprehensive testing guide
- `TEMPLATE_GUIDE.md` - Resume template customization
- `USAGE_GUIDE.md` - Detailed usage instructions
- `QUICK_START.md` - Quick start guide

Historical documentation in `archive_docs/` for reference.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use functional React components with hooks (no class components)
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/ResumeSync/issues)
- **Documentation**: Check `docs/` directory
- **Logs**: `docker compose logs [service]`
- **API Docs**: http://localhost:8000/docs

---

## Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - UI library
- **OpenRouter** - AI model access
- **LangChain** - Multi-agent framework
- **Apify** - Web scraping infrastructure
- **Docker** - Containerization platform

---

<div align="center">

**Built with**: FastAPI • React • PostgreSQL • Docker • OpenRouter AI • LangChain

Made with ❤️ for job seekers everywhere

</div>
