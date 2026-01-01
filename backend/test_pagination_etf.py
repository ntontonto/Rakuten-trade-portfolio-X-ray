"""
Test to verify pagination actually works with a fund that has more history
"""
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.yahoo_scraper_enhanced import YahooScraperFetcher


def test_pagination_with_longer_period():
    """
    Test with a longer time period to trigger actual pagination
    Using a popular ETF that should have lots of historical data
    """
    print("\n" + "=" * 80)
    print("PAGINATION TEST: Fetching 3 years of daily data")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Use a popular ETF that definitely has multi-page history
    ticker = "1326"  # TOPIX ETF - should have lots of data
    
    end_date = date.today()
    start_date = end_date - timedelta(days=1095)  # 3 years
    
    print(f"\nTicker: {ticker}")
    print(f"Period: {start_date} to {end_date} (3 years)")
    print(f"Mode: Daily")
    print(f"\nThis should trigger pagination...\n")
    
    df = scraper.fetch(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        frequency="daily"
    )
    
    if df is not None and len(df) > 0:
        print(f"\n" + "=" * 80)
        print("RESULTS:")
        print("=" * 80)
        print(f"Total data points: {len(df)}")
        print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"Price range: ¥{df['price'].min():,.2f} to ¥{df['price'].max():,.2f}")
        
        # Estimate pages
        rows_per_page = 20
        estimated_pages = (len(df) + rows_per_page - 1) // rows_per_page
        print(f"\nEstimated pages scraped: {estimated_pages}")
        
        if estimated_pages > 1:
            print("✅ PAGINATION TRIGGERED!")
        else:
            print("ℹ️  Only 1 page needed")
            
        # Save to CSV to demonstrate
        csv_path = f"/tmp/{ticker}_3year_daily.csv"
        success = scraper.fetch_and_save_csv(
            ticker=ticker,
            output_path=csv_path,
            start_date=start_date,
            end_date=end_date,
            frequency="daily"
        )
        
        if success:
            print(f"\n✅ CSV saved to: {csv_path}")
    else:
        print("❌ No data retrieved")


if __name__ == "__main__":
    test_pagination_with_longer_period()
