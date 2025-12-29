# Phase 4: ML Integration - Revised Plan

## Data Constraints Analysis

### Available from Rakuten CSVs
- ✅ Transaction history with dates and prices
- ✅ Buy/sell prices at specific points in time
- ✅ Current portfolio snapshot (balance CSV)
- ✅ Realized/unrealized P&L
- ✅ Cash flow history (investments and withdrawals)

### NOT Available
- ❌ Daily historical price data for individual assets
- ❌ Continuous time series for each holding
- ❌ Market data between transaction dates

## Realistic ML Features (CSV-Based Only)

### Feature 1: Portfolio Growth Forecasting ⭐ Priority 1
**What it does:**
- Builds time series of total portfolio value from transaction history
- Forecasts portfolio value 30/60/90 days ahead
- Shows confidence intervals

**Data Source:**
- Extract from transactions: cumulative portfolio value at each transaction date
- Current snapshot from balance CSV

**Algorithm:** Prophet (Facebook's time series forecasting)

**Implementation:**
```python
# backend/app/ml/models/portfolio_forecaster.py
class PortfolioForecaster:
    def build_timeseries(self, transactions):
        # Aggregate portfolio value at each transaction date
        # Returns: [(date, total_value), ...]

    def forecast(self, horizon_days=90):
        # Prophet prediction
        # Returns: future dates + predicted values + confidence bands
```

**Frontend Component:**
- Line chart with historical + forecasted values
- Shaded confidence interval
- Toggle 30/60/90 day forecast

---

### Feature 2: Cash Flow Pattern Analysis ⭐ Priority 2
**What it does:**
- Analyzes monthly investment patterns
- Predicts future monthly contributions
- Identifies trends (increasing/decreasing investment rate)

**Data Source:**
- Transaction amounts grouped by month
- Buy vs Sell volume

**Algorithm:** Linear regression + moving averages

**Implementation:**
```python
# backend/app/ml/models/cashflow_predictor.py
class CashFlowPredictor:
    def analyze_patterns(self, transactions):
        # Group by month, calculate net flow
        # Detect trends (DCA, lump sum, etc.)

    def predict_next_months(self, n_months=6):
        # Predict future monthly investments
```

**Frontend Component:**
- Bar chart: historical monthly flows + predicted
- Trend line overlay
- Stats: average monthly investment, consistency score

---

### Feature 3: Risk Scoring System ⭐ Priority 1
**What it does:**
- Assigns risk score (0-100) to each holding
- Calculates portfolio-wide risk metrics
- No external data needed

**Risk Factors from CSV:**
1. **Concentration Risk**: % of portfolio in single asset
2. **Volatility Proxy**: Price variance across transactions
3. **Asset Class Risk**: Equity > REIT > Bond
4. **Holding Duration**: Longer holding = more stable
5. **Transaction Frequency**: Frequent trades = higher risk

**Algorithm:** Weighted scoring model → XGBoost (future)

**Implementation:**
```python
# backend/app/services/risk_analyzer.py
class RiskAnalyzer:
    def calculate_concentration_risk(self, holdings):
        # Herfindahl index

    def calculate_volatility_proxy(self, transactions):
        # Std dev of transaction prices per asset

    def assign_risk_score(self, holding):
        # Weighted sum of factors
        # Returns: score (0-100), level (Low/Med/High)
```

**Frontend Component:**
- Heatmap table: holdings with color-coded risk
- Overall portfolio risk gauge
- Risk breakdown by factor

---

### Feature 4: Portfolio Optimization ⭐ Priority 2
**What it does:**
- Suggests rebalancing based on current allocation
- Uses historical XIRR as expected return proxy
- Recommends buy/sell actions

**Data Source:**
- Current holdings (quantities, values)
- Historical XIRR per asset (already calculated)
- Asset class categories

**Algorithm:** Mean-Variance Optimization (Markowitz)

**Implementation:**
```python
# backend/app/ml/models/portfolio_optimizer.py
class PortfolioOptimizer:
    def calculate_optimal_weights(self, holdings):
        # Use XIRR as expected return
        # Estimate covariance from transaction data
        # Solve for max Sharpe ratio

    def generate_rebalancing_plan(self, current, optimal):
        # Suggest: "Sell 5 shares of QQQ, Buy 10 shares of AGG"
```

**Frontend Component:**
- Current vs Optimal allocation comparison (pie charts)
- Rebalancing suggestions table
- Expected improvement in Sharpe ratio

---

### Feature 5: Transaction Pattern Detection ⭐ Priority 3
**What it does:**
- Identifies investment strategy from transaction history
- Detects: Dollar-Cost Averaging, Lump Sum, Market Timing
- Provides strategy insights

**Data Source:**
- Transaction dates and amounts
- Buy/sell patterns

**Algorithm:** Pattern matching + clustering

**Implementation:**
```python
# backend/app/ml/models/strategy_detector.py
class StrategyDetector:
    def detect_dca_pattern(self, transactions):
        # Regular monthly investments?

    def detect_market_timing(self, transactions):
        # Irregular large purchases?

    def classify_strategy(self):
        # Returns: "Consistent DCA" | "Lump Sum" | "Mixed"
```

---

## External Data Integration (Future Phase 4.5)

### Feature 6: Individual Asset Price Forecasting ⚠️ (Requires External API)
**What it does:**
- Forecast individual stock/ETF prices
- Only for assets with Yahoo Finance tickers

**Requirements:**
- Yahoo Finance API or Alpha Vantage
- Ticker mapping: QQQ, VTI, etc. → Yahoo symbols
- Rate limit handling

**Implementation:**
```python
# backend/app/services/external_data_fetcher.py
class PriceFetcher:
    def fetch_historical_prices(self, ticker, start_date, end_date):
        # Call Yahoo Finance API
        # Return daily prices

# backend/app/ml/models/asset_forecaster.py
class AssetForecaster:
    def forecast_price(self, ticker, horizon_days=90):
        # Fetch history → Prophet → Forecast
```

**Note:** Not included in initial Phase 4 due to:
- External API dependencies
- Rate limits and costs
- Data quality issues (delisted tickers, name changes)

---

## Implementation Timeline

### Week 1: Data Extraction & Portfolio Forecaster
- [ ] Create CSV analyzer to build portfolio time series
- [ ] Implement `PortfolioForecaster` with Prophet
- [ ] Add API endpoint: `POST /api/v1/ml/forecast/portfolio`
- [ ] Create frontend component: `PortfolioForecastPanel.tsx`

### Week 2: Risk Scoring System
- [ ] Implement `RiskAnalyzer` service
- [ ] Calculate concentration, volatility proxy, asset class risk
- [ ] Add API endpoint: `GET /api/v1/portfolios/{id}/risk-analysis`
- [ ] Create frontend component: `RiskHeatmap.tsx`

### Week 3: Cash Flow & Optimization
- [ ] Implement `CashFlowPredictor`
- [ ] Implement `PortfolioOptimizer` (basic version)
- [ ] Add API endpoints
- [ ] Create frontend components

### Week 4: Integration & Testing
- [ ] Integrate all ML components into dashboard
- [ ] Test with real CSV data
- [ ] Performance optimization
- [ ] Documentation

---

## Database Schema Additions

```sql
-- ML predictions cache table
CREATE TABLE ml_predictions (
    id UUID PRIMARY KEY,
    portfolio_id UUID REFERENCES portfolios(id),
    model_type VARCHAR(50),  -- 'portfolio_forecast' | 'risk_score' | 'cashflow'
    prediction_data JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    model_version VARCHAR(20)
);

-- Risk scores table
CREATE TABLE risk_scores (
    id UUID PRIMARY KEY,
    holding_id UUID REFERENCES holdings(id),
    overall_score INT,  -- 0-100
    risk_level VARCHAR(20),  -- Low/Medium/High
    concentration_risk FLOAT,
    volatility_score FLOAT,
    factors JSONB,  -- Detailed breakdown
    calculated_at TIMESTAMP
);
```

---

## API Endpoints (Phase 4)

### Portfolio Forecasting
```
POST /api/v1/ml/forecast/portfolio
Body: { "portfolio_id": "uuid", "horizon_days": 90 }
Response: {
    "historical": [{"date": "2020-01-01", "value": 100000}, ...],
    "forecast": [{"date": "2025-03-01", "value": 150000, "lower": 145000, "upper": 155000}],
    "model_version": "1.0",
    "confidence": 0.85
}
```

### Risk Analysis
```
GET /api/v1/portfolios/{id}/risk-analysis
Response: {
    "overall_risk_score": 45,  // 0-100
    "risk_level": "Medium",
    "portfolio_risks": {
        "concentration_risk": 0.35,
        "volatility_score": 0.42,
        "diversification_score": 0.75
    },
    "holdings_risk": [
        {
            "symbol": "QQQ",
            "risk_score": 65,
            "risk_level": "Medium-High",
            "factors": {...}
        }
    ]
}
```

### Cash Flow Prediction
```
GET /api/v1/portfolios/{id}/cashflow/predict
Response: {
    "historical_monthly": [{"month": "2024-12", "net_flow": 15000}, ...],
    "predicted_monthly": [{"month": "2025-01", "predicted_flow": 15200, "confidence": 0.9}],
    "pattern": "Consistent DCA",
    "average_monthly": 15000
}
```

### Portfolio Optimization
```
POST /api/v1/ml/optimize
Body: { "portfolio_id": "uuid", "objective": "max_sharpe" }
Response: {
    "current_allocation": {"QQQ": 0.25, "VTI": 0.50, ...},
    "optimal_allocation": {"QQQ": 0.20, "VTI": 0.55, ...},
    "rebalancing_actions": [
        {"action": "sell", "symbol": "QQQ", "shares": 5},
        {"action": "buy", "symbol": "VTI", "shares": 10}
    ],
    "expected_sharpe_improvement": 0.15
}
```

---

## Success Criteria

### Must Have (Phase 4 Core)
- ✅ Portfolio value forecasting with 90-day horizon
- ✅ Risk scoring for all holdings (0-100 scale)
- ✅ Portfolio-wide risk metrics
- ✅ Cash flow pattern analysis

### Nice to Have
- ✅ Portfolio optimization suggestions
- ✅ Transaction strategy detection
- ✅ Confidence intervals on forecasts

### Future (Phase 4.5)
- ⚠️ Individual asset price forecasting (requires external API)
- ⚠️ Real-time price updates
- ⚠️ Backtesting capabilities

---

## Dependencies

### Python Packages (Add to requirements.txt)
```
prophet>=1.1.5          # Time series forecasting
scikit-learn>=1.4.0     # Optimization, clustering
xgboost>=2.0.0          # Future: advanced risk modeling
scipy>=1.11.0           # Optimization algorithms
```

### Frontend Packages
```json
{
  "recharts": "^2.10.0",  // Already installed
  // Charts for forecast visualization
}
```

---

## Next Steps

1. **Confirm Approach**: Do you approve this revised plan focused on CSV-extractable data?
2. **Sample Data Analysis**: I can analyze your actual CSV files to validate the approach
3. **Prototype**: Build portfolio forecaster first as proof of concept
4. **Iterate**: Add risk scoring, then optimization

**Key Question:** Should we proceed with Phase 4 using only CSV-based ML, or do you want to integrate external APIs (Yahoo Finance) for individual asset forecasting?
