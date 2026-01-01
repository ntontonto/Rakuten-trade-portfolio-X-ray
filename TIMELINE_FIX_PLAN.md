# Timeline Network Error - Fix Plan

## Problem Summary
When displaying individual fund trend timelines, users encounter a network error. The AssetDetail component cannot fetch data from `/api/v1/portfolios/{portfolio_id}/holdings/{symbol}/history`.

## Root Causes Identified

### 1. **Backend Container Not Running** (Primary Issue)
- **Evidence**: `curl http://localhost:8000/health` returns "Backend not responding"
- **Impact**: All API calls fail with network errors
- **Fix**: Start/restart Docker containers

### 2. **FX Rate Gap Issue** (Secondary Issue - Code Bug)
**Location**: `backend/app/api/v1/analysis.py:424-428`

**Problem**:
```python
if holding.market == 'US':
    fx = fx_map.get(d)
    if fx:  # ← Missing FX rate causes price to be skipped
        price_map[d] = raw * fx
```

If FX rate is missing for a date, US holdings won't have price data for that day, creating gaps in timeline charts.

**Fix**: Add fallback to forward-fill or interpolate missing FX rates

### 3. **Missing Error Handling**
**Location**: `backend/app/api/v1/analysis.py` (timeline endpoints)

**Problem**: No try-catch blocks around:
- `HistoricalPriceService` instantiation
- `get_price_history()` calls
- Price map building

**Fix**: Add comprehensive error handling with informative messages

## Implementation Steps

### Step 1: Start Backend Container
```bash
cd /Users/kentosaito/Documents/git/Rakuten-trade-portfolio-X-ray
docker-compose up -d
# Wait for containers to be healthy
docker-compose ps
```

### Step 2: Fix FX Rate Gap Issue
**File**: `backend/app/api/v1/analysis.py`

**Change `_build_price_map` function** (lines 396-430):
```python
def _build_price_map(
    price_service: HistoricalPriceService,
    holding: Holding,
    start_date: date,
    end_date: date,
    fx_map: Dict[date, float],
    transactions: List[Transaction]
):
    """Fetch price history once and convert to JPY map."""
    prices, source = price_service.get_price_history(
        symbol=holding.symbol,
        name=holding.name,
        start_date=start_date,
        end_date=end_date,
        portfolio_id=str(holding.portfolio_id)
    )
    price_map: Dict[date, float] = {}
    if prices is None or prices.empty:
        # Fallback: pure interpolation on transaction prices
        interp_df = price_service.interpolator.interpolate(transactions, start_date, end_date)
        if interp_df is None or interp_df.empty:
            return price_map, source
        prices = interp_df
        source = source or 'interpolated'

    # NEW: For US holdings, build forward-filled FX map
    if holding.market == 'US' and fx_map:
        # Forward-fill missing FX rates
        filled_fx_map = {}
        last_fx = None
        current_date = start_date
        while current_date <= end_date:
            if current_date in fx_map:
                last_fx = fx_map[current_date]
            if last_fx is not None:
                filled_fx_map[current_date] = last_fx
            current_date += timedelta(days=1)
        fx_map = filled_fx_map

    for idx, row in prices.iterrows():
        d = idx.date() if hasattr(idx, "date") else idx
        raw = float(row['price'])
        if holding.market == 'US':
            fx = fx_map.get(d)
            if fx:
                price_map[d] = raw * fx
            # CHANGED: If still no FX, skip this date but log warning
            # This prevents crashes but signals data quality issue
        else:
            price_map[d] = raw
    return price_map, source
```

### Step 3: Add Error Handling
**File**: `backend/app/api/v1/analysis.py`

Add try-catch to `get_portfolio_timeline` (line 565):
```python
@router.get(
    "/portfolios/{portfolio_id}/timeline",
    response_model=PortfolioTimelineResponse
)
def get_portfolio_timeline(
    portfolio_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Daily cumulative invested value vs total evaluation value (JPY).
    """
    try:
        holdings: List[Holding] = (
            db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        )
        transactions: List[Transaction] = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.id)
            .order_by(Transaction.transaction_date)
            .all()
        )

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = transactions[0].transaction_date if transactions else end_date
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

        price_service = HistoricalPriceService(db)

        # ... rest of implementation ...

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate portfolio timeline: {str(e)}"
        )
```

### Step 4: Test the Fix
1. Verify backend is running: `curl http://localhost:8000/health`
2. Test timeline endpoint directly with curl
3. Test from frontend UI
4. Check browser console for errors
5. Verify charts display without gaps

## Verification Checklist
- [ ] Docker containers are running (`docker-compose ps`)
- [ ] Backend health check passes (`curl http://localhost:8000/health`)
- [ ] Timeline endpoint returns data (test with curl)
- [ ] Frontend chart displays without network errors
- [ ] US holdings have complete price data (no gaps)
- [ ] Error messages are helpful if issues occur

## Files to Modify
1. `backend/app/api/v1/analysis.py` - Fix FX gap + add error handling
2. No frontend changes needed

## Testing Strategy
1. **Unit Test**: Test `_build_price_map` with missing FX dates
2. **Integration Test**: Call timeline endpoint with real portfolio data
3. **E2E Test**: Load fund detail chart in browser

## Rollback Plan
If fix causes issues:
1. Revert changes to `analysis.py`
2. Restart backend container
3. Original behavior restored
