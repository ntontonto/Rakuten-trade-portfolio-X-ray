# Portfolio X-Ray - Startup Guide

Complete guide to launch the full-stack application using Docker Compose.

---

## Prerequisites

**Required:**
- ✅ Docker Desktop (includes Docker Compose)
- ✅ Git

**Optional:**
- Google Gemini API key (for AI insights feature)

---

## Quick Start (3 Steps)

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if you want AI insights (optional)
# Add your GEMINI_API_KEY=your_actual_key_here
```

### Step 2: Launch Services

```bash
# Start all services (database, backend, frontend)
docker-compose up --build

# OR run in background (detached mode)
docker-compose up -d --build
```

### Step 3: Access Application

Once services are running:

- **Frontend (React App)**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

---

## Service Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                      │
│         React + TypeScript + Vite               │
│            http://localhost:5173                │
└──────────────────┬──────────────────────────────┘
                   │ API calls
                   ↓
┌─────────────────────────────────────────────────┐
│                   Backend                       │
│         FastAPI + Python 3.11                   │
│            http://localhost:8000                │
└──────────────────┬──────────────────────────────┘
                   │ SQL queries
                   ↓
┌─────────────────────────────────────────────────┐
│                  Database                       │
│            PostgreSQL 15                        │
│            localhost:5432                       │
└─────────────────────────────────────────────────┘
```

---

## Docker Compose Commands

### Start Services

```bash
# Build and start all services
docker-compose up --build

# Start in background (detached)
docker-compose up -d

# Start only specific services
docker-compose up db backend
```

### Stop Services

```bash
# Stop all services (graceful)
docker-compose down

# Stop and remove volumes (DELETES DATABASE!)
docker-compose down -v

# Stop without removing containers
docker-compose stop
```

### View Logs

```bash
# View all logs
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# Logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Check Status

```bash
# List running services
docker-compose ps

# View resource usage
docker stats
```

---

## Service Details

### PostgreSQL (Database)
- **Container**: `portfolio-db`
- **Port**: 5432
- **User**: portfolio_user
- **Password**: portfolio_pass
- **Database**: portfolio_db
- **Data**: Persisted in Docker volume `postgres_data`

**Health Check:**
```bash
# Check if database is ready
docker-compose exec db pg_isready -U portfolio_user
```

**Connect to Database:**
```bash
# Using psql in container
docker-compose exec db psql -U portfolio_user -d portfolio_db

# From host (requires psql installed)
psql -h localhost -U portfolio_user -d portfolio_db
```

### Backend (FastAPI)
- **Container**: `portfolio-backend`
- **Port**: 8000
- **Auto-reload**: Enabled (changes reflected immediately)
- **Migrations**: Run automatically on startup

**Check Backend Health:**
```bash
curl http://localhost:8000/health
```

**View API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Run Backend Commands:**
```bash
# Access backend shell
docker-compose exec backend sh

# Run migrations manually
docker-compose exec backend alembic upgrade head

# Run tests
docker-compose exec backend pytest

# Check logs
docker-compose logs -f backend
```

### Frontend (React + Vite)
- **Container**: `portfolio-frontend`
- **Port**: 5173
- **Hot Module Replacement**: Enabled
- **API URL**: Configured via VITE_API_BASE_URL

**Rebuild Frontend:**
```bash
# If you modify package.json
docker-compose build frontend
docker-compose up -d frontend
```

**Check Frontend Logs:**
```bash
docker-compose logs -f frontend
```

---

## First-Time Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd Rakuten-trade-portfolio-X-ray
```

### 2. Create Environment File
```bash
cp .env.example .env
```

### 3. (Optional) Add Gemini API Key
Edit `.env`:
```
GEMINI_API_KEY=your_actual_api_key_here
```

Get API key: https://makersuite.google.com/app/apikey

### 4. Launch Application
```bash
docker-compose up --build
```

**First launch will:**
1. Download Docker images (PostgreSQL, Node, Python)
2. Install backend dependencies
3. Install frontend dependencies
4. Create database
5. Run migrations
6. Start all services

**Estimated time:** 5-10 minutes (first time only)

---

## Usage Workflow

### 1. Upload CSV Files

