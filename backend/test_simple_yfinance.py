"""Simple yfinance test"""
import yfinance as yf
from datetime import date

print("Testing yfinance connection...")

# Try simplest possible query
try:
    ticker = yf.Ticker("AAPL")
    print(f"Ticker object created: {ticker}")

    # Try to get info
    info = ticker.info
    print(f"Got info: {info.get('symbol', 'No symbol')}")

    # Try historical data
    hist = ticker.history(period="1mo")
    print(f"Historical data: {len(hist)} rows")
    print(hist.head())

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
