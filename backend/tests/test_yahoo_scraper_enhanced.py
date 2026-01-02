"""
Test the enhanced Yahoo scraper with weekly frequency and calculation start date
"""
from datetime import date, timedelta
from app.services.yahoo_scraper_enhanced import YahooScraperFetcher


def test_weekly_data_0331418A():
    """Test fetching WEEKLY data for fund 0331418A"""
    print("\n" + "=" * 80)
    print("TEST: WEEKLY DATA FOR FUND 0331418A")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Fetch 6 months of weekly data
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    print(f"\nFetching WEEKLY data...")
    df = scraper.fetch(
        ticker="0331418A",
        start_date=start_date,
        end_date=end_date,
        frequency="weekly"  # 週間
    )
    
    if df is not None:
        print(f"\n✅ SUCCESS! Fetched {len(df)} weekly data points")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nLast 5 rows:")
        print(df.tail())
        print(f"\nSummary:")
        print(f"  Period: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"  NAV range: ¥{df['price'].min():.2f} to ¥{df['price'].max():.2f}")
        print(f"  Average: ¥{df['price'].mean():.2f}")
        
        # Check if data is actually weekly (roughly 7 days between points)
        if len(df) > 1:
            avg_gap = (df.index[-1] - df.index[0]).days / len(df)
            print(f"  Avg days between data points: {avg_gap:.1f}")
            if 5 <= avg_gap <= 9:
                print(f"  ✅ Confirmed: Weekly data (avg ~7 days)")
            else:
                print(f"  ⚠️  May not be weekly data")
    else:
        print("❌ No data found")
    
    print("=" * 80)


def test_daily_vs_weekly_comparison():
    """Compare daily vs weekly data for 0331418A"""
    print("\n" + "=" * 80)
    print("TEST: DAILY vs WEEKLY COMPARISON")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=False)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=90)  # 3 months
    
    # Fetch daily
    print("\n1. Fetching DAILY data...")
    daily_df = scraper.fetch("0331418A", start_date, end_date, frequency="daily")
    
    # Fetch weekly
    print("\n2. Fetching WEEKLY data...")
    weekly_df = scraper.fetch("0331418A", start_date, end_date, frequency="weekly")
    
    print("\n" + "-" * 80)
    print("COMPARISON:")
    print("-" * 80)
    
    if daily_df is not None:
        print(f"Daily data:  {len(daily_df)} points")
    else:
        print(f"Daily data:  No data")
    
    if weekly_df is not None:
        print(f"Weekly data: {len(weekly_df)} points")
    else:
        print(f"Weekly data: No data")
    
    if daily_df is not None and weekly_df is not None:
        ratio = len(daily_df) / len(weekly_df) if len(weekly_df) > 0 else 0
        print(f"Ratio:       {ratio:.1f}x (expected ~5-7x for daily vs weekly)")
    
    print("=" * 80)


def test_calc_start_date():
    """Test using calculation start date filter"""
    print("\n" + "=" * 80)
    print("TEST: CALCULATION START DATE FILTER")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Fetch 1 year of data
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    # But only use last 90 days for calculations
    calc_start = end_date - timedelta(days=90)
    
    print(f"\nScenario:")
    print(f"  Fetch all data from: {start_date}")
    print(f"  But calculations start: {calc_start}")
    print(f"  End date: {end_date}")
    
    df = scraper.fetch(
        ticker="0331418A",
        start_date=start_date,
        end_date=end_date,
        frequency="daily",
        calc_start_date=calc_start
    )
    
    if df is not None:
        print(f"\n✅ Got {len(df)} data points after filtering")
        print(f"\nActual date range in DataFrame:")
        print(f"  First: {df.index[0].date()}")
        print(f"  Last:  {df.index[-1].date()}")
        
        days_span = (df.index[-1] - df.index[0]).days
        print(f"  Span:  {days_span} days")
        
        if days_span <= 100:  # Should be ~90 days
            print(f"  ✅ Correctly filtered to ~90 days")
        else:
            print(f"  ⚠️  Span is larger than expected")
    else:
        print("❌ No data found")
    
    print("=" * 80)


def test_lookback_method():
    """Test the convenience lookback method"""
    print("\n" + "=" * 80)
    print("TEST: LOOKBACK METHOD (最近365日)")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Fetch last 365 days of weekly data
    df = scraper.fetch_with_lookback(
        ticker="0331418A",
        end_date=date.today(),
        lookback_days=365,
        frequency="weekly"
    )
    
    if df is not None:
        print(f"\n✅ Got {len(df)} weekly points from last 365 days")
        print(f"\nData summary:")
        print(df.describe())
    else:
        print("❌ No data found")
    
    print("=" * 80)


def test_lookback_with_calc_start():
    """Test lookback + calculation start date (common use case)"""
    print("\n" + "=" * 80)
    print("TEST: LOOKBACK + CALC START (Fetch 2 years, calculate from 1 year)")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Fetch 2 years of data, but only calculate from 1 year ago
    today = date.today()
    one_year_ago = today - timedelta(days=365)
    
    df = scraper.fetch_with_lookback(
        ticker="0331418A",
        end_date=today,
        lookback_days=730,  # 2 years
        frequency="weekly",
        calc_start_date=one_year_ago
    )
    
    if df is not None:
        print(f"\n✅ Got {len(df)} weekly points")
        print(f"   (Fetched 2 years, filtered to 1 year for calculations)")
        print(f"\nDate range:")
        print(f"  From: {df.index[0].date()}")
        print(f"  To:   {df.index[-1].date()}")
        print(f"  Span: {(df.index[-1] - df.index[0]).days} days")
    else:
        print("❌ No data found")
    
    print("=" * 80)


if __name__ == "__main__":
    # Run all tests
    print("\n" + "=" * 80)
    print("ENHANCED YAHOO SCRAPER - COMPREHENSIVE TESTS")
    print("=" * 80)
    
    test_weekly_data_0331418A()
    test_daily_vs_weekly_comparison()
    test_calc_start_date()
    test_lookback_method()
    test_lookback_with_calc_start()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
