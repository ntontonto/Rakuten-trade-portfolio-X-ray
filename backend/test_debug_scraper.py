"""
Debug test to see what's in the table
"""
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.yahoo_scraper_enhanced import YahooScraperFetcher


def test_without_date_filter():
    """
    Test without date filtering to see what data is available
    """
    print("\n" + "=" * 80)
    print("DEBUG TEST: Check table content")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Use very wide date range
    ticker = "0331418A"
    
    end_date = date.today()
    start_date = date(2020, 1, 1)  # Very old start date
    
    print(f"\nTicker: {ticker}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Mode: Weekly\n")
    
    df = scraper.fetch(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        frequency="weekly"
    )
    
    if df is not None and len(df) > 0:
        print(f"\n✅ Got {len(df)} records")
        print(f"\nFirst few:")
        print(df.head(10))
        print(f"\nLast few:")
        print(df.tail(10))
    else:
        print("❌ No data")


if __name__ == "__main__":
    test_without_date_filter()
