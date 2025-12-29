# Portfolio X-Ray - Quick Start

⚡ **3 commands to launch the entire application**

---

## 🚀 Launch Application

```bash
# 1. Create environment file (one-time)
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

---

## 📋 Daily Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

---

## 🔧 Useful Commands

```bash
# Backend shell
docker-compose exec backend sh

# Database access
docker-compose exec db psql -U portfolio_user -d portfolio_db

# Run tests
docker-compose exec backend pytest

# Check status
docker-compose ps
```

---

## 🆘 Troubleshooting

```bash
# Nuclear option (fresh start)
docker-compose down -v
docker-compose up --build

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# View errors
docker-compose logs backend
```

---

## 📱 Application URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Main application |
| Backend API | http://localhost:8000 | REST API |
| Swagger Docs | http://localhost:8000/docs | API documentation |
| PostgreSQL | localhost:5432 | Database |

---

## ✅ First-Time Setup Checklist

- [ ] Docker Desktop installed and running
- [ ] Cloned repository
- [ ] Created `.env` file (`cp .env.example .env`)
- [ ] (Optional) Added Gemini API key to `.env`
- [ ] Run `docker-compose up --build`
- [ ] Wait 5-10 minutes for first build
- [ ] Open http://localhost:5173
- [ ] Upload CSV files
- [ ] ✨ Done!

---

## 🎯 What You Get

**Frontend (React):**
- Portfolio dashboard with KPIs
- 9 interactive charts (Recharts)
- Editable holdings table
- AI insights panel
- File upload with drag-drop

**Backend (FastAPI):**
- 16 REST API endpoints
- PostgreSQL database
- XIRR calculation engine
- CSV parsing (Shift_JIS support)
- Gemini AI integration

**Database (PostgreSQL):**
- Persistent data storage
- Transaction history
- Holdings with metrics
- Automatic migrations

---

## 📊 System Status Check

```bash
# Check if everything is running
docker-compose ps

# Should see:
# portfolio-db        Up (healthy)
# portfolio-backend   Up
# portfolio-frontend  Up
```

---

## 🔥 Common Issues

**Port already in use:**
```bash
lsof -i :5173  # Check what's using port
# Change port in docker-compose.yml if needed
```

**Database connection failed:**
```bash
docker-compose restart db
docker-compose logs db
```

**Frontend not loading:**
```bash
docker-compose logs frontend
# Check for npm install errors
```

**Backend errors:**
```bash
docker-compose logs backend
# Check for Python import errors
```

---

## 🎓 Learn More

- Full guide: [STARTUP_GUIDE.md](./STARTUP_GUIDE.md)
- README: [README.md](./README.md)
- API docs: http://localhost:8000/docs (after starting)

---

**Need help?** Check logs with `docker-compose logs -f`