1. Open http://localhost:5173
2. Drag and drop your Rakuten Securities CSV files:
   - Transaction history files (US, JP, INVST)
   - Asset balance file
3. Wait for processing

### 2. View Dashboard

After upload:
- Portfolio summary (XIRR, total value, P&L)
- 9 interactive charts
- Holdings table with editable prices
- AI insights (if Gemini API key configured)

### 3. Edit Prices (Simulation)

- Click any current price in the holdings table
- Enter new price
- Press Enter to recalculate XIRR

### 4. Generate AI Insights

- Click "分析を実行" button
- Wait for Gemini to analyze portfolio
- View markdown-formatted insights

---

## Troubleshooting

### Services Won't Start

**Error:** `port already in use`
```bash
# Check what's using the port
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Database

# Kill the process or change ports in docker-compose.yml
```

**Error:** `Cannot connect to Docker daemon`
```bash
# Start Docker Desktop application
# Or run: open -a Docker
```

### Database Issues

**Error:** `database does not exist`
```bash
# Recreate database
docker-compose down -v
docker-compose up --build
```

**Error:** `password authentication failed`
```bash
# Check .env file has correct credentials
# Restart services
docker-compose restart
```

### Backend Won't Start

**Check logs:**
```bash
docker-compose logs backend
```

**Common issues:**
- Missing dependencies: `docker-compose build backend`
- Database not ready: Wait for health check
- Port conflict: Change port in docker-compose.yml

**Force rebuild:**
```bash
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Frontend Won't Start

**Check logs:**
```bash
docker-compose logs frontend
```

**Rebuild:**
```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

**Clear node_modules:**
```bash
docker-compose down
docker volume rm portfolio-xray_node_modules
docker-compose up --build
```

### Database Migrations Failed

```bash
# Run migrations manually
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history
```

---

## Development Mode

### Backend Development (without Docker)

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database (PostgreSQL must be running)
export DATABASE_URL=postgresql://portfolio_user:portfolio_pass@localhost:5432/portfolio_db

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Frontend Development (without Docker)

```bash
cd frontend

# Install dependencies
npm install

# Create .env
cp .env.example .env

# Start dev server
npm run dev
```

### Using Docker for DB Only

```bash
# Start only database
docker-compose up -d db

# Run backend locally
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Run frontend locally
cd frontend
npm run dev
```

---

## Production Deployment

### Build for Production

```bash
# Build optimized images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Update `.env` for production:
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/portfolio_db
# Add production Gemini API key
```

### Backup Database

```bash
# Backup
docker-compose exec db pg_dump -U portfolio_user portfolio_db > backup.sql

# Restore
cat backup.sql | docker-compose exec -T db psql -U portfolio_user -d portfolio_db
```

---

## Resource Usage

**Typical resource consumption:**
- PostgreSQL: ~50MB RAM
- Backend: ~200MB RAM
- Frontend (dev): ~150MB RAM
- **Total**: ~400MB RAM

**Disk space:**
- Docker images: ~2GB
- Database volume: ~100MB (grows with data)
- node_modules: ~500MB

---

## Next Steps After Launch

Once the application is running:

1. ✅ Upload your CSV files
2. ✅ Verify dashboard displays correctly
3. ✅ Test price editing
4. ✅ Generate AI insights (if configured)
5. 🔄 Ready for Phase 4: ML Integration

---

## Support

**Check Service Health:**
```bash
# Database
curl http://localhost:8000/health

# Backend API
curl http://localhost:8000/

# Frontend
curl http://localhost:5173/
```

**Common Commands:**
```bash
# Complete restart
docker-compose down && docker-compose up --build

# View all logs
docker-compose logs -f

# Check running containers
docker-compose ps

# Remove everything (fresh start)
docker-compose down -v
docker-compose up --build
```

---

## Summary

```bash
# Daily workflow:
docker-compose up -d          # Start services
# Use application...
docker-compose down            # Stop services

# Development:
docker-compose logs -f         # Monitor logs
docker-compose restart backend # Restart after code changes
docker-compose exec backend pytest  # Run tests

# Troubleshooting:
docker-compose down -v         # Nuclear option
docker-compose up --build      # Fresh start
```

**Application URLs:**
- 🎨 **Frontend**: http://localhost:5173
- ⚙️ **Backend**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
