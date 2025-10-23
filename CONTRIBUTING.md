# Contributing to ResumeSync

Thank you for considering contributing to ResumeSync! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:
- A clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Docker version, etc.)
- Relevant logs (use `docker compose logs [service]`)

### Suggesting Features

We welcome feature suggestions! Please create an issue with:
- A clear description of the feature
- Use case and benefits
- Any implementation ideas (optional)

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/ResumeSync.git
   cd ResumeSync
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines below
   - Write or update tests as needed
   - Update documentation if needed

4. **Test your changes**
   ```bash
   docker compose exec backend pytest
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of your changes
   - Reference any related issues
   - Wait for review and address feedback

## Code Style Guidelines

### Python (Backend)

- Follow **PEP 8** style guide
- Use Python 3.10+ features and type hints
- Use `async/await` for database operations
- Import order: stdlib → third-party → local (separated by blank lines)

Example:
```python
from typing import Optional
import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
```

### JavaScript/React (Frontend)

- Use **functional components** with hooks only (no class components)
- Use **arrow functions** for components
- File naming: **PascalCase** for components (e.g., `LoginPage.jsx`)
- React files with JSX must have `.jsx` extension
- API calls go in `services/api.js`, never directly in components

Example:
```jsx
import { useState, useEffect } from 'react';
import api from '../services/api';

const MyComponent = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const result = await api.getData();
      setData(result);
    };
    fetchData();
  }, []);

  return <div>{data?.name}</div>;
};

export default MyComponent;
```

## Development Workflow

### Setting Up Development Environment

1. **Install dependencies**
   ```bash
   ./START.sh
   ```

2. **Access services**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. **View logs**
   ```bash
   docker compose logs -f backend
   docker compose logs -f frontend
   ```

### Database Changes

1. **Modify models** in `backend/app/models/`

2. **Generate migration**
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "description"
   ```

3. **Review migration** in `backend/alembic/versions/`

4. **Apply migration**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

5. **Commit both** model change and migration file

### Adding API Endpoints

1. **Create endpoint** in `backend/app/api/[module].py`
2. **Register router** in `backend/app/main.py`
3. **Add API client method** in `frontend/src/services/api.js`
4. **Write tests** in `backend/tests/`

## Testing

### Running Tests

```bash
# All tests
docker compose exec backend pytest

# Specific file
docker compose exec backend pytest tests/test_auth.py -v

# By marker
docker compose exec backend pytest -m unit
docker compose exec backend pytest -m integration
docker compose exec backend pytest -m "not slow"
```

### Test Markers

- `unit` - Unit tests
- `integration` - Integration tests
- `e2e` - End-to-end tests
- `slow` - Slow-running tests
- `ai` - Tests that use AI models
- `mock` - Tests with mocked dependencies

### Writing Tests

- Place tests in `backend/tests/`
- Use fixtures from `conftest.py`
- Mock external APIs (OpenRouter, Apify, etc.)
- Test both success and error cases

Example:
```python
import pytest
from app.services.cv_generator import CVGenerator

@pytest.mark.unit
def test_generate_resume(mock_profile, mock_job):
    generator = CVGenerator()
    result = generator.generate(mock_profile, mock_job)
    assert result["match_score"] > 0
```

## Critical Rules

### Never Do This
1. Never use OpenAI API directly - use OpenRouter
2. Never scrape LinkedIn on every resume generation
3. Never hardcode API keys
4. Never commit `.env` files
5. Never use `docker-compose` (v1) - use `docker compose` (v2)
6. Never create class-based React components
7. Never skip database migrations
8. Never fabricate profile data in AI prompts

### Always Do This
1. Use Docker Compose for development
2. Check logs before assuming something works
3. Run migrations after model changes
4. Use JWT authentication for protected endpoints
5. Handle errors with proper HTTP status codes
6. Return structured JSON from API endpoints
7. Use the multi-agent system for resume generation

## Documentation

- Update `README.md` if adding major features
- Document API endpoints in docstrings
- Add comments for complex logic
- Update `docs/` folder for technical details
- Keep `CLAUDE.md` updated for AI assistance context

## Questions?

- Check existing issues and documentation
- Ask in Pull Request comments
- Create a discussion issue for general questions

Thank you for contributing to ResumeSync!
