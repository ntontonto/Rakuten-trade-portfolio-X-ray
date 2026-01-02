from app.api.deps import get_db_session
from app.services.price_fetcher import HistoricalPriceService
from datetime import date

# Get database session
db = next(get_db_session())

# Initialize price fetcher
fetcher = HistoricalPriceService(db=db)

# Test assets
test_assets = [
    ("4755", "楽天グループ", None),
    ("1693", "ＷＴ銅上場投信", None),
    ("25314203", "NZAM・ベータ 米国REIT", None),
    ("03311187", "eMAXIS Slim 米国株式(S&P500)", None),
    ("0331418A", "eMAXIS Slim 全世界株式(オール・カントリー)", None),
]

print("=" * 80)
print("DATA SOURCE TEST")
print("=" * 80)

for symbol, name, portfolio_id in test_assets:
    print(f"\nTesting: {name} ({symbol})")
    print("-" * 80)

    prices, source = fetcher.get_price_history(
        symbol=symbol,
        name=name,
        start_date=date(2025, 12, 25),
        end_date=date(2025, 12, 31),
        portfolio_id=portfolio_id
    )

    if prices is not None and len(prices) > 0:
        print(f"✅ Got {len(prices)} prices")
        print(f"📊 Source: {source.upper()}")
        print(f"   Latest: {prices.index[-1].date()} = ¥{prices.iloc[-1]['price']:.2f}")
    else:
        print(f"❌ No data")
        print(f"📊 Source: {source}")

    # Check if interpolated
    if source == 'interpolated':
        print(f"⚠️  WARNING: Using interpolated values!")

db.close()
