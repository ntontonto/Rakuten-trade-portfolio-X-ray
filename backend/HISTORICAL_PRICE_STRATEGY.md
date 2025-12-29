# Historical Price Data Strategy

## Problem
To calculate portfolio value time series, we need historical prices for each asset between transaction dates. But we only have:
- Transaction prices at buy/sell dates
- Current snapshot prices from balance CSV

## Multi-Tier Approach (Recommended)

### Tier 1: External APIs for Liquid Assets ✅ (Best Quality)

**Use Case:** US stocks, ETFs with Yahoo Finance tickers

**Data Source:** Yahoo Finance API (free, via `yfinance` library)

**Coverage:**
- ✅ US stocks: PLTR, PLUG, MU, MGA, TQQQ, etc.
- ✅ US ETFs: QQQ, DIA, IYR, EPHE, etc.
- ✅ Some Japanese ETFs: 1326, 1542, 1674, etc. (if listed on Yahoo)

**Implementation:**
```python
import yfinance as yf

def fetch_historical_prices(ticker: str, start_date: str, end_date: str):
    """
    Fetch daily historical prices from Yahoo Finance

    Args:
        ticker: Yahoo Finance ticker (e.g., "PLTR", "1326.T" for Japanese)
        start_date: "2020-01-01"
        end_date: "2025-12-31"

    Returns:
        DataFrame with Date and Close price
    """
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df[['Close']]
```

**Ticker Mapping Required:**
```python
TICKER_MAP = {
    # US stocks - direct mapping
    "PLTR": "PLTR",
    "QQQ": "QQQ",

    # Japanese stocks - add ".T" suffix for Tokyo Stock Exchange
    "1326": "1326.T",  # SPDR Gold
    "1542": "1542.T",  # Pure Silver Trust
    "1674": "1674.T",  # WisdomTree Platinum

    # Investment trusts - need proxy indices (see Tier 2)
}
```

**Pros:**
- ✅ Real historical data
- ✅ Free and reliable
- ✅ Daily granularity

**Cons:**
- ❌ API rate limits (2000 requests/hour)
- ❌ Japanese mutual funds not available

---

### Tier 2: Proxy Index Mapping for Investment Trusts ⚡ (Good Approximation)

**Use Case:** Japanese mutual funds (eMAXIS Slim, etc.)

**Strategy:** Map funds to proxy indices, fetch index performance

**Proxy Mappings:**
```python
FUND_TO_INDEX_MAP = {
    # eMAXIS Slim series
    "eMAXIS Slim 米国株式(S&P500)": {
        "proxy": "^GSPC",  # S&P 500 Index
        "currency": "USD",
        "multiplier": 1.0  # Adjust if needed
    },

    "eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)": {
        "proxy": "ACWI",  # MSCI All Country World Index ETF
        "currency": "USD",
        "multiplier": 1.0
    },

    "eMAXIS Slim 先進国リートインデックス(除く日本)": {
        "proxy": "VNQI",  # Vanguard Global ex-US Real Estate ETF
        "currency": "USD",
        "multiplier": 1.0
    },

    "eMAXIS Slim 先進国債券インデックス(除く日本)": {
        "proxy": "BNDX",  # Vanguard Total International Bond ETF
        "currency": "USD",
        "multiplier": 1.0
    },

    "三菱UFJ 純金ファンド(ファインゴールド)": {
        "proxy": "GLD",  # SPDR Gold Trust
        "currency": "USD",
        "multiplier": 1.0
    },

    "iFreeNEXT FANG+インデックス": {
        "proxy": "FNGU",  # MicroSectors FANG+ Index 3X Leveraged ETN
        "currency": "USD",
        "multiplier": 0.33  # De-leverage
    },

    "たわらノーロード インド株式Nifty50": {
        "proxy": "INDA",  # iShares MSCI India ETF
        "currency": "USD",
        "multiplier": 1.0
    },

    "ニッセイSOX指数インデックスファンド": {
        "proxy": "SOXX",  # iShares Semiconductor ETF
        "currency": "USD",
        "multiplier": 1.0
    },

    "NZAM・ベータ 米国REIT": {
        "proxy": "VNQ",  # Vanguard Real Estate ETF
        "currency": "USD",
        "multiplier": 1.0
    },
}
```

