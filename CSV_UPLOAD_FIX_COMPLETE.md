# CSV Upload Double-Counting - Fix Complete ✅

## Summary

Fixed the issue where uploading the same CSV file multiple times caused 累計投資額 (cumulative invested amount) to be double-counted in the portfolio timeline.

---

## Changes Made

### File: `backend/app/api/v1/upload.py`

#### 1. Added Holding Import (Line 13)
```python
from app.db.models import Portfolio, Transaction, Holding
```

#### 2. Added Data Deletion Logic (Lines 99-110)
```python
# Clear existing data for idempotent uploads (replace, not append)
if portfolio_id:
    # Delete existing holdings (will be recalculated from transactions)
    deleted_holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).delete()

    # Delete existing transactions (will be recreated from CSV)
    deleted_transactions = db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).delete()

    db.commit()

    if deleted_transactions > 0 or deleted_holdings > 0:
        print(f"🗑️  Cleared existing data: {deleted_transactions} transactions, {deleted_holdings} holdings")
```

**What This Does:**
- Before processing CSV files, deletes all existing transactions and holdings for the portfolio
- Ensures CSV upload is **replace** operation, not **append**
- Keeps portfolio metadata and price_history cache intact

#### 3. Updated Response Message (Lines 206-218)
```python
# Determine if data was replaced or created fresh
data_replaced = deleted_transactions > 0 or deleted_holdings > 0 if 'deleted_transactions' in locals() else False

return {
    "success": True,
    "message": f"Processed {len(files)} file(s) successfully. {'All previous data replaced.' if data_replaced else 'New portfolio created.'}",
    # ... other fields ...
    "data_replaced": data_replaced
}
```

**What This Does:**
- Informs user whether data was replaced or newly created
- Adds `data_replaced` flag to API response

---

## How It Works Now

### Before Fix (Bug):
1. **First upload**: CSV → Creates 100 transactions in DB
2. **Second upload**: Same CSV → Creates ANOTHER 100 transactions (200 total!)
3. **Timeline**: 累計投資額 = 2x actual amount ❌

### After Fix (Correct):
1. **First upload**: CSV → Creates 100 transactions in DB
2. **Second upload**: Same CSV → **Deletes** 100 old transactions → Creates 100 new transactions (100 total ✅)
3. **Timeline**: 累計投資額 = correct amount ✅

---

## What Gets Deleted vs Preserved

### Deleted (On Each Upload):
- ✅ **Transactions** - Recreated from CSV
- ✅ **Holdings** - Recalculated from new transactions

### Preserved:
- ✅ **Portfolio** - Same portfolio ID, metadata kept
- ✅ **Price History Cache** - Performance optimization, not touched

---

## Testing Instructions

### Prerequisite: Restart Backend
```bash
cd /Users/kentosaito/Documents/git/Rakuten-trade-portfolio-X-ray
docker-compose restart backend

# Wait for backend to start
docker-compose logs backend --follow
# Wait until you see: "Application startup complete"
```

### Test 1: Initial Upload
```bash
# Upload CSV first time
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
     -F "files=@inputs/assetbalance(all)_*.csv" \
     -F "files=@inputs/tradehistory(US)_*.csv"

# Expected response:
{
  "success": true,
  "message": "Processed 2 file(s) successfully. New portfolio created.",
  "data_replaced": false,
  "transactions_imported": 100,
  ...
}
```

### Test 2: Get Timeline (First Upload)
```bash
# Get portfolio ID from upload response, then:
curl "http://localhost:8000/api/v1/portfolios/{portfolio_id}/timeline?start_date=2024-01-01&end_date=2024-12-31"

# Note the final invested_cumulative_jpy value
# Example: 1,000,000 JPY
```

### Test 3: Duplicate Upload (Main Test)
```bash
# Upload EXACT SAME CSV files again
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
     -F "files=@inputs/assetbalance(all)_*.csv" \
     -F "files=@inputs/tradehistory(US)_*.csv"

# Expected response:
{
  "success": true,
  "message": "Processed 2 file(s) successfully. All previous data replaced.",
  "data_replaced": true,
  "transactions_imported": 100,  # ← Same count as first upload
  ...
}
```

### Test 4: Verify Timeline (After Duplicate Upload)
```bash
# Get timeline again
curl "http://localhost:8000/api/v1/portfolios/{portfolio_id}/timeline?start_date=2024-01-01&end_date=2024-12-31"

# Expected: invested_cumulative_jpy should be SAME as Test 2
# Example: 1,000,000 JPY (NOT 2,000,000 JPY!)
```

### Test 5: Frontend Test
1. Open browser to http://localhost:5173
2. Upload CSV files via UI
3. Check 累計投資額 in timeline chart (note the value)
4. Upload SAME CSV files again
5. Check 累計投資額 again
6. **Expected**: Same value as step 3 (not doubled!)

---

## Backend Logs to Check

After uploading, check backend logs:

```bash
docker-compose logs backend --tail=20
```

**First Upload (New Portfolio):**
```
✨ Created new portfolio: 12345678-1234-1234-1234-123456789abc
```

**Second Upload (Data Replacement):**
```
♻️ Reusing existing portfolio: 12345678-1234-1234-1234-123456789abc
🗑️  Cleared existing data: 100 transactions, 5 holdings
```

---

## Database Verification (Optional)

If you want to verify at database level:

```bash
# Connect to PostgreSQL
docker exec -it portfolio-db psql -U portfolio_user -d portfolio_db

# Check transaction count
SELECT COUNT(*) FROM transactions;

# Upload CSV → Count increases
# Upload SAME CSV → Count stays SAME (replaced, not doubled!)

# Exit
\q
```

---

## Edge Cases Handled

### Case 1: Multiple Portfolios
**Behavior**: Each portfolio's data is replaced independently
**Test**: Upload with different `portfolio_id` parameter

### Case 2: Price History Preserved
**Behavior**: Deleting transactions doesn't delete price_history cache
**Test**: Check `price_history` table count before/after upload (should stay same or increase, never decrease)

### Case 3: No Previous Data
**Behavior**: First upload doesn't try to delete (nothing to delete)
**Test**: Fresh database → Upload → No errors

---

## Rollback Instructions

If you need to revert this fix:

```bash
cd /Users/kentosaito/Documents/git/Rakuten-trade-portfolio-X-ray
git checkout backend/app/api/v1/upload.py
docker-compose restart backend
```

---

## Files Modified

1. **backend/app/api/v1/upload.py**
   - Line 13: Added `Holding` import
   - Lines 99-110: Added deletion logic
   - Lines 206-218: Updated response message

**No other files modified:**
- ✅ No database migration needed
- ✅ No frontend changes needed
- ✅ No other backend files changed

---

## Success Criteria

- [x] Python syntax verified (py_compile passed)
- [x] Deletion logic implemented
- [x] Response message updated
- [ ] Backend restarted (USER ACTION)
- [ ] Initial upload tested (USER ACTION)
- [ ] Duplicate upload tested (USER ACTION)
- [ ] Timeline verified (USER ACTION)

---

## What's Next

1. **Restart backend** to apply changes:
   ```bash
   docker-compose restart backend
   ```

2. **Test the fix** using instructions above

3. **Verify** that 累計投資額 is not double-counted on re-upload

4. If any issues occur, check:
   - Backend logs: `docker-compose logs backend`
   - Response message for `data_replaced: true`
   - Database transaction count

---

## Notes

- This fix makes CSV upload **idempotent** (uploading same file multiple times = same result)
- Portfolio ID remains stable across uploads
- Price history cache improves performance on subsequent uploads
- No breaking changes to API or database schema
