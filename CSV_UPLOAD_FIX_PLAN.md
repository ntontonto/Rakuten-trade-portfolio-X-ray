# CSV Upload Double-Counting Fix Plan

## Problem Analysis

### Current Behavior (Based on Actual Code)

**When uploading CSV files multiple times:**

1. **Portfolio Reuse** (`upload.py:84-89`)
   ```python
   existing_portfolio = db.query(Portfolio).first()
   if existing_portfolio:
       portfolio = existing_portfolio  # Reuses existing portfolio
   ```

2. **Transactions APPENDED** (`upload.py:144-157`)
   ```python
   for tx_data in parsed['data']:
       transaction = Transaction(...)
       db.add(transaction)  # Always adds, never deletes old ones
   ```
   - **NO deletion of existing transactions**
   - Each CSV upload **ADDS** new transactions to the database

3. **Holdings UPDATED** (`portfolio_aggregator.py:122-142`)
   ```python
   existing = db.query(Holding).filter(...).first()
   if existing:
       holding = existing  # Updates existing holding
   ```
   - Holdings are correctly updated, not duplicated

4. **Timeline Calculation** (`analysis.py:651-653`)
   ```python
   for tx in transactions:
       if tx.side == 'BUY':
           invested_by_date[tx.transaction_date] += float(tx.amount_jpy)
   ```
   - Sums **ALL** transactions in the database
   - **Includes duplicates** from multiple uploads

### Result: 累計投資額 Double-Counting

**Example:**
- **First upload**: CSV with 100 transactions → Creates 100 transactions in DB
- **Second upload**: Same CSV → Creates ANOTHER 100 transactions (duplicates!)
- **Timeline shows**: 累計投資額 = 2x the actual amount (double-counted)

**Why holdings are OK but timeline is wrong:**
- Holdings are **updated** (correct current state)
- Transactions are **appended** (historical duplicates)
- Timeline sums all transactions → includes duplicates

---

## Root Cause

**Location**: `backend/app/api/v1/upload.py:144-173`

**Missing Logic**: No code to delete existing transactions before inserting new ones.

**Evidence from code search**:
```bash
grep -i "delete.*transaction" upload.py  # No matches
grep -i "Transaction.*delete" upload.py  # No matches
grep -i "clear" upload.py                # No matches
```

---

## User's Expected Behavior

1. ✅ Upload CSV → **REPLACE** all portfolio data (transactions + holdings)
2. ✅ Keep `price_history` table intact (for performance/caching)
3. ✅ No double-counting in 累計投資額
4. ✅ Portfolio timeline data cached in DB (reduce latency)

---

## Fix Plan

### Option 1: Delete Transactions + Holdings on Upload (Recommended)

**Implementation Location**: `backend/app/api/v1/upload.py`

**Add BEFORE line 104** (before processing files):

```python
# NEW CODE: Clear existing data when uploading to existing portfolio
if portfolio_id or existing_portfolio:
    pid = portfolio_id if portfolio_id else existing_portfolio.id

    # Delete existing holdings (will recalculate from transactions)
    deleted_holdings = db.query(Holding).filter(Holding.portfolio_id == pid).delete()

    # Delete existing transactions (will recreate from CSV)
    deleted_transactions = db.query(Transaction).filter(Transaction.portfolio_id == pid).delete()

    db.commit()

    print(f"🗑️  Cleared existing data: {deleted_transactions} transactions, {deleted_holdings} holdings")
```

**What this does**:
1. When uploading to existing portfolio, delete all transactions and holdings first
2. Then process CSV and create fresh transactions/holdings
3. **Does NOT delete**:
   - Portfolio metadata (keeps portfolio ID)
   - Price history cache (keeps performance)
4. Result: CSV upload becomes a "replace all" operation

**Files Modified**:
- `backend/app/api/v1/upload.py` (add deletion logic)

**Database Impact**:
- Transactions table: DELETE + INSERT (same count)
- Holdings table: DELETE + INSERT (same count)
- Portfolio table: NO CHANGE
- Price_history table: NO CHANGE (keeps cache)

---

### Option 2: Upsert Transactions (More Complex, Not Recommended)

**Why not this approach:**
- Requires unique constraint on (portfolio_id, transaction_date, symbol, side, quantity)
- Hard to determine uniqueness for transactions (user might legitimately buy same stock twice in one day)
- More complex logic
- Doesn't solve the fundamental issue of "CSV should replace, not append"

---

## Implementation Details

