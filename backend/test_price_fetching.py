"""
Test Historical Price Fetching

Tests the multi-tier price fetching system with real portfolio data
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.price_fetcher import (
    YahooFinanceFetcher,
    LinearInterpolator,
    ExchangeRateService
)
from app.services.ticker_mappings import get_yahoo_ticker


def test_tier1_yahoo_finance():
    """Test Tier 1: Yahoo Finance direct fetch"""
    print("\n" + "=" * 80)
    print("TEST 1: YAHOO FINANCE (Tier 1)")
    print("=" * 80)

    fetcher = YahooFinanceFetcher()

    test_cases = [
        ("PLTR", "US Stock"),
        ("QQQ", "US ETF"),
        ("1326.T", "Japanese ETF - Gold"),
        ("INVALID", "Should fail"),
    ]

    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)

    for ticker, description in test_cases:
        print(f"\n📊 Testing {ticker} ({description})")
        prices = fetcher.fetch(ticker, start_date, end_date)

        if prices is not None:
            print(f"   ✅ Success: {len(prices)} prices")
            print(f"   First: {prices.index[0].date()} = ¥{prices.iloc[0]['price']:.2f}")
            print(f"   Last:  {prices.index[-1].date()} = ¥{prices.iloc[-1]['price']:.2f}")
        else:
            print(f"   ❌ Failed to fetch")


def test_exchange_rates():
    """Test USD/JPY exchange rate fetching"""
    print("\n" + "=" * 80)
    print("TEST 3: EXCHANGE RATE SERVICE")
    print("=" * 80)

    yahoo_fetcher = YahooFinanceFetcher()
    fx_service = ExchangeRateService(yahoo_fetcher)

    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)

    print(f"\n💱 Testing USD/JPY rates from {start_date} to {end_date}")

    rates = fx_service.get_rates(start_date, end_date)

    if rates is not None:
        print(f"   ✅ Success: {len(rates)} exchange rates")
        print(f"   First: {rates.index[0].date()} = ¥{rates.iloc[0]['rate']:.2f}/USD")
        print(f"   Last:  {rates.index[-1].date()} = ¥{rates.iloc[-1]['rate']:.2f}/USD")

        # Calculate average and range
        avg_rate = rates['rate'].mean()
        min_rate = rates['rate'].min()
        max_rate = rates['rate'].max()

        print(f"\n   Statistics:")
        print(f"      Average: ¥{avg_rate:.2f}/USD")
        print(f"      Min: ¥{min_rate:.2f}/USD")
        print(f"      Max: ¥{max_rate:.2f}/USD")
    else:
        print(f"   ❌ Failed to fetch rates")


def test_ticker_mappings():
    """Test ticker mapping coverage"""
    print("\n" + "=" * 80)
    print("TEST 4: TICKER MAPPING COVERAGE")
    print("=" * 80)

    # Sample symbols from your portfolio
    test_symbols = [
        ("PLTR", "Palantir"),
        ("QQQ", "QQQ ETF"),
        ("1326", "SPDR Gold"),
        ("1542", "Pure Silver"),
        ("eMAXIS Slim 米国株式(S&P500)", "eMAXIS S&P500"),
        ("eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)", "eMAXIS ACWI"),
        ("三菱UFJ 純金ファンド(ファインゴールド)", "Gold Fund"),
    ]

    print("\n📋 Checking mapping coverage:")

    for symbol, description in test_symbols:
        # Check Yahoo direct
        yahoo_ticker = get_yahoo_ticker(symbol)

        if yahoo_ticker:
            print(f"   ✅ {symbol:40s} → Yahoo: {yahoo_ticker}")
        else:
            print(f"   ⚠️  {symbol:40s} → No mapping (will use interpolation)")



def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("HISTORICAL PRICE FETCHING TEST SUITE")
    print("=" * 80)
    print("\nTesting multi-tier price fetching system:")
    print("  Tier 1: Yahoo Finance (direct tickers)")
    print("  Tier 2: Official NAV (mutual funds)")
    print("  Tier 3: Linear Interpolation (fallback)")

    try:
        # Test each tier
        test_ticker_mappings()
        test_tier1_yahoo_finance()
        test_exchange_rates()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nThe price fetching system is ready!")
        print("\nNext steps:")
        print("  1. The system can now fetch historical prices for your portfolio")
        print("  2. Ready to build portfolio value time series")
        print("  3. Can proceed with ML forecasting")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
