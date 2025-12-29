#!/bin/bash

# Portfolio X-Ray - Pre-flight Check
# Verifies all requirements before launching

echo "=================================="
echo "Portfolio X-Ray - Pre-flight Check"
echo "=================================="
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Docker
echo "🔍 Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "   ✅ Docker installed: $DOCKER_VERSION"

    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        echo "   ✅ Docker daemon is running"
    else
        echo "   ❌ Docker daemon is NOT running"
        echo "      → Start Docker Desktop or run: open -a Docker"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "   ❌ Docker NOT found"
    echo "      → Install Docker Desktop from https://www.docker.com/products/docker-desktop"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 2: Docker Compose
echo "🔍 Checking Docker Compose..."
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version 2>/dev/null || docker compose version 2>/dev/null)
    echo "   ✅ Docker Compose available: $COMPOSE_VERSION"
else
    echo "   ❌ Docker Compose NOT found"
    echo "      → Included with Docker Desktop, or install separately"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 3: Environment file
echo "🔍 Checking .env file..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"

    # Check for Gemini API key
    if grep -q "GEMINI_API_KEY=your_gemini" .env; then
        echo "   ⚠️  Gemini API key not configured (AI insights will not work)"
        echo "      → Add your API key to .env if you want AI insights"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "   ✅ Gemini API key configured"
    fi
else
    echo "   ⚠️  .env file NOT found"
    echo "      → Creating from .env.example..."

    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ Created .env from template"
        echo "      → Edit .env to add your Gemini API key (optional)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "   ❌ .env.example also missing"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# Check 4: Port availability
echo "🔍 Checking port availability..."

check_port() {
    PORT=$1
    SERVICE=$2
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   ⚠️  Port $PORT is already in use (needed for $SERVICE)"
        echo "      → Stop the process using: lsof -ti:$PORT | xargs kill -9"
        echo "      → Or change port in docker-compose.yml"
        WARNINGS=$((WARNINGS + 1))
        return 1
    else
        echo "   ✅ Port $PORT is available ($SERVICE)"
        return 0
    fi
}

check_port 5432 "PostgreSQL"
check_port 8000 "Backend API"
check_port 5173 "Frontend"
echo ""

# Check 5: Disk space
echo "🔍 Checking disk space..."
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
echo "   ℹ️  Available disk space: $AVAILABLE"
echo "      (Needs ~3GB for Docker images + dependencies)"
echo ""

# Check 6: Docker Compose config
echo "🔍 Validating docker-compose.yml..."
if docker-compose config > /dev/null 2>&1; then
    echo "   ✅ docker-compose.yml is valid"
else
    echo "   ❌ docker-compose.yml has errors"
    echo "      → Run: docker-compose config"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 7: Required directories
echo "🔍 Checking project structure..."
REQUIRED_DIRS=("backend" "frontend" "inputs")
for DIR in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$DIR" ]; then
        echo "   ✅ $DIR/ directory exists"
    else
        echo "   ❌ $DIR/ directory missing"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check 8: CSV input files
echo "🔍 Checking input CSV files..."
if [ -d "inputs" ]; then
    CSV_COUNT=$(find inputs -name "*.csv" | wc -l | tr -d ' ')
    if [ "$CSV_COUNT" -gt 0 ]; then
        echo "   ✅ Found $CSV_COUNT CSV file(s) in inputs/"
        find inputs -name "*.csv" -exec basename {} \; | while read file; do
            echo "      - $file"
        done
    else
        echo "   ⚠️  No CSV files in inputs/ directory"
        echo "      → Add your Rakuten Securities CSV files to inputs/"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# Summary
echo "=================================="
echo "Summary"
echo "=================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Ready to launch."
    echo ""
    echo "Next steps:"
    echo "  1. docker-compose up --build"
    echo "  2. Open http://localhost:5173"
    echo "  3. Upload your CSV files"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  $WARNINGS warning(s) - you can proceed but some features may not work"
    echo ""
    echo "Ready to launch:"
    echo "  docker-compose up --build"
    echo ""
    exit 0
else
    echo "❌ $ERRORS error(s) and $WARNINGS warning(s) found"
    echo ""
    echo "Please fix the errors above before launching."
    echo ""
    exit 1
fi