**Algorithm:**
```python
def estimate_fund_price(fund_name: str, date: str, initial_nav: float, initial_date: str):
    """
    Estimate mutual fund NAV using proxy index performance

    Args:
        fund_name: Fund name
        date: Target date for estimation
        initial_nav: Known NAV at a transaction date
        initial_date: Date of known NAV

    Returns:
        Estimated NAV
    """
    proxy_info = FUND_TO_INDEX_MAP.get(fund_name)
    if not proxy_info:
        return None

    # Fetch proxy index prices
    proxy = yf.Ticker(proxy_info["proxy"])
    initial_price = proxy.history(start=initial_date, end=initial_date)['Close'].iloc[0]
    target_price = proxy.history(start=date, end=date)['Close'].iloc[0]

    # Calculate return ratio
    return_ratio = target_price / initial_price

    # Apply to fund NAV
    estimated_nav = initial_nav * return_ratio * proxy_info["multiplier"]

    return estimated_nav
```

**Pros:**
- ✅ Good approximation (correlation ~0.95 for index funds)
- ✅ Works for Japanese mutual funds
- ✅ Uses free Yahoo Finance data

**Cons:**
- ⚠️ Not exact NAV (tracking error exists)
- ⚠️ Currency conversion needed

---

### Tier 3: Linear Interpolation (Fallback) 📊

**Use Case:** When no API data available or API fails

**Algorithm:**
```python
def interpolate_prices(transactions: List[Transaction], target_dates: List[date]):
    """
    Linear interpolation between known transaction prices

    Args:
        transactions: List of transactions with dates and prices
        target_dates: Dates to interpolate

    Returns:
        DataFrame with interpolated prices
    """
    # Extract known points
    known_dates = [tx.transaction_date for tx in transactions]
    known_prices = [tx.amount_jpy / tx.quantity for tx in transactions]

    # Sort by date
    sorted_data = sorted(zip(known_dates, known_prices))

    # Interpolate
    from scipy.interpolate import interp1d
    f = interp1d(
        [d.timestamp() for d, _ in sorted_data],
        [p for _, p in sorted_data],
        kind='linear',
        fill_value='extrapolate'
    )

    interpolated = [
        f(d.timestamp()) for d in target_dates
    ]

    return interpolated
```

**Pros:**
- ✅ Always works (no external dependency)
- ✅ Simple implementation

**Cons:**
- ❌ Very inaccurate (misses market movements)
- ❌ Smooth lines don't reflect volatility

---

### Tier 4: Investment Trust Association API 🇯🇵 (Best for JP Funds)

**Use Case:** Official NAV data for Japanese mutual funds

**Data Source:** 投信協会 (Investment Trusts Association, Japan)
- Website: https://www.toushin.or.jp/
- Has CSV download for fund NAVs

**Challenge:**
- Need fund code (ISIN) mapping
- Not a real-time API (daily CSV files)
- May require web scraping

**Potential Implementation:**
```python
def fetch_japan_fund_nav(fund_isin: str, date: str):
    """
    Fetch NAV from Investment Trust Association

    Would require:
    1. ISIN mapping: eMAXIS Slim S&P500 → JP90C000J7J5
    2. Web scraping or CSV download
    3. Parse NAV data
    """
    # Placeholder - would need real implementation
    pass
```

**Status:**
- ⚠️ Complex to implement
- ⚠️ Requires ISIN code maintenance
- ✅ Would be most accurate for JP funds

---

## Recommended Implementation Plan

### Phase 1: Basic (Week 1)
```python
class HistoricalPriceService:
    def get_price_history(self, symbol: str, start_date, end_date):
        # Try Tier 1: Yahoo Finance
        if symbol in TICKER_MAP:
            return self.fetch_yahoo_finance(TICKER_MAP[symbol], start_date, end_date)

        # Try Tier 2: Proxy mapping
        if symbol in FUND_TO_INDEX_MAP:
            return self.estimate_via_proxy(symbol, start_date, end_date)

        # Fallback Tier 3: Linear interpolation
        return self.interpolate_from_transactions(symbol, start_date, end_date)
```

**Coverage:**
- ✅ US stocks: Yahoo Finance
- ✅ JP ETFs: Yahoo Finance with ".T" suffix
- ✅ Investment trusts: Proxy indices
- ✅ Fallback: Interpolation

### Phase 2: Enhanced (Future)
- Add caching layer (Redis or DB)
- Add Tier 4: JP mutual fund API
- Add exchange rate history (USD/JPY from Yahoo Finance)

---

## API Selection Matrix

