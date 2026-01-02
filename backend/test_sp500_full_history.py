"""
Test S&P500 full history backfill from first purchase date
"""
from datetime import date
from app.db.base import SessionLocal
from app.services.price_cache_service import PriceCacheService

def test_full_history():
    """Test fetching full 5-year history"""

    symbol = "03311187"
    ticker = "03311187"

    # Your actual transaction dates
    start_date = date(2020, 12, 2)  # First purchase
    end_date = date.today()

    print("\n" + "="*80)
    print("S&P500 FULL HISTORY TEST")
    print("="*80)
    print(f"Symbol: {symbol}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Days requested: {(end_date - start_date).days}")
    print()

    db = SessionLocal()
    cache_service = PriceCacheService(db)

    # Force refresh to trigger backfill
    print("Requesting full history with force_refresh=True...")
    print()

    data, source = cache_service.get_price_history(
        symbol=symbol,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        source='scraped',
        force_refresh=True  # Force backfill
    )

    print("\n" + "="*80)
    print("RESULT")
    print("="*80)

    if data is not None and len(data) > 0:
        print(f"✅ Data fetched:")
        print(f"   Rows: {len(data)}")
        print(f"   First date: {data.index[0].date()}")
        print(f"   Last date: {data.index[-1].date()}")
        print(f"   Source: {source}")

        days_covered = (data.index[-1].date() - data.index[0].date()).days
        print(f"   Days covered: {days_covered}")

        if data.index[0].date() <= date(2021, 1, 1):
            print(f"\n✅ SUCCESS! Got historical data from {data.index[0].date()}")
        else:
            print(f"\n⚠️ Missing old data. Earliest: {data.index[0].date()} (expected ~2020-12)")
    else:
        print(f"❌ No data returned")

    db.close()

if __name__ == "__main__":
    test_full_history()
