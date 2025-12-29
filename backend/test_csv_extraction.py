"""
Test script to extract and analyze data from CSV files in inputs/ directory

This demonstrates what data we can extract for ML forecasting.
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.csv_parser import CSVParser
from app.services.asset_classifier import classify_asset
import pandas as pd
from datetime import datetime


def main():
    # Initialize parser
    parser = CSVParser()

    # Find CSV files
    inputs_dir = Path(__file__).parent.parent / "inputs"

    if not inputs_dir.exists():
        print(f"Error: inputs directory not found at {inputs_dir}")
        return

    csv_files = list(inputs_dir.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {inputs_dir}")
        return

    print(f"Found {len(csv_files)} CSV files")
    print("=" * 80)

    all_transactions = []
    balance_data = []
    exchange_rates = {}

    # Parse each file
    for csv_file in csv_files:
        print(f"\n📄 Processing: {csv_file.name}")
        print("-" * 80)

        try:
            with open(csv_file, 'rb') as f:
                content = f.read()

            result = parser.parse_file(content, csv_file.name)

            if result['type'] == 'balance':
                print(f"✅ Asset Balance File")
                balance_data.extend(result['data'])
                exchange_rates.update(result.get('exchange_rates', {}))
                print(f"   Holdings extracted: {len(result['data'])}")
                if exchange_rates:
                    print(f"   Exchange rates: {exchange_rates}")

            elif result['type'] == 'transactions':
                print(f"✅ Transaction History File")
                transactions = result['data']

                # Classify assets
                for tx in transactions:
                    tx['asset_class'] = classify_asset(tx.get('name', ''), tx.get('symbol', ''))

                all_transactions.extend(transactions)
                print(f"   Transactions extracted: {len(transactions)}")

                if transactions:
                    first_date = min(tx['date'] for tx in transactions if pd.notna(tx['date']))
                    last_date = max(tx['date'] for tx in transactions if pd.notna(tx['date']))
                    print(f"   Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")

            else:
                print(f"⚠️  Unknown file type")

        except Exception as e:
            print(f"❌ Error processing file: {e}")

    print("\n" + "=" * 80)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 80)

    # Transaction analysis
    if all_transactions:
        print(f"\n🔹 Total Transactions: {len(all_transactions)}")

        df = pd.DataFrame(all_transactions)

        # Date range
        first_date = df['date'].min()
        last_date = df['date'].max()
        days = (last_date - first_date).days
        print(f"   Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
        print(f"   Duration: {days} days ({days/365:.1f} years)")

        # Markets
        print(f"\n🔹 Markets:")
        for market, count in df['market'].value_counts().items():
            print(f"   {market}: {count} transactions")

        # Unique assets
        print(f"\n🔹 Unique Assets: {df['symbol'].nunique()}")
        assets = df.groupby('symbol').agg({
            'name': 'first',
            'market': 'first',
            'asset_class': 'first',
            'date': ['min', 'max', 'count']
        })

        print("\n   Top 10 assets by transaction count:")
        top_assets = assets.sort_values(('date', 'count'), ascending=False).head(10)
        for symbol, row in top_assets.iterrows():
            name = row[('name', 'first')]
            market = row[('market', 'first')]
            count = row[('date', 'count')]
            print(f"   {symbol:10s} ({market:5s}): {count:3d} transactions - {name[:40]}")

        # Asset class distribution
        print(f"\n🔹 Asset Classes:")
        for asset_class, count in df['asset_class'].value_counts().items():
            total_value = df[df['asset_class'] == asset_class]['amount_jpy'].sum()
            print(f"   {asset_class:12s}: {count:3d} tx, ¥{total_value:,.0f}")

        # Monthly pattern
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby(['month', 'side']).agg({'amount_jpy': 'sum'}).reset_index()
        monthly_pivot = monthly.pivot(index='month', columns='side', values='amount_jpy').fillna(0)

        print(f"\n🔹 Monthly Investment Pattern:")
        print(f"   Active months: {len(monthly_pivot)}")
        if 'BUY' in monthly_pivot.columns:
            avg_monthly = monthly_pivot['BUY'].mean()
            print(f"   Average monthly investment: ¥{avg_monthly:,.0f}")

            # Consistency check
            std_monthly = monthly_pivot['BUY'].std()
            consistency = 1 - min(std_monthly / avg_monthly if avg_monthly > 0 else 0, 1.0)
            print(f"   Consistency score: {consistency:.2f} (1.0 = perfect DCA)")

        # Extract time series for forecasting
        print(f"\n🔹 Extractable Time Series Data:")

        # Build portfolio value time series (approximation)
        df_sorted = df.sort_values('date')
        df_sorted['cumulative_invested'] = df_sorted.apply(
            lambda x: x['amount_jpy'] if x['side'] == 'BUY' else -x['amount_jpy'],
            axis=1
        ).cumsum()

        timeseries = df_sorted[['date', 'cumulative_invested']].copy()
        timeseries = timeseries.drop_duplicates(subset=['date'])

        print(f"   Data points: {len(timeseries)}")
        print(f"   This can be used for portfolio-level forecasting")

        print(f"\n   Sample time series (first 10 points):")
        for _, row in timeseries.head(10).iterrows():
            print(f"   {row['date'].strftime('%Y-%m-%d')}: ¥{row['cumulative_invested']:,.0f}")

    # Balance analysis
    if balance_data:
        print(f"\n🔹 Current Holdings (from balance file):")
        print(f"   Total holdings: {len(balance_data)}")

        total_value = sum(item['value'] for item in balance_data)
        print(f"   Total portfolio value: ¥{total_value:,.0f}")

        print(f"\n   Top 10 holdings by value:")
        sorted_balance = sorted(balance_data, key=lambda x: x['value'], reverse=True)
        for item in sorted_balance[:10]:
            name = item.get('name', 'N/A')
            value = item['value']
            pct = (value / total_value * 100) if total_value > 0 else 0
            print(f"   {value:>12,.0f} ({pct:5.1f}%) - {name[:50]}")

    print("\n" + "=" * 80)
    print("✨ DATA READY FOR ML FEATURES")
    print("=" * 80)
    print("""
Available for Phase 4 ML:
1. ✅ Portfolio Growth Forecasting
   - Time series with {0} data points
   - {1:.1f} years of history

2. ✅ Monthly Cash Flow Prediction
   - {2} months of investment data
   - Pattern: Can be analyzed

3. ✅ Risk Scoring
   - {3} unique assets to score
   - Transaction frequency, volatility proxy available

4. ✅ Portfolio Optimization
   - Current allocation across {4} asset classes
   - Historical transaction data for covariance estimation

⚠️  NOT Available:
   - Daily historical prices (would need external API)
   - Individual asset price forecasting (requires Yahoo Finance)
    """.format(
        len(timeseries) if all_transactions else 0,
        days / 365 if all_transactions else 0,
        len(monthly_pivot) if all_transactions else 0,
        df['symbol'].nunique() if all_transactions else 0,
        df['asset_class'].nunique() if all_transactions else 0
    ))


if __name__ == "__main__":
    main()
