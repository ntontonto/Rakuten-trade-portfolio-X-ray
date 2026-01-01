"""
Test fetching data from 2021 December with date range setting
"""
from datetime import date
from app.services.yahoo_scraper_enhanced import YahooScraperFetcher

def test_2021_data():
    """Test if date range setting can fetch 2021 data"""

    ticker = "03311187"
    start_date = date(2021, 12, 1)
    end_date = date(2021, 12, 31)

    print("\n" + "="*80)
    print("2021 DATA FETCH TEST (with date range setting)")
    print("="*80)
    print(f"Ticker: {ticker}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    print("This test will:")
    print("1. Load Yahoo Finance page")
    print("2. Set custom date range (2021/12/01 to 2021/12/31)")
    print("3. Click 表示 (Display) button")
    print("4. Fetch historical data")
    print()

    scraper = YahooScraperFetcher(headless=True, debug=True)  # Enable debug mode

    print("Fetching data...")
    try:
        df = scraper.fetch(ticker, start_date, end_date, frequency='daily')
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        df = None

    print("\n" + "="*80)
    print("RESULT")
    print("="*80)

    if df is not None and len(df) > 0:
        print(f"✅ SUCCESS! Fetched {len(df)} rows")
        print(f"   Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"\n   Sample data:")
        for i, (idx, row) in enumerate(df.head(5).iterrows()):
            price = row.get('price', 'N/A')
            nav = row.get('nav', 'N/A')
            print(f"     {idx.date()}: price={price}, nav={nav}")

        if df.index[0].date().year == 2021:
            print(f"\n✅ Date range setting works! Got 2021 data!")
            return True
        else:
            print(f"\n⚠️ Got data but not from 2021. Earliest: {df.index[0].date()}")
            return False
    else:
        print(f"❌ No data returned")
        return False

if __name__ == "__main__":
    success = test_2021_data()
    exit(0 if success else 1)
