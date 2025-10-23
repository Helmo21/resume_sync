#!/bin/bash

# ResumeSync - Pre-Push Verification Script
# Run this before pushing to ensure repository is clean and secure

set -e

echo "🔍 ResumeSync Pre-Push Verification"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check and report
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "1. Security Checks"
echo "------------------"

# Check for .env files in git
if git ls-files | grep -q "backend/.env$"; then
    check_fail ".env file is tracked by git! Run: git rm --cached backend/.env"
else
    check_pass "No .env file tracked in git"
fi

# Check for API keys in staged files
if git diff --cached | grep -qi "sk-or-v1-"; then
    check_fail "OpenRouter API key found in staged changes!"
else
    check_pass "No API keys in staged changes"
fi

# Check .env.example for real keys
if grep -q "sk-or-v1-[a-f0-9]" backend/.env.example 2>/dev/null; then
    check_fail "Real API key in .env.example!"
else
    check_pass ".env.example is clean"
fi

echo ""
echo "2. Code Quality Checks"
echo "----------------------"

# Check for __pycache__
if find . -name "__pycache__" -type d | grep -q .; then
    check_warn "__pycache__ directories found (will be ignored by git)"
else
    check_pass "No __pycache__ directories"
fi

# Check for .pyc files
if find . -name "*.pyc" -type f | grep -q .; then
    check_warn ".pyc files found (will be ignored by git)"
else
    check_pass "No .pyc files"
fi

# Check for .pytest_cache
if find . -name ".pytest_cache" -type d | grep -q .; then
    check_warn ".pytest_cache found (will be ignored by git)"
else
    check_pass "No .pytest_cache"
fi

echo ""
echo "3. Documentation Checks"
echo "-----------------------"

# Check for README.md
if [ -f "README.md" ]; then
    check_pass "README.md exists"
else
    check_fail "README.md missing!"
fi

# Check for LICENSE
if [ -f "LICENSE" ]; then
    check_pass "LICENSE exists"
else
    check_warn "LICENSE file missing"
fi

# Check for .gitignore
if [ -f ".gitignore" ]; then
    check_pass ".gitignore exists"
else
    check_fail ".gitignore missing!"
fi

echo ""
echo "4. Structure Checks"
echo "-------------------"

# Check for required directories
[ -d "backend" ] && check_pass "backend/ directory exists" || check_fail "backend/ missing"
[ -d "frontend" ] && check_pass "frontend/ directory exists" || check_fail "frontend/ missing"
[ -d "docs" ] && check_pass "docs/ directory exists" || check_warn "docs/ directory missing"

echo ""
echo "5. Git Status"
echo "-------------"

# Show git status
if git rev-parse --git-dir > /dev/null 2>&1; then
    check_pass "Git repository initialized"

    # Count files to be committed
    STAGED=$(git diff --cached --name-only | wc -l)
    UNSTAGED=$(git diff --name-only | wc -l)
    UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)

    echo "   Staged: $STAGED files"
    echo "   Unstaged: $UNSTAGED files"
    echo "   Untracked: $UNTRACKED files"
else
    check_fail "Not a git repository!"
fi

echo ""
echo "6. Large Files Check"
echo "--------------------"

# Check for files larger than 10MB
LARGE_FILES=$(find . -type f -size +10M ! -path "./.git/*" ! -path "./node_modules/*" 2>/dev/null)
if [ -z "$LARGE_FILES" ]; then
    check_pass "No large files (>10MB) found"
else
    check_warn "Large files found:"
    echo "$LARGE_FILES" | while read file; do
        SIZE=$(du -h "$file" | cut -f1)
        echo "      $SIZE - $file"
    done
fi

echo ""
echo "===================================="
echo "Summary"
echo "===================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Repository is ready to push.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m \"Your commit message\""
    echo "  3. git push origin main"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ ${WARNINGS} warning(s) found. Review them before pushing.${NC}"
    echo ""
    echo "Warnings can usually be ignored if files are in .gitignore"
    exit 0
else
    echo -e "${RED}✗ ${ERRORS} error(s) found. Fix them before pushing!${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Remove .env: git rm --cached backend/.env"
    echo "  - Clean cache: find . -name '__pycache__' -type d -exec rm -rf {} +"
    echo "  - Check staged: git diff --cached"
    exit 1
fi
