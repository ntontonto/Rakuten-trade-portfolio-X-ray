"""
Test if Yahoo Finance Japan has historical data for ticker 03311187
"""
from datetime import date
from app.services.yahoo_scraper_enhanced import YahooScraperFetcher

def test_yahoo_data_availability():
    """Test different date ranges to see what data is available"""

    ticker = "03311187"
    scraper = YahooScraperFetcher(headless=True, debug=False)

    test_ranges = [
        ("2025 data", date(2025, 1, 1), date(2025, 12, 31)),
        ("2024 data", date(2024, 1, 1), date(2024, 12, 31)),
        ("2023 data", date(2023, 1, 1), date(2023, 12, 31)),
        ("2022 data", date(2022, 1, 1), date(2022, 12, 31)),
        ("2021 data", date(2021, 1, 1), date(2021, 12, 31)),
        ("2020 data", date(2020, 1, 1), date(2020, 12, 31)),
    ]

    print("\n" + "="*80)
    print(f"YAHOO FINANCE DATA AVAILABILITY TEST - Ticker: {ticker}")
    print("="*80)
    print()

    for label, start, end in test_ranges:
        print(f"Testing {label} ({start} to {end})...")

        try:
            df = scraper.fetch(ticker, start, end, frequency='daily')

            if df is not None and len(df) > 0:
                print(f"  ✅ Data available: {len(df)} rows")
                print(f"     Range: {df.index[0].date()} to {df.index[-1].date()}")
            else:
                print(f"  ❌ No data available")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        print()

    print("="*80)
    print("CONCLUSION:")
    print("If only 2025 has data, this ticker may have been recently listed")
    print("or Yahoo Finance Japan only provides recent data for this fund.")
    print("="*80)

if __name__ == "__main__":
    test_yahoo_data_availability()