| Asset Type | Primary Source | Fallback | Accuracy |
|------------|----------------|----------|----------|
| US Stocks (PLTR, MU) | Yahoo Finance | Interpolation | 100% |
| US ETFs (QQQ, IYR) | Yahoo Finance | Interpolation | 100% |
| JP ETFs (1326.T, 1542.T) | Yahoo Finance | Interpolation | 95% |
| eMAXIS Slim Funds | Proxy Index (^GSPC, ACWI) | Interpolation | 90-95% |
| Other JP Funds | Proxy Index | Interpolation | 85-90% |
| Unknown Assets | Interpolation | None | 50-60% |

---

## Code Structure

```
backend/app/services/
├── price_fetcher.py          # Main service
│   ├── YahooFinanceFetcher   # Tier 1
│   ├── ProxyIndexEstimator   # Tier 2
│   ├── LinearInterpolator    # Tier 3
│   └── HistoricalPriceService # Coordinator
├── ticker_mappings.py        # Ticker and proxy mappings
└── exchange_rate_service.py  # USD/JPY history
```

---

## Database Schema for Caching

```sql
CREATE TABLE historical_prices (
    id UUID PRIMARY KEY,
    symbol VARCHAR(50),
    date DATE,
    price NUMERIC(18, 6),
    source VARCHAR(20),  -- 'yahoo', 'proxy', 'interpolated'
    created_at TIMESTAMP,
    UNIQUE(symbol, date)
);

CREATE INDEX idx_symbol_date ON historical_prices(symbol, date);
```

---

## API Rate Limit Management

**Yahoo Finance Limits:**
- 2000 requests/hour
- 48,000 requests/day

**Strategy:**
```python
import time
from functools import wraps

def rate_limit(calls_per_hour=2000):
    min_interval = 3600 / calls_per_hour  # seconds between calls
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_hour=2000)
def fetch_yahoo_finance(ticker, start, end):
    # Actual API call
    pass
```

---

## Currency Conversion

For USD-denominated assets, fetch USD/JPY exchange rate history:

```python
def fetch_exchange_rates(start_date, end_date):
    """
    Fetch USD/JPY historical rates from Yahoo Finance
    """
    fx = yf.Ticker("USDJPY=X")
    rates = fx.history(start=start_date, end=end_date)
    return rates[['Close']]
```

---

## Example: Calculate Portfolio Value Time Series

```python
def build_portfolio_value_timeseries(portfolio_id: str):
    """
    Build daily portfolio value from inception to present
    """
    # 1. Get all holdings
    holdings = get_holdings(portfolio_id)

    # 2. Determine date range
    transactions = get_transactions(portfolio_id)
    start_date = min(tx.transaction_date for tx in transactions)
    end_date = datetime.now()

    # 3. Create date range
    dates = pd.date_range(start_date, end_date, freq='D')

    # 4. For each holding, get price history
    portfolio_values = []

    for date in dates:
        total_value = 0

        for holding in holdings:
            # Get quantity held at this date
            qty = get_quantity_at_date(holding.symbol, date, transactions)

            if qty == 0:
                continue

            # Get price at this date
            price = price_service.get_price_history(
                holding.symbol,
                date,
                date
            )

            # Convert to JPY if needed
            if holding.market == 'US':
                fx_rate = get_exchange_rate(date)
                price_jpy = price * fx_rate
            else:
                price_jpy = price

            total_value += qty * price_jpy

        portfolio_values.append({
            'date': date,
            'total_value': total_value
        })

    return pd.DataFrame(portfolio_values)
```

---

## Dependencies to Add

```txt
# requirements.txt
yfinance>=0.2.36           # Yahoo Finance API
scipy>=1.11.0              # Interpolation
requests>=2.31.0           # HTTP requests
redis>=5.0.0               # Caching (optional)
```

---

## Next Steps

**Question for you:**
1. **Should we implement API-based fetching now?** (Tier 1 + Tier 2)
   - Pros: Accurate historical data
   - Cons: External dependency, rate limits

2. **Or start with interpolation only?** (Tier 3)
   - Pros: Simple, no dependencies
   - Cons: Less accurate

3. **Hybrid approach?** Use API where available, interpolate for others
   - Pros: Best of both worlds
   - Cons: More complex

**My recommendation:**
Start with **Hybrid (Tier 1 + Tier 2 + Tier 3 fallback)** because:
- Your portfolio has many US stocks/ETFs (easy with Yahoo Finance)
- Investment trusts can use proxy indices (good accuracy)
- Fallback ensures nothing breaks

Would you like me to implement the Hybrid approach?
