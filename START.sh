#!/bin/bash

# ResumeSync - Quick Start Script

echo "🚀 Starting ResumeSync..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp backend/.env.example backend/.env
    echo ""
    echo "📝 Please edit backend/.env and add your:"
    echo "   - LINKEDIN_CLIENT_ID"
    echo "   - LINKEDIN_CLIENT_SECRET"
    echo "   - OPENAI_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Start services
echo "🐳 Starting Docker containers..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if backend is ready
echo "🔍 Checking backend health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is ready!"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Run migrations
echo ""
echo "📦 Running database migrations..."
docker compose exec -T backend alembic upgrade head

echo ""
echo "✅ ResumeSync is ready!"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
echo ""
