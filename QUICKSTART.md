# Quick Start Guide - Portfolio X-Ray

## Phase 2 Complete! 🎉

The backend API is now fully functional with all endpoints ready to use.

## What's New

### API Endpoints Available

#### 1. Upload CSV Files
```bash
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -F "files=@your_transaction_history.csv" \
  -F "files=@your_asset_balance.csv"
```

#### 2. Get Portfolio Summary
```bash
curl "http://localhost:8000/api/v1/portfolios/{portfolio_id}/summary"
```

#### 3. Calculate XIRR
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/xirr" \
  -H "Content-Type: application/json" \
  -d '{
    "cash_flows": [
      {"date": "2023-01-01", "amount": -1000},
      {"date": "2024-01-01", "amount": 1200}
    ]
  }'
```

#### 4. Get Portfolio Metrics
```bash
curl "http://localhost:8000/api/v1/portfolios/{portfolio_id}/analysis/metrics"
```

#### 5. Update Holding Price
```bash
curl -X PUT "http://localhost:8000/api/v1/portfolios/{portfolio_id}/holdings/VTI/price" \
  -H "Content-Type: application/json" \
  -d '{"current_price": 250.50}'
```

#### 6. Generate AI Insights
```bash
curl -X POST "http://localhost:8000/api/v1/ai/insights" \
  -H "Content-Type: application/json" \
  -d '{"portfolio_id": "{portfolio_id}"}'
```

## Running the Application

### Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up --build

# The API will be available at:
# - API: http://localhost:8000
# - Swagger Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### Option 2: Local Development

```bash
# 1. Start PostgreSQL (ensure it's running on port 5432)

# 2. Install dependencies
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env and set DATABASE_URL and GEMINI_API_KEY

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload

# API available at http://localhost:8000
```

## Testing the API

### 1. Check Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. View API Documentation

Open in browser: http://localhost:8000/docs

This provides:
- Interactive API testing
- Request/response schemas
- Authentication (future)

### 3. Upload Sample CSV

If you have Rakuten Securities CSV files:

```bash
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -F "files=@/path/to/your/transactions.csv" \
  -F "files=@/path/to/your/balance.csv"
```

Response will include:
- `portfolio_id`: UUID of created portfolio
- `transactions_imported`: Number of transactions processed
- `holdings_created`: Number of holdings created
- `summary`: Portfolio metrics

### 4. Get Portfolio Summary

Using the `portfolio_id` from step 3:

```bash
curl "http://localhost:8000/api/v1/portfolios/{PORTFOLIO_ID}/summary"
```

Response includes:
- `total_xirr`: Overall portfolio return (annualized)
- `total_current_value`: Market value in JPY
- `total_unrealized_pl`: Unrealized profit/loss
- `total_realized_pl`: Realized profit/loss
- `holdings_count`: Number of holdings

### 5. Get Chart Data

```bash
# Asset allocation by class
curl "http://localhost:8000/api/v1/portfolios/{PORTFOLIO_ID}/charts/allocation-by-class"

# Monthly investment flow
curl "http://localhost:8000/api/v1/portfolios/{PORTFOLIO_ID}/charts/monthly-flow"

# Top performers
curl "http://localhost:8000/api/v1/portfolios/{PORTFOLIO_ID}/charts/top-performers"
```

## Database

The application uses PostgreSQL with the following tables:

- **portfolios** - Portfolio metadata
- **transactions** - All buy/sell transactions
- **holdings** - Current positions with XIRR
- **predictions** - ML predictions (future use)

To access the database:

```bash
docker exec -it portfolio-db psql -U portfolio_user -d portfolio_db
```

Useful queries:
```sql
-- View all portfolios
SELECT * FROM portfolios;

-- View holdings with XIRR
SELECT symbol, name, quantity, current_price, xirr
FROM holdings
WHERE portfolio_id = 'YOUR_UUID';

-- View recent transactions
SELECT transaction_date, symbol, side, quantity, amount_jpy
FROM transactions
ORDER BY transaction_date DESC
LIMIT 10;
```

## Troubleshooting

### Issue: "sqlalchemy.exc.OperationalError"
**Solution:** Ensure PostgreSQL is running:
```bash
docker-compose up db
```

### Issue: "Module not found"
**Solution:** Reinstall dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Alembic migration fails"
**Solution:** Reset database (⚠️ destroys data):
```bash
docker-compose down -v
docker-compose up --build
```

### Issue: "AI insights return 'API key not configured'"
**Solution:** Set GEMINI_API_KEY in `.env`:
```bash
echo "GEMINI_API_KEY=your_key_here" >> backend/.env
```

Get API key from: https://makersuite.google.com/app/apikey

## Development Workflow

### Making Changes

1. **Edit code** - Changes are hot-reloaded
2. **Run tests** - `cd backend && pytest`
3. **Check API docs** - http://localhost:8000/docs

### Adding New Endpoints

1. Create router in `backend/app/api/v1/`
2. Add to `router.py`
3. Create Pydantic schemas in `backend/app/schemas/`
4. Test via Swagger UI

### Database Migrations

When you modify models:

```bash
# Generate migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Next Steps

### Phase 3: Frontend (Coming Soon)
- React + TypeScript dashboard
- Interactive charts with Recharts
- Real-time price updates
- File upload UI

### Phase 4: ML Integration (Coming Soon)
- Price forecasting (Prophet)
- Portfolio optimization
- Risk analysis

## API Reference

Full API documentation: http://localhost:8000/docs

Key endpoints:
- `POST /api/v1/upload/csv` - Upload CSV files
- `GET /api/v1/portfolios` - List portfolios
- `GET /api/v1/portfolios/{id}/summary` - Portfolio summary
- `GET /api/v1/portfolios/{id}/holdings` - List holdings
- `PUT /api/v1/portfolios/{id}/holdings/{symbol}/price` - Update price
- `GET /api/v1/portfolios/{id}/analysis/metrics` - All metrics
- `POST /api/v1/analysis/xirr` - Calculate XIRR
- `POST /api/v1/ai/insights` - Generate AI report
- `GET /api/v1/portfolios/{id}/charts/*` - Chart data

## Support

- Issues: https://github.com/yourusername/Rakuten-trade-portfolio-X-ray/issues
- Docs: See README.md and plan file

---

**Status:** Phase 2 Complete ✅ | All Backend APIs Operational
