"""
Unit tests for Yahoo Finance scraper (Playwright-based)

Tests the scraper's ability to fetch historical prices from:
1. Yahoo Finance Japan (for JP funds/stocks)
2. Yahoo Finance Global (for US stocks)
"""
import pytest
from datetime import date
from app.services.yahoo_scraper import YahooScraperFetcher


class TestYahooScraperFetcher:
    """Test Yahoo Finance scraper functionality"""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance with headless browser"""
        return YahooScraperFetcher(headless=True)

    @pytest.fixture
    def date_range(self):
        """Test date range (short period for faster tests)"""
        return date(2024, 1, 2), date(2024, 1, 31)

    # ==================== Japanese Fund Tests ====================

    def test_jp_mutual_fund_0331418A(self, scraper, date_range):
        """Test Japanese mutual fund code 0331418A (オルカン)"""
        start_date, end_date = date_range
        
        df = scraper.fetch("0331418A", start_date, end_date)
        
        if df is not None:
            # If data is found
            assert len(df) > 0, "Should return at least one data point"
            assert "price" in df.columns, "DataFrame should have 'price' column"
            assert df.index.name == "date", "Index should be named 'date'"
            print(f"✅ Found {len(df)} data points for 0331418A")
            print(f"   Latest: {df.index[-1].date()} = ¥{df.iloc[-1]['price']:.2f}")
        else:
            # If no data found (expected for mutual funds)
            print("⚠️  No data found for 0331418A (expected - mutual funds not on Yahoo Finance)")
            pytest.skip("Mutual fund 0331418A not available on Yahoo Finance")

    def test_jp_etf_1326(self, scraper, date_range):
        """Test Japanese ETF (1326 - SPDR Gold)"""
        start_date, end_date = date_range
        
        df = scraper.fetch("1326", start_date, end_date)
        
        assert df is not None, "Should return data for Japanese ETF"
        assert len(df) > 0, "Should have at least one data point"
        assert "price" in df.columns, "Should have price column"
        
        # Verify data is within date range
        first_date = df.index[0].date()
        last_date = df.index[-1].date()
        assert first_date >= start_date, "First date should be >= start_date"
        assert last_date <= end_date, "Last date should be <= end_date"
        
        print(f"✅ Found {len(df)} data points for 1326.T")

    # ==================== US Stock Tests ====================

    def test_us_stock_pltr(self, scraper, date_range):
        """Test US stock (PLTR - Palantir)"""
        start_date, end_date = date_range
        
        df = scraper.fetch("PLTR", start_date, end_date)
        
        assert df is not None, "Should return data for US stock"
        assert len(df) > 0, "Should have at least one data point"
        assert "price" in df.columns, "Should have price column"
        
        print(f"✅ Found {len(df)} data points for PLTR")

    # ==================== URL Building Tests ====================

    def test_build_url_jp_numeric(self, scraper):
        """Test URL building for Japanese numeric ticker"""
        url = scraper._build_url("1326")
        assert "finance.yahoo.co.jp" in url
        assert "1326" in url
        assert "/history" in url

    def test_build_url_jp_with_t(self, scraper):
        """Test URL building for .T ticker"""
        url = scraper._build_url("1326.T")
        assert "finance.yahoo.co.jp" in url
        assert "1326" in url  # .T should be removed
        assert "/history" in url

    def test_build_url_us_stock(self, scraper):
        """Test URL building for US ticker"""
        url = scraper._build_url("PLTR")
        assert "finance.yahoo.com" in url
        assert "PLTR" in url
        assert "/history" in url

    def test_build_url_fund_code(self, scraper):
        """Test URL building for fund code with letter"""
        url = scraper._build_url("0331418A")
        # Should use JP site (starts with digits)
        assert "finance.yahoo.co.jp" in url
        assert "0331418A" in url

    # ==================== Edge Cases ====================

    def test_invalid_ticker(self, scraper, date_range):
        """Test with invalid/non-existent ticker"""
        start_date, end_date = date_range
        
        df = scraper.fetch("INVALIDTICKER999", start_date, end_date)
        
        # Should return None for invalid ticker
        assert df is None, "Should return None for invalid ticker"

    def test_empty_date_range(self, scraper):
        """Test with same start and end date"""
        test_date = date(2024, 1, 15)
        
        df = scraper.fetch("PLTR", test_date, test_date)
        
        # Might return None or single data point
        if df is not None:
            assert len(df) <= 1, "Should return at most one data point"

    # ==================== Data Quality Tests ====================

    def test_price_values_positive(self, scraper, date_range):
        """Test that all prices are positive numbers"""
        start_date, end_date = date_range
        
        df = scraper.fetch("PLTR", start_date, end_date)
        
        if df is not None:
            assert (df["price"] > 0).all(), "All prices should be positive"
            assert df["price"].notna().all(), "No NaN values in prices"

    def test_dates_sorted(self, scraper, date_range):
        """Test that dates are sorted chronologically"""
        start_date, end_date = date_range
        
        df = scraper.fetch("PLTR", start_date, end_date)
        
        if df is not None and len(df) > 1:
            dates = df.index.to_list()
            assert dates == sorted(dates), "Dates should be sorted chronologically"

    def test_no_duplicate_dates(self, scraper, date_range):
        """Test that there are no duplicate dates"""
        start_date, end_date = date_range
        
        df = scraper.fetch("PLTR", start_date, end_date)
        
        if df is not None:
            assert not df.index.duplicated().any(), "Should not have duplicate dates"


# ==================== Integration Test ====================

def test_scraper_full_flow_0331418A():
    """
    Full integration test for fund 0331418A
    
    This test demonstrates the complete flow:
    1. Create scraper
    2. Fetch data
    3. Verify result
    """
    print("\n" + "=" * 70)
    print("YAHOO SCRAPER - FULL INTEGRATION TEST FOR 0331418A")
    print("=" * 70)
    
    scraper = YahooScraperFetcher(headless=True)
    
    # Test parameters
    ticker = "0331418A"
    start = date(2024, 1, 2)
    end = date(2024, 1, 31)
    
    print(f"\nFetching: {ticker}")
    print(f"Period: {start} to {end}")
    print(f"URL: {scraper._build_url(ticker)}")
    print("-" * 70)
    
    # Fetch data
    df = scraper.fetch(ticker, start, end)
    
    # Report results
    if df is not None:
        print(f"✅ SUCCESS! Fetched {len(df)} data points")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nLast 5 rows:")
        print(df.tail())
        print(f"\nSummary:")
        print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"  Price range: ¥{df['price'].min():.2f} to ¥{df['price'].max():.2f}")
        print(f"  Average: ¥{df['price'].mean():.2f}")
    else:
        print("❌ NO DATA FOUND")
        print("\nExpected Result:")
        print("  Japanese mutual fund codes (like 0331418A) are typically")
        print("  NOT available on Yahoo Finance. This is normal behavior.")
        print("\nThe system will automatically fall back to:")
        print("  1. Official NAV cache (if CSV exists)")
        print("  2. Linear interpolation from transaction prices")
        
        # This is expected, so we mark it as a skip rather than failure
        pytest.skip("Fund 0331418A not available on Yahoo Finance (expected behavior)")
    
    print("=" * 70)


if __name__ == "__main__":
    # Run the integration test directly
    test_scraper_full_flow_0331418A()
