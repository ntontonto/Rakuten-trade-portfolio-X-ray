#!/usr/bin/env python3
"""
Test script for verifying Japanese ticker flow (4755.T and 1693.T)
Run this inside Docker container or with proper environment
"""
from datetime import date, timedelta
import sys

# Test 1: Alias Resolution
print("=" * 80)
print("TEST 1: ALIAS RESOLUTION")
print("=" * 80)

from app.services.alias_resolver import resolve_alias
from app.services.ticker_mappings import get_yahoo_ticker

test_cases = [
    # 4755 (Rakuten)
    ("4755", ""),
    ("4755.T", ""),
    ("", "楽天グループ"),
    ("", "楽天 グループ"),
    
    # 1693 (WisdomTree Copper)
    ("1693", ""),
    ("1693.T", ""),
    ("", "ＷＴ銅上場投信"),
    ("", "ＷＴ銅上場投信（WisdomTree 銅）"),
    ("", "WisdomTree 銅"),
]

for symbol_in, name_in in test_cases:
    symbol_out, name_out = resolve_alias(symbol_in, name_in)
    ticker = get_yahoo_ticker(symbol_out)
    
    input_str = f"'{symbol_in}', '{name_in}'"
    output_str = f"{symbol_out} → {ticker}"
    
    print(f"  {input_str:50} → {output_str}")

print()

# Test 2: URL Construction
print("=" * 80)
print("TEST 2: URL CONSTRUCTION")
print("=" * 80)

from app.services.yahoo_scraper_enhanced import YahooScraperFetcher

scraper = YahooScraperFetcher(headless=True, debug=False)

url_tests = [
    ("4755.T", "daily"),
    ("4755.T", "weekly"),
    ("1693.T", "daily"),
    ("1693.T", "weekly"),
    ("0331418A", "daily"),
    ("0331418A", "weekly"),
]

for ticker, freq in url_tests:
    url = scraper._build_url(ticker, freq)
    print(f"  {ticker:15} ({freq:7}) → {url}")

print()

# Test 3: Scraper Fetch (Dry Run)
print("=" * 80)
print("TEST 3: SCRAPER FETCH (DRY RUN)")
print("=" * 80)

end_date = date.today()
start_date = end_date - timedelta(days=30)  # 1 month of data

scraper_debug = YahooScraperFetcher(headless=True, debug=True)

scrape_tests = [
    ("4755.T", "daily", "Rakuten Group (Daily)"),
    ("1693.T", "daily", "WisdomTree Copper ETF (Daily)"),
]

for ticker, freq, description in scrape_tests:
    print(f"\n--- {description} ---")
    try:
        df = scraper_debug.fetch(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            frequency=freq
        )
        
        if df is not None and len(df) > 0:
            print(f"✅ SUCCESS: Fetched {len(df)} data points")
            print(f"   Period: {df.index[0].date()} to {df.index[-1].date()}")
            print(f"   Price range: {df['price'].min():.2f} to {df['price'].max():.2f}")
            print(f"   First 3 rows:")
            print(df.head(3))
        else:
            print(f"❌ FAILED: No data returned")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

print()

# Test 4: Weekly Mode (if requested)
if "--weekly" in sys.argv:
    print("=" * 80)
    print("TEST 4: WEEKLY MODE")
    print("=" * 80)
    
    start_date = end_date - timedelta(days=180)  # 6 months
    
    weekly_tests = [
        ("4755.T", "Rakuten Group (Weekly)"),
        ("1693.T", "WisdomTree Copper ETF (Weekly)"),
    ]
    
    for ticker, description in weekly_tests:
        print(f"\n--- {description} ---")
        try:
            df = scraper_debug.fetch(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                frequency="weekly"
            )
            
            if df is not None and len(df) > 0:
                print(f"✅ SUCCESS: Fetched {len(df)} data points")
                print(f"   Period: {df.index[0].date()} to {df.index[-1].date()}")
                
                # Check if data is actually weekly
                if len(df) > 1:
                    avg_gap = (df.index[-1] - df.index[0]).days / len(df)
                    print(f"   Avg days between points: {avg_gap:.1f}")
                    if 5 <= avg_gap <= 9:
                        print(f"   ✅ Confirmed: Weekly data")
                    else:
                        print(f"   ⚠️  May not be weekly data (Yahoo limitation)")
            else:
                print(f"❌ FAILED: No data returned")
        except Exception as e:
            print(f"❌ ERROR: {e}")

print()
print("=" * 80)
print("ALL TESTS COMPLETE")
print("=" * 80)
print("\nTo test weekly mode, run with: --weekly")
print("Example: python test_japanese_ticker_flow.py --weekly")
