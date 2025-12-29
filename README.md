# Portfolio X-Ray

Advanced portfolio analysis tool with XIRR calculations, ML predictions, and real-time visualizations for Rakuten Securities investors.

## Features

### Current (Phases 1-3 Complete)
- ✅ XIRR (Extended Internal Rate of Return) calculation using Newton-Raphson method
- ✅ CSV parsing for Rakuten Securities files (Shift_JIS encoding)
  - Transaction history (US stocks, JP stocks, Investment trusts)
  - Asset balance data with automatic price updates
- ✅ Asset classification (Equity, Bond, REIT, Commodity)
- ✅ Strategy classification (Core/Satellite)
- ✅ PostgreSQL database with Alembic migrations
- ✅ FastAPI backend with automatic API documentation (16 endpoints)
- ✅ React + TypeScript frontend with Vite
- ✅ 9 interactive chart visualizations (Recharts)
- ✅ AI-powered portfolio insights (Google Gemini)
- ✅ Real-time price editing with XIRR recalculation
- ✅ TailwindCSS responsive design

### Planned (Future Phases)
- 🔄 ML-powered price forecasting (Prophet)
- 🔄 Portfolio optimization recommendations (Mean-Variance)
- 🔄 Risk analysis with scoring (XGBoost)
- 🔄 PDF export functionality
- 🔄 Nginx reverse proxy

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- PostgreSQL 15 (database)
- SQLAlchemy + Alembic (ORM + migrations)
- Pandas, NumPy (data processing)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Zustand (state management)
- TailwindCSS (styling)
- Recharts (visualizations)
- Lucide React (icons)

**Infrastructure:**
- Docker + Docker Compose
- Nginx (reverse proxy)

## Getting Started

### Prerequisites
- Docker Desktop (includes Docker Compose)
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Rakuten-trade-portfolio-X-ray.git
   cd Rakuten-trade-portfolio-X-ray
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your GEMINI_API_KEY if needed
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Development Setup (Without Docker)

1. **Backend Setup**
   ```bash
   cd backend

   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Setup PostgreSQL locally
   # Update DATABASE_URL in backend/.env

   # Run migrations
   alembic upgrade head

   # Start server
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend

   # Install dependencies
   npm install

   # Setup environment
   cp .env.example .env
   # Update VITE_API_BASE_URL if needed

   # Start development server
   npm run dev
   ```

3. **Run Tests**
   ```bash
   cd backend
   pytest
   ```

## Project Structure

```
portfolio-xray/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # ✅ API routes
│   │   │   ├── upload.py
│   │   │   ├── portfolio.py
│   │   │   ├── analysis.py
│   │   │   └── ai_insights.py
│   │   ├── db/            # ✅ Database models
│   │   │   ├── base.py
│   │   │   └── models/
│   │   ├── ml/            # ML models (to be added)
│   │   ├── schemas/       # ✅ Pydantic schemas
│   │   ├── services/      # ✅ Business logic
│   │   │   ├── xirr_calculator.py
│   │   │   ├── csv_parser.py
│   │   │   ├── asset_classifier.py
│   │   │   ├── portfolio_aggregator.py
│   │   │   └── balance_merger.py
│   │   ├── utils/         # Utility functions
│   │   ├── config.py      # ✅ Settings
│   │   └── main.py        # ✅ FastAPI app
│   ├── alembic/           # ✅ Database migrations
│   ├── tests/             # ✅ Unit tests
│   ├── Dockerfile         # ✅ Backend container
│   └── requirements.txt   # ✅ Python dependencies
├── frontend/              # ✅ React application
│   ├── src/
│   │   ├── components/    # ✅ React components
│   │   │   ├── layout/    # Header, Dashboard, SplashScreen
│   │   │   ├── kpi/       # XIRRGauge, MetricsGrid
│   │   │   ├── charts/    # 9 chart visualizations
│   │   │   ├── table/     # HoldingsTable
│   │   │   └── ai/        # AIInsightPanel
│   │   ├── services/      # ✅ API client
│   │   ├── stores/        # ✅ Zustand state management
│   │   ├── types/         # ✅ TypeScript types
│   │   └── App.tsx        # ✅ Main app component
│   ├── Dockerfile         # ✅ Frontend container
│   └── package.json       # ✅ Dependencies
├── nginx/                 # (To be created in Phase 5)
├── docker-compose.yml     # ✅ Docker services
└── README.md              # ✅ This file
```

## API Documentation

Once the server is running, visit http://localhost:8000/docs for interactive API documentation.

### Available Endpoints (Phase 1 & 2)

**Core**
- `GET /` - API info
- `GET /health` - Health check

