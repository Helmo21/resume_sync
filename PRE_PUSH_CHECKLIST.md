# Pre-Push Checklist

**IMPORTANT**: Complete this checklist before pushing to your repository.

## Security Check

- [ ] **No `.env` files committed** - Only `.env.example` should be in the repo
  ```bash
  # Verify:
  git ls-files | grep "\.env$"
  # Should return nothing (only .env.example is OK)
  ```

- [ ] **No API keys in code** - Check all files for exposed secrets
  ```bash
  # Search for common patterns:
  grep -r "sk-or-v1-" . --exclude-dir={node_modules,.git,archive_docs}
  grep -r "OPENROUTER_API_KEY=" . --exclude-dir={node_modules,.git}
  ```

- [ ] **backend/.env.example cleaned** - No real API keys in example file
  ```bash
  # Verify:
  cat backend/.env.example | grep "sk-or-v1-"
  # Should return placeholder, not real key
  ```

## Code Quality

- [ ] **No Python cache files** - `__pycache__` directories removed
  ```bash
  find . -name "__pycache__" -type d
  # Should return nothing
  ```

- [ ] **No compiled Python files** - `.pyc` files removed
  ```bash
  find . -name "*.pyc"
  # Should return nothing
  ```

- [ ] **No test cache** - `.pytest_cache` removed
  ```bash
  find . -name ".pytest_cache" -type d
  # Should return nothing
  ```

- [ ] **Git ignore updated** - `.gitignore` covers all sensitive/temp files

## Documentation

- [ ] **README.md complete** - Professional and comprehensive
- [ ] **LICENSE file present** - MIT license included
- [ ] **CONTRIBUTING.md present** - Contribution guidelines clear
- [ ] **CLAUDE.md updated** - Project instructions current
- [ ] **docs/ organized** - All documentation in proper location

## Docker Configuration

- [ ] **docker-compose.yml clean** - No hardcoded secrets
- [ ] **Dockerfile optimized** - Multi-stage if possible
- [ ] **.dockerignore present** - Excludes unnecessary files

## Repository Structure

```
Expected structure:
ResumeSync/
├── backend/              ✓ FastAPI backend
│   ├── app/             ✓ Application code
│   ├── alembic/         ✓ Migrations
│   ├── tests/           ✓ Test suite
│   └── .env.example     ✓ Example config (NO REAL KEYS)
├── frontend/            ✓ React frontend
├── teamplate/           ✓ Resume templates
├── docs/                ✓ Documentation
├── archive_docs/        ✓ Historical docs
├── .claude/             ✓ Claude Code config (optional)
├── README.md            ✓ Main documentation
├── LICENSE              ✓ MIT License
├── CONTRIBUTING.md      ✓ Contribution guide
├── CLAUDE.md            ✓ AI instructions
├── docker-compose.yml   ✓ Docker config
├── START.sh             ✓ Startup script
└── .gitignore           ✓ Ignore rules
```

## Files to Remove Before Push

Run these commands to ensure clean repository:

```bash
# Remove all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove all .pyc files
find . -type f -name "*.pyc" -delete

# Remove pytest cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Remove any .env files (keep .env.example)
find . -type f -name ".env" ! -name ".env.example" -delete

# Verify git status
git status
```

## Optional: Clean Git History

If you accidentally committed sensitive data:

```bash
# DANGER: This rewrites history!
# Only use if you haven't pushed yet or repo is private

# Remove file from all history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if safe to do so)
git push origin --force --all
```

## Final Verification

Before pushing, run:

```bash
# 1. Check what will be committed
git status

# 2. Review changes
git diff

# 3. Check for secrets
git diff | grep -i "api_key\|secret\|password\|token"

# 4. Verify .gitignore is working
git check-ignore backend/.env
# Should output: backend/.env

# 5. Check for large files
find . -type f -size +10M ! -path "./.git/*" ! -path "./node_modules/*"
```

## Git Commands for Clean Push

```bash
# 1. Add files (review what's being added!)
git add .

# 2. Check staged files
git diff --cached --name-only

# 3. Commit with clear message
git commit -m "Initial commit: ResumeSync AI-powered resume generator"

# 4. Create repository on GitHub/GitLab (don't push yet!)

# 5. Add remote
git remote add origin https://github.com/yourusername/ResumeSync.git

# 6. Push to main branch
git push -u origin main
```

## Post-Push Verification

After pushing:

- [ ] Visit repository on GitHub
- [ ] Check no `.env` files visible
- [ ] Verify README displays correctly
- [ ] Check file structure is clean
- [ ] Test clone on another machine
- [ ] Verify Docker setup works from fresh clone

## Environment Variables Setup (For Users)

Remember to document that users need to:

1. Copy `.env.example` to `.env`
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Fill in their own credentials:
   - `LINKEDIN_CLIENT_ID`
   - `LINKEDIN_CLIENT_SECRET`
   - `OPENROUTER_API_KEY`
   - `SECRET_KEY` (generate with: `openssl rand -hex 32`)

## Checklist Complete?

Once all items are checked:

```bash
# Create a clean commit
git add .
git commit -m "Clean repository for production push"

# Push to your private repository
git push origin main
```

---

**Remember**: Never commit:
- `.env` files with real credentials
- `__pycache__/` directories
- `node_modules/` directories
- API keys or secrets
- Large binary files (unless necessary)
- Personal data or test data with PII

**Good luck with your repository! 🚀**
