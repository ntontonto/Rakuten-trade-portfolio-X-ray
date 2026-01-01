"""
Test script for cache optimization and multi-phase backfill

This script tests:
1. First request: Cache miss → triggers backfill (should take ~15-20 seconds)
2. Database check: Verify full history was cached
3. Second request: Cache hit → instant response (should take <1 second)
"""
import time
from datetime import date, timedelta
from app.db.base import SessionLocal
from app.services.price_cache_service import PriceCacheService

def test_cache_backfill():
    """Test cache with multi-phase backfill"""

    # Test parameters
    symbol = "0331418A"
    ticker = "0331418A"

    # Request 1.5 years of data (realistic for user scenario)
    # This fund only has data since early 2025, so we'll request from 1 year ago
    end_date = date.today()
    start_date = end_date - timedelta(days=400)  # ~1.3 years ago

    print("\n" + "="*80)
    print("CACHE OPTIMIZATION TEST")
    print("="*80)
    print(f"Symbol: {symbol}")
    print(f"Date range: {start_date} to {end_date} ({(end_date - start_date).days} days)")
    print()

    # Get database session
    db = SessionLocal()
    cache_service = PriceCacheService(db)

    # Test 1: First request (cache miss, should trigger backfill)
    print("TEST 1: First request (cache miss, triggers multi-phase backfill)")
    print("-" * 80)
    start_time = time.time()

    data1, source1 = cache_service.get_price_history(
        symbol=symbol,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        source='scraped',
        force_refresh=False
    )

    elapsed1 = time.time() - start_time

    if data1 is not None:
        print(f"\n✅ First request completed:")
        print(f"   - Rows returned: {len(data1)}")
        print(f"   - Date range: {data1.index[0].date()} to {data1.index[-1].date()}")
        print(f"   - Source: {source1}")
        print(f"   - Time taken: {elapsed1:.2f} seconds")
    else:
        print(f"\n❌ First request failed!")
        print(f"   - Time taken: {elapsed1:.2f} seconds")

    # Check database cache
    print("\n" + "-" * 80)
    print("DATABASE CHECK: Verify cached data")
    print("-" * 80)

    from app.db.models.price_history import PriceHistory
    from sqlalchemy import func, and_

    cache_stats = db.query(
        func.min(PriceHistory.date).label('first_date'),
        func.max(PriceHistory.date).label('last_date'),
        func.count(PriceHistory.id).label('row_count')
    ).filter(
        and_(
            PriceHistory.symbol == symbol,
            PriceHistory.source == 'scraped'
        )
    ).first()

    if cache_stats and cache_stats.row_count > 0:
        print(f"\n✅ Database cache populated:")
        print(f"   - First date: {cache_stats.first_date}")
        print(f"   - Last date: {cache_stats.last_date}")
        print(f"   - Total rows: {cache_stats.row_count}")
        days_cached = (cache_stats.last_date - cache_stats.first_date).days
        print(f"   - Days covered: {days_cached}")
    else:
        print(f"\n⚠️ No data in cache!")

    # Test 2: Second request (cache hit, should be instant)
    print("\n" + "="*80)
    print("TEST 2: Second request (cache hit, should be instant)")
    print("-" * 80)

    time.sleep(1)  # Small delay to ensure cache is committed

    start_time = time.time()

    data2, source2 = cache_service.get_price_history(
        symbol=symbol,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        source='scraped',
        force_refresh=False
    )

    elapsed2 = time.time() - start_time

    if data2 is not None:
        print(f"\n✅ Second request completed:")
        print(f"   - Rows returned: {len(data2)}")
        print(f"   - Date range: {data2.index[0].date()} to {data2.index[-1].date()}")
        print(f"   - Source: {source2}")
        print(f"   - Time taken: {elapsed2:.2f} seconds")

        if source2 == 'cache':
            print(f"   - ✅ Using cache! (not scraping)")
        else:
            print(f"   - ⚠️ Not using cache (re-scraping)")
    else:
        print(f"\n❌ Second request failed!")
        print(f"   - Time taken: {elapsed2:.2f} seconds")

    # Performance comparison
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print(f"First request (cache miss):  {elapsed1:.2f} seconds")
    print(f"Second request (cache hit):  {elapsed2:.2f} seconds")

    if elapsed2 < 1 and source2 == 'cache':
        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else float('inf')
        print(f"\n✅ SUCCESS! Cache speedup: {speedup:.1f}x faster")
        print(f"✅ Response time improved from {elapsed1:.2f}s to {elapsed2:.2f}s")
    else:
        print(f"\n⚠️ Cache may not be working optimally")
        print(f"   Expected: <1 second with source='cache'")
        print(f"   Actual: {elapsed2:.2f} seconds with source='{source2}'")

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    success_count = 0
    total_tests = 4

    # Check 1: First request returned data
    if data1 is not None and len(data1) > 0:
        print("✅ First request returned data")
        success_count += 1
    else:
        print("❌ First request failed")

    # Check 2: Data was cached in database
    if cache_stats and cache_stats.row_count > 0:
        print(f"✅ Data cached in database ({cache_stats.row_count} rows)")
        success_count += 1
    else:
        print("❌ Data not cached in database")

    # Check 3: Second request used cache
    if source2 == 'cache':
        print("✅ Second request used cache (not scraping)")
        success_count += 1
    else:
        print(f"❌ Second request did not use cache (source: {source2})")

    # Check 4: Cache response was fast
    if elapsed2 < 1:
        print(f"✅ Cache response was fast ({elapsed2:.2f}s < 1s)")
        success_count += 1
    else:
        print(f"❌ Cache response was slow ({elapsed2:.2f}s >= 1s)")

    print("\n" + "-" * 80)
    print(f"RESULT: {success_count}/{total_tests} tests passed")
    print("="*80 + "\n")

    db.close()

    return success_count == total_tests


if __name__ == "__main__":
    success = test_cache_backfill()
    exit(0 if success else 1)
