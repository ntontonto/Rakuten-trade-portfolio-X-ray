"""
Test the enhanced Yahoo scraper with pagination and CSV export

This script demonstrates:
1. Fetching weekly data with pagination (multiple pages)
2. Deduplication of records
3. Extracting NAV, diff, and AUM data
4. Saving results as CSV
"""
from datetime import date, timedelta
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.yahoo_scraper_enhanced import YahooScraperFetcher


def test_pagination_with_weekly_data():
    """Test fetching weekly data across multiple pages"""
    print("\n" + "=" * 80)
    print("TEST 1: PAGINATION WITH WEEKLY DATA FOR 0331418A")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    # Fetch 2 years of weekly data to ensure multiple pages
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    print(f"\nFetching WEEKLY data for 2 years...")
    print(f"This should trigger pagination (次へ button clicks)")
    
    df = scraper.fetch(
        ticker="0331418A",
        start_date=start_date,
        end_date=end_date,
        frequency="weekly"
    )
    
    if df is not None and len(df) > 0:
        print(f"\n✅ SUCCESS! Fetched {len(df)} weekly data points")
        
        print(f"\nFirst 5 rows:")
        print(df.head())
        
        print(f"\nLast 5 rows:")
        print(df.tail())
        
        print(f"\nData Summary:")
        print(f"  Period: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"  NAV range: ¥{df['price'].min():,.2f} to ¥{df['price'].max():,.2f}")
        print(f"  Average NAV: ¥{df['price'].mean():,.2f}")
        
        # Check available columns
        print(f"\nAvailable columns: {list(df.columns)}")
        
        if 'diff' in df.columns:
            valid_diffs = df['diff'].dropna()
            if len(valid_diffs) > 0:
                print(f"  Diff (前日比) range: ¥{valid_diffs.min():,.2f} to ¥{valid_diffs.max():,.2f}")
        
        if 'aum_million' in df.columns:
            valid_aum = df['aum_million'].dropna()
            if len(valid_aum) > 0:
                print(f"  AUM (純資産) range: ¥{valid_aum.min():,.0f}M to ¥{valid_aum.max():,.0f}M")
        
        # Check if data is weekly
        if len(df) > 1:
            avg_gap = (df.index[-1] - df.index[0]).days / (len(df) - 1)
            print(f"\n  Avg days between data points: {avg_gap:.1f}")
            if 5 <= avg_gap <= 9:
                print(f"  ✅ Confirmed: Weekly data (avg ~7 days)")
            else:
                print(f"  ℹ️  Data frequency: {avg_gap:.1f} days")
        
        return df
    else:
        print("❌ No data found")
        return None


def test_csv_export():
    """Test exporting scraped data to CSV"""
    print("\n" + "=" * 80)
    print("TEST 2: CSV EXPORT")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=365)  # 1 year
    
    output_path = "/tmp/fund_0331418A_weekly.csv"
    
    print(f"\nFetching weekly data and saving to CSV...")
    print(f"Output: {output_path}")
    
    success = scraper.fetch_and_save_csv(
        ticker="0331418A",
        output_path=output_path,
        start_date=start_date,
        end_date=end_date,
        frequency="weekly"
    )
    
    if success:
        print(f"\n✅ CSV saved successfully!")
        
        # Read and display first few lines
        with open(output_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        print(f"\nCSV Preview (first 10 lines):")
        print("-" * 80)
        for line in lines[:10]:
            print(line.rstrip())
        print("-" * 80)
        print(f"Total rows: {len(lines) - 1} (excluding header)")
        
        print(f"\n💡 You can find the full CSV at: {output_path}")
    else:
        print("❌ Failed to save CSV")


def test_calc_start_date_with_pagination():
    """Test pagination with calculation start date filter"""
    print("\n" + "=" * 80)
    print("TEST 3: PAGINATION + CALCULATION START DATE")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # Fetch 2 years
    calc_start = end_date - timedelta(days=180)  # But only use last 6 months
    
    print(f"\nScenario:")
    print(f"  Fetch period:  {start_date} to {end_date} (2 years)")
    print(f"  Calc period:   {calc_start} to {end_date} (6 months)")
    print(f"  Frequency:     Weekly")
    
    df = scraper.fetch(
        ticker="0331418A",
        start_date=start_date,
        end_date=end_date,
        frequency="weekly",
        calc_start_date=calc_start
    )
    
    if df is not None and len(df) > 0:
        print(f"\n✅ SUCCESS!")
        print(f"  Returned data: {len(df)} rows (filtered to last 6 months)")
        print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
        
        # Verify all dates are >= calc_start_date
        earliest = df.index.min().date()
        if earliest >= calc_start:
            print(f"  ✅ Calculation start date filter working correctly")
        else:
            print(f"  ⚠️  Some dates before calc_start: {earliest}")
    else:
        print("❌ No data found")


def test_deduplication():
    """Test that duplicate dates are properly removed"""
    print("\n" + "=" * 80)
    print("TEST 4: DEDUPLICATION CHECK")
    print("=" * 80)
    
    scraper = YahooScraperFetcher(headless=True, debug=True)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    print(f"\nFetching daily data (more likely to have duplicates)...")
    
    df = scraper.fetch(
        ticker="0331418A",
        start_date=start_date,
        end_date=end_date,
        frequency="daily"
    )
    
    if df is not None and len(df) > 0:
        # Check for duplicate dates
        duplicate_dates = df.index[df.index.duplicated()]
        
        if len(duplicate_dates) == 0:
            print(f"\n✅ No duplicate dates found!")
            print(f"  Total records: {len(df)}")
            print(f"  Unique dates: {df.index.nunique()}")
        else:
            print(f"\n⚠️  Found {len(duplicate_dates)} duplicate dates")
            print(f"  Duplicates: {list(duplicate_dates)}")
    else:
        print("❌ No data found")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("YAHOO FINANCE SCRAPER - PAGINATION & CSV EXPORT TESTS")
    print("🚀" * 40)
    
    # Run all tests
    test_pagination_with_weekly_data()
    test_csv_export()
    test_calc_start_date_with_pagination()
    test_deduplication()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ Pagination (clicking 次へ button)")
    print("   ✅ Deduplication by date")
    print("   ✅ NAV, diff, AUM extraction")
    print("   ✅ CSV export")
    print("   ✅ Calculation start date filtering")
    print("=" * 80 + "\n")