### Step 1: Add Deletion Logic to Upload Endpoint

**File**: `backend/app/api/v1/upload.py`

**Insert after line 97** (after portfolio creation/reuse logic):

```python
# Clear existing data for idempotent uploads
if portfolio_id:
    # Portfolio ID was provided by user - clear its data
    print(f"🗑️  Clearing existing data for portfolio {portfolio_id}")
    db.query(Holding).filter(Holding.portfolio_id == portfolio_id).delete()
    db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).delete()
    db.commit()
```

### Step 2: Add Clear Warning Message in Response

**File**: `backend/app/api/v1/upload.py`

**Modify return statement** (line 193-202):

```python
return {
    "success": True,
    "message": f"Processed {len(files)} file(s) successfully. All previous data replaced.",
    "portfolio_id": str(portfolio_id),
    "files_processed": parsed_files,
    "transactions_imported": len(all_transactions),
    "holdings_created": len(holdings),
    "balance_merge": merge_stats,
    "summary": summary,
    "data_replaced": True  # NEW: Indicate data was replaced
}
```

### Step 3: No Frontend Changes Needed

The frontend already handles the response correctly. No changes required.

---

## Testing Plan

### Test 1: Initial Upload
```bash
# Upload CSV first time
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
     -F "files=@transaction_history.csv"

# Expected: Creates portfolio, transactions, holdings
# Check: 累計投資額 = X JPY
```

### Test 2: Duplicate Upload (Current Bug)
```bash
# Upload SAME CSV second time
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
     -F "files=@transaction_history.csv"

# BEFORE FIX: 累計投資額 = 2X JPY (double-counted!)
# AFTER FIX: 累計投資額 = X JPY (correct, data replaced)
```

### Test 3: Timeline Verification
```bash
# Get timeline
curl "http://localhost:8000/api/v1/portfolios/{portfolio_id}/timeline?start_date=2024-01-01&end_date=2024-12-31"

# Expected: invested_cumulative_jpy shows correct single-counted values
```

### Test 4: Holdings Verification
```bash
# Get holdings
curl "http://localhost:8000/api/v1/portfolios/{portfolio_id}/holdings"

# Expected: Quantities and values are correct (should be same before/after fix since holdings were already updating correctly)
```

---

## Edge Cases

### Case 1: Portfolio Has Transactions from Other Sources
**Current Behavior**: If transactions were created via API (not CSV upload), they would be deleted

**Solution**: This is acceptable because:
- Application currently only supports CSV upload as transaction source
- If needed later, add a `source` field to Transaction model to distinguish CSV vs API transactions

### Case 2: Multiple Portfolios
**Current Behavior**: Code reuses first portfolio found (`db.query(Portfolio).first()`)

**Solution**: Already acceptable because:
- This is intentional for single-portfolio applications
- If user wants multiple portfolios, they can provide `portfolio_id` parameter

### Case 3: Price History Cache
**Behavior**: NOT deleted (intentional)

**Reasoning**:
- Price history is expensive to fetch (scraping, API calls)
- Reusing same portfolio means same assets → same price data needed
- Cache improves performance on re-upload

---

## Rollback Plan

If fix causes issues:

```bash
cd /Users/kentosaito/Documents/git/Rakuten-trade-portfolio-X-ray
git checkout backend/app/api/v1/upload.py
docker-compose restart backend
```

---

## Files to Modify

1. **backend/app/api/v1/upload.py** (PRIMARY)
   - Add deletion logic after line 97
   - Update response message at line 194

---

## Summary

**Current Issue**:
- ✅ Identified: Transactions are appended, not replaced
- ✅ Root cause: No deletion logic in upload endpoint
- ✅ Impact: 累計投資額 double-counting on re-upload

**Proposed Fix**:
- ✅ Simple: Add 2-3 lines to delete transactions + holdings before upload
- ✅ Safe: Only deletes data for the specific portfolio being updated
- ✅ Preserves: Portfolio metadata and price history cache
- ✅ Result: CSV upload becomes idempotent (upload same file multiple times = same result)

**Implementation Effort**:
- 1 file to modify
- ~10 lines of code
- No database migration needed
- No frontend changes needed

---

## Approval Required

Please review this plan and confirm:
1. ✅ Delete transactions + holdings on CSV upload (Option 1)
2. ✅ Keep portfolio metadata intact
3. ✅ Keep price_history cache intact
4. ✅ No frontend changes needed

Once approved, I will implement the fix.
