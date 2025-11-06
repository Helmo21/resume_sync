#!/bin/bash
# Deploy LinkedIn Job Scraper V2 Integration
# This script rebuilds and deploys all new services

set -e  # Exit on error

echo "========================================="
echo "🚀 LinkedIn Job Scraper V2 - Deployment"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Pre-flight: Check .env file
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ ERROR: backend/.env file not found!${NC}"
    echo ""
    echo "Please create backend/.env from backend/.env.example:"
    echo "  cp backend/.env.example backend/.env"
    echo ""
    echo "Then edit backend/.env and add:"
    echo "  1. OPENROUTER_API_KEY (required for AI matching)"
    echo "  2. LINKEDIN_SERVICE_ACCOUNTS (required for job scraping)"
    echo ""
    exit 1
fi

# Check if LinkedIn accounts are configured
if grep -q "scraper1@example.com" backend/.env; then
    echo -e "${YELLOW}⚠️  WARNING: LinkedIn service accounts not configured!${NC}"
    echo ""
    echo "Please edit backend/.env and replace:"
    echo "  LINKEDIN_SERVICE_ACCOUNTS=\"scraper1@example.com:Password123!|...\""
    echo ""
    echo "With your actual LinkedIn scraping accounts."
    echo "DO NOT use your personal LinkedIn account!"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Step 1: Stop existing containers
echo -e "${YELLOW}Step 1/5: Stopping existing containers...${NC}"
docker compose down
echo -e "${GREEN}✅ Containers stopped${NC}"
echo ""

# Step 2: Rebuild images
echo -e "${YELLOW}Step 2/5: Rebuilding Docker images (this may take 5-10 minutes)...${NC}"
docker compose build
echo -e "${GREEN}✅ Images rebuilt${NC}"
echo ""

# Step 3: Start services
echo -e "${YELLOW}Step 3/5: Starting all services...${NC}"
docker compose up -d
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 4: Wait for services to be healthy
echo -e "${YELLOW}Step 4/5: Waiting for services to be healthy...${NC}"
sleep 10

# Check if database is up
if docker compose exec -T db pg_isready -U resumesync &> /dev/null; then
    echo -e "${GREEN}✅ Database is ready${NC}"
else
    echo -e "${RED}❌ Database is not responding${NC}"
    exit 1
fi

# Check if Redis is up
if docker compose exec -T redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
    exit 1
fi

echo ""

# Step 5: Run database migration
echo -e "${YELLOW}Step 5/5: Running database migration...${NC}"
docker compose exec -T backend alembic upgrade head
echo -e "${GREEN}✅ Migration complete${NC}"
echo ""

# Verify Celery worker
echo "🔍 Verifying Celery worker..."
if docker compose ps celery_worker | grep -q "Up"; then
    echo -e "${GREEN}✅ Celery worker is running${NC}"
else
    echo -e "${RED}⚠️  Celery worker may not be running${NC}"
fi
echo ""

# Summary
echo "========================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Services running:"
echo "  - Backend API:      http://localhost:8000"
echo "  - API Docs:         http://localhost:8000/docs"
echo "  - Frontend:         http://localhost:5173"
echo "  - PostgreSQL:       localhost:5432"
echo "  - Redis:            localhost:6379"
echo ""
echo "📋 Check logs:"
echo "  docker compose logs backend -f"
echo "  docker compose logs celery_worker -f"
echo ""
echo "🔍 View loaded service accounts:"
echo "  docker compose logs backend | grep 'Loaded service account'"
echo ""
echo "📖 Full documentation: INTEGRATION_COMPLETE.md"
echo ""
echo -e "${GREEN}✅ LinkedIn service accounts loaded from .env automatically!${NC}"
echo ""
