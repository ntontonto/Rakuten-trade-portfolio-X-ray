"""
Test S&P500 fund mapping and price fetching

This test verifies:
1. Alias resolution works correctly
2. Price data can be scraped (not interpolated)
"""
from datetime import date, timedelta
from app.services.alias_resolver import resolve_alias
from app.db.base import SessionLocal
from app.services.price_cache_service import PriceCacheService

def test_sp500_mapping():
    """Test S&P500 fund ticker mapping"""

    print("\n" + "="*80)
    print("S&P500 FUND MAPPING TEST")
    print("="*80)

    # Test 1: Alias resolution
    print("\nTEST 1: Alias Resolution")
    print("-" * 80)

    symbol = "eMAXIS Slim 米国株式(S&P500)"
    name = "eMAXIS Slim 米国株式(S&P500)"

    resolved_symbol, resolved_name = resolve_alias(symbol, name)

    print(f"Input symbol: {symbol}")
    print(f"Input name:   {name}")
    print(f"\nResolved symbol: {resolved_symbol}")
    print(f"Resolved name:   {resolved_name}")

    if resolved_symbol == "03311187":
        print("\n✅ Alias resolution works! Symbol resolved to ticker: 03311187")
    else:
        print(f"\n❌ Alias resolution failed! Expected '03311187', got '{resolved_symbol}'")
        return False

    # Test 2: Price fetching (small range to test quickly)
    print("\n" + "="*80)
    print("TEST 2: Price Data Fetching")
    print("-" * 80)

    db = SessionLocal()
    cache_service = PriceCacheService(db)

    # Request last 30 days only (quick test)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    print(f"Fetching data for ticker: {resolved_symbol}")
    print(f"Date range: {start_date} to {end_date} (30 days)")
    print()

    try:
        data, source = cache_service.get_price_history(
            symbol=resolved_symbol,
            ticker=resolved_symbol,
            start_date=start_date,
            end_date=end_date,
            source='scraped',
            force_refresh=False
        )

        if data is not None and len(data) > 0:
            print(f"\n✅ Price data fetched successfully!")
            print(f"   - Rows: {len(data)}")
            print(f"   - Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print(f"   - Source: {source}")

            # Show sample data
            print(f"\n   Sample prices:")
            for i, (idx, row) in enumerate(data.head(3).iterrows()):
                price = row.get('price', 'N/A')
                nav = row.get('nav', 'N/A')
                print(f"     {idx.date()}: price={price}, nav={nav}")

            if source == 'scraped' or source == 'cache':
                print(f"\n✅ Using real scraped data (not interpolation)!")
                success = True
            else:
                print(f"\n⚠️ Data source is '{source}' (expected 'scraped' or 'cache')")
                success = False
        else:
            print(f"\n❌ No data returned!")
            print(f"   - Source: {source}")
            success = False

    except Exception as e:
        print(f"\n❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        success = False
    finally:
        db.close()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    if success:
        print("✅ All tests passed!")
        print("✅ S&P500 fund mapping is working correctly")
        print("✅ Real price data can be fetched (no interpolation needed)")
    else:
        print("❌ Some tests failed - check output above")

    print("="*80 + "\n")

    return success


if __name__ == "__main__":
    success = test_sp500_mapping()
    exit(0 if success else 1)
