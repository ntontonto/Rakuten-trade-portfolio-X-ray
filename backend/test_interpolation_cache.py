"""
Test that interpolated data gets cached
"""
from datetime import date
from app.db.base import SessionLocal
from app.services.price_fetcher import HistoricalPriceService

def test_interpolation_caching():
    """Test requesting old data that requires interpolation"""

    print("\n" + "="*80)
    print("INTERPOLATION CACHING TEST")
    print("="*80)

    # Use a fund that only has 2025 scraped data
    # Request 2020-2024 data (should trigger interpolation)
    symbol = "eMAXIS Slim 米国株式(S&P500)"  # Actual symbol in transactions table
    portfolio_id = "e652d6b8-4af2-4ef4-baf9-45262b76a449"  # Your portfolio ID

    db = SessionLocal()
    price_service = HistoricalPriceService(db)

    # Request OLD data (before scraped data is available)
    start_date = date(2020, 12, 2)
    end_date = date(2024, 12, 31)

    print(f"\nRequesting data for {symbol}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Expected: Should use interpolation (no scraped data for this period)")
    print()

    # First request (should calculate interpolation and cache it)
    print("=" * 80)
    print("FIRST REQUEST (should calculate & cache interpolation)")
    print("=" * 80)

    data1, source1 = price_service.get_price_history(
        symbol=symbol,
        name="eMAXIS Slim 米国株式(S&P500)",
        start_date=start_date,
        end_date=end_date,
        portfolio_id=portfolio_id
    )

    if data1 is not None:
        print(f"\n✅ First request returned:")
        print(f"   Rows: {len(data1)}")
        print(f"   Date range: {data1.index[0].date()} to {data1.index[-1].date()}")
        print(f"   Source: {source1}")
    else:
        print(f"\n❌ First request failed")
        db.close()
        return False

    # Check database for interpolated cache
    print("\n" + "=" * 80)
    print("DATABASE CHECK (should have interpolated cache now)")
    print("=" * 80)

    from app.db.models.price_history import PriceHistory
    from sqlalchemy import func, and_

    interpolated_cache = db.query(
        func.count(PriceHistory.id).label('row_count'),
        func.min(PriceHistory.date).label('first_date'),
        func.max(PriceHistory.date).label('last_date')
    ).filter(
        and_(
            PriceHistory.symbol == symbol,
            PriceHistory.source == 'interpolated'
        )
    ).first()

    if interpolated_cache and interpolated_cache.row_count > 0:
        print(f"\n✅ Interpolated data cached in database:")
        print(f"   Rows: {interpolated_cache.row_count}")
        print(f"   Date range: {interpolated_cache.first_date} to {interpolated_cache.last_date}")
    else:
        print(f"\n⚠️ No interpolated data in cache")

    # Second request (should use cached interpolation)
    print("\n" + "=" * 80)
    print("SECOND REQUEST (should use cached interpolation - FAST!)")
    print("=" * 80)

    import time
    start_time = time.time()

    data2, source2 = price_service.get_price_history(
        symbol=symbol,
        name="eMAXIS Slim 米国株式(S&P500)",
        start_date=start_date,
        end_date=end_date,
        portfolio_id=portfolio_id
    )

    elapsed = time.time() - start_time

    if data2 is not None:
        print(f"\n✅ Second request returned:")
        print(f"   Rows: {len(data2)}")
        print(f"   Source: {source2}")
        print(f"   Time: {elapsed:.3f} seconds")

        if elapsed < 0.5:
            print(f"\n✅ SUCCESS! Cache made it fast (<0.5s)")
        else:
            print(f"\n⚠️ Slower than expected (should be <0.5s for cached data)")
    else:
        print(f"\n❌ Second request failed")

    db.close()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_interpolation_caching()
