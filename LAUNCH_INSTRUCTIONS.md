# 🚀 How to Launch Portfolio X-Ray

## Current Status

✅ **Everything is ready!** You just need to start Docker.

### Pre-flight Check Results:
- ✅ Docker installed: v28.3.0
- ✅ Docker Compose: v2.38.1
- ✅ All ports available (5432, 8000, 5173)
- ✅ docker-compose.yml validated
- ✅ CSV files ready (4 files in inputs/)
- ✅ .env file created
- ⚠️ Docker daemon not running (needs to be started)

---

## 🎯 Launch Steps (2 commands)

### Step 1: Start Docker Desktop

```bash
# Option A: Use Finder
# Open Applications → Docker

# Option B: Use terminal
open -a Docker

# Wait ~10 seconds for Docker to start
```

### Step 2: Launch Application

```bash
# Run from project root
docker-compose up --build
```

**That's it!** 🎉

---

## ⏱️ What Happens Next

**First launch (5-10 minutes):**
1. Downloads Docker images (PostgreSQL, Node, Python)
2. Installs backend dependencies (~100 packages)
3. Installs frontend dependencies (~1000 packages)
4. Creates database
5. Runs migrations
6. Starts all services

**Subsequent launches (<1 minute):**
- Uses cached images and dependencies
- Only restarts services

---

## 📱 Access Points

Once you see these messages:
```
portfolio-db        | database system is ready to accept connections
portfolio-backend   | Uvicorn running on http://0.0.0.0:8000
portfolio-frontend  | ➜  Local: http://localhost:5173/
```

**Open your browser:**

| Service | URL | Purpose |
|---------|-----|---------|
| 🎨 **Frontend** | http://localhost:5173 | Main application |
| ⚙️ **API** | http://localhost:8000 | Backend REST API |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger documentation |

---

## 📊 Using the Application

### 1. Upload CSV Files

Your CSV files are already in `inputs/`:
- ✅ assetbalance(all)_20251226_175959.csv
- ✅ tradehistory(US)_20251226.csv
- ✅ tradehistory(JP)_20251226.csv
- ✅ tradehistory(INVST)_20251226.csv

**To upload:**
1. Go to http://localhost:5173
2. Drag and drop all 4 CSV files
3. Wait for processing (~5 seconds)

### 2. View Dashboard

After upload, you'll see:
- **Portfolio XIRR**: Annual return rate
- **KPI Metrics**: Current value, P&L, realized gains
- **9 Charts**: Asset allocation, performance, trends
- **Holdings Table**: All your investments with metrics

### 3. Simulate Prices

Click any price in the holdings table → Enter new price → See XIRR recalculate instantly

### 4. AI Insights (Optional)

**If you want AI insights:**
1. Get Gemini API key: https://makersuite.google.com/app/apikey
2. Edit `.env`: `GEMINI_API_KEY=your_key_here`
3. Restart: `docker-compose restart backend`
4. Click "分析を実行" button in app

---

## 🛑 Stopping the Application

```bash
# Stop all services (graceful)
docker-compose down

# Stop and keep running
Ctrl + C (in the terminal)
```

---

## 🔧 Useful Commands

```bash
# View logs (all services)
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Check service status
docker-compose ps

# Fresh restart (nuclear option)
docker-compose down -v
docker-compose up --build
```

---

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill it
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

### Frontend Not Loading

```bash
# Check logs
docker-compose logs frontend

# Rebuild
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Database Connection Error

```bash
# Restart database
docker-compose restart db

# Check health
docker-compose exec db pg_isready -U portfolio_user
```

### Complete Reset

```bash
# Delete everything and start fresh
docker-compose down -v
docker volume prune
docker-compose up --build
```

---

## 📈 What You Get

### Frontend Features:
- ✅ Portfolio dashboard with real-time KPIs
- ✅ XIRR gauge (annual return visualization)
- ✅ 9 interactive charts (Recharts)
- ✅ Editable holdings table
- ✅ AI insights panel (Gemini)
- ✅ File upload with drag-drop
- ✅ Search and filter

### Backend Features:
- ✅ 16 REST API endpoints
- ✅ XIRR calculation (Newton-Raphson)
- ✅ CSV parsing (Shift_JIS encoding)
- ✅ PostgreSQL database
- ✅ Transaction aggregation
- ✅ Asset classification
- ✅ Gemini AI integration
- ✅ Auto migrations

### Data Processed:
Based on your CSV files:
- **230 transactions** over 5.1 years
- **40 unique assets** (US stocks, JP stocks, Investment trusts)
- **4 asset classes** (Equity, Commodity, REIT, Bond)
- **3 markets** (US, JP, INVST)

---

## 🎓 Next Steps

After you've verified the application works:

1. ✅ **Phase 3 Complete**: Full-stack app operational
2. 🔄 **Phase 4 Next**: ML forecasting (we'll use interpolation for prices)
3. 📊 **Data Quality**: Can add Yahoo Finance caching later

---

## 📝 Summary

**To launch RIGHT NOW:**

```bash
# 1. Start Docker
open -a Docker

# 2. Wait 10 seconds, then launch
docker-compose up --build

# 3. Open browser
# http://localhost:5173
```

**First time:** ~10 minutes
**After that:** ~30 seconds

**Your CSV files are already in the right place!**

---

## 📚 Documentation

- **Quick Start**: [QUICK_START.md](./QUICK_START.md)
- **Full Guide**: [STARTUP_GUIDE.md](./STARTUP_GUIDE.md)
- **README**: [README.md](./README.md)
- **Phase 4 Plan**: [PHASE4_REVISED_PLAN.md](./PHASE4_REVISED_PLAN.md)

---

**Ready when you are!** 🚀

Run pre-flight check anytime: `./preflight_check.sh`