**Upload & Portfolio**
- `POST /api/v1/upload/csv` - Upload CSV files ✅
- `GET /api/v1/portfolios` - List portfolios ✅
- `POST /api/v1/portfolios` - Create portfolio ✅
- `GET /api/v1/portfolios/{id}` - Get portfolio ✅
- `GET /api/v1/portfolios/{id}/summary` - Portfolio summary ✅
- `GET /api/v1/portfolios/{id}/holdings` - Current holdings ✅
- `PUT /api/v1/portfolios/{id}/holdings/{symbol}/price` - Update price ✅

**Analysis**
- `POST /api/v1/analysis/xirr` - Calculate XIRR ✅
- `GET /api/v1/portfolios/{id}/analysis/metrics` - All metrics ✅

**Charts**
- `GET /api/v1/portfolios/{id}/charts/allocation-by-class` ✅
- `GET /api/v1/portfolios/{id}/charts/allocation-by-strategy` ✅
- `GET /api/v1/portfolios/{id}/charts/monthly-flow` ✅
- `GET /api/v1/portfolios/{id}/charts/top-performers` ✅

**AI Insights**
- `POST /api/v1/ai/insights` - Generate AI portfolio report ✅

### Upcoming Endpoints (Phase 4)

- `POST /api/v1/ml/forecast/{symbol}` - Price forecasting
- `POST /api/v1/ml/optimize` - Portfolio optimization
- `GET /api/v1/portfolios/{id}/ml/risk-analysis` - Risk scores

## Database Schema

### Core Tables
- **portfolios** - Portfolio metadata
- **transactions** - All buy/sell/dividend events
- **holdings** - Current positions with calculated metrics
- **predictions** - ML model outputs (future)

See detailed schema in [PLAN.md](/.claude/plans/flickering-beaming-owl.md)

## Development Roadmap

- [x] **Phase 1: Backend Foundation** (Weeks 1-2) ✅ COMPLETED
  - [x] FastAPI setup
  - [x] Database models
  - [x] XIRR calculator
  - [x] CSV parser
  - [x] Docker configuration

- [x] **Phase 2: Backend API** (Weeks 3-4) ✅ COMPLETED
  - [x] Upload endpoints
  - [x] Analysis endpoints
  - [x] AI insights (Gemini)
  - [x] Chart data endpoints

- [x] **Phase 3: Frontend** (Weeks 5-6) ✅ COMPLETED
  - [x] React + TypeScript setup with Vite
  - [x] TailwindCSS styling
  - [x] Dashboard layout components
  - [x] KPI components (XIRRGauge, MetricsGrid)
  - [x] 9 chart visualizations (Recharts)
  - [x] Holdings table with editable prices
  - [x] AI insights panel
  - [x] Zustand state management
  - [x] File upload with drag-drop

- [ ] **Phase 4: ML Integration** (Weeks 7-8)
  - [ ] Price forecasting
  - [ ] Portfolio optimization
  - [ ] Risk analysis

- [ ] **Phase 5: Docker & Deployment** (Week 9)
  - [ ] Complete containerization
  - [ ] Nginx setup

- [ ] **Phase 6: Testing & Polish** (Week 10)
  - [ ] E2E testing
  - [ ] Performance optimization

## Testing

Run backend tests:
```bash
cd backend
pytest -v
```

Test XIRR calculations:
```bash
pytest tests/test_xirr.py -v
```

## Contributing

This is a personal project currently in active development. Contributions are welcome after the initial implementation is complete.

## License

MIT License

## Acknowledgments

- Original single-file HTML implementation as proof of concept
- Rakuten Securities for CSV data format
- FastAPI and React communities

---

**Current Status:** Phase 3 Complete ✅ | Full-Stack Application Ready
**Next:** Phase 4 - ML Integration (Forecasting, Optimization, Risk Analysis)

## Charts & Visualizations

The application includes 9 interactive chart visualizations:

1. **Asset Allocation by Class** - Pie chart showing portfolio breakdown by asset type
2. **Core/Satellite Strategy** - Pie chart showing strategic allocation
3. **XIRR by Asset Class** - Horizontal bar chart comparing returns across asset classes
4. **Monthly Investment Flow** - Stacked bar chart showing investment and withdrawal patterns
5. **Realized P&L by Class** - Bar chart showing realized profits/losses per asset class
6. **Top 5 XIRR Performers** - Horizontal bar chart highlighting best performers
7. **Core/Satellite Cumulative Trend** - Area chart showing portfolio composition over time
8. **Win Rate for Closed Positions** - Doughnut chart showing success rate
9. **Holding Period vs XIRR** - Scatter chart analyzing return vs holding duration

## Usage

1. **Upload CSV Files**: Drag and drop your Rakuten Securities CSV files (transaction history and balance)
2. **View Dashboard**: See comprehensive portfolio metrics, KPIs, and XIRR
3. **Explore Charts**: Interact with 9 different visualizations
4. **Edit Prices**: Click on current prices in the holdings table to simulate different scenarios
5. **Generate AI Insights**: Click "分析を実行" for AI-powered portfolio analysis

See [QUICKSTART.md](./QUICKSTART.md) for detailed usage guide and API examples.