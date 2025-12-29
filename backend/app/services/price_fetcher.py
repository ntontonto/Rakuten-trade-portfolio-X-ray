"""
Historical Price Fetcher

Multi-tier approach:
1. Yahoo Finance (direct tickers)
2. Proxy indices (mutual funds)
3. Linear interpolation (fallback)
"""

import time
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Tuple
from functools import wraps
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.services.ticker_mappings import (
    get_yahoo_ticker,
    get_proxy_info,
    PROXY_ALTERNATIVES
)
from app.db.models.transaction import Transaction


# Rate limiting decorator
def rate_limit(calls_per_hour: int = 2000):
    """
    Rate limiting decorator for API calls

    Args:
        calls_per_hour: Maximum calls allowed per hour
    """
    min_interval = 3600 / calls_per_hour
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


class YahooFinanceFetcher:
    """Tier 1: Fetch prices from Yahoo Finance"""

    @rate_limit(calls_per_hour=2000)
    def fetch(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical prices from Yahoo Finance

        Args:
            ticker: Yahoo Finance ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with Date index and Close price, or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                auto_adjust=True  # Adjust for splits/dividends
            )

            if df.empty:
                print(f"⚠️ No data for {ticker}")
                return None

            # Return only close prices
            result = df[['Close']].copy()
            result.columns = ['price']
            result.index.name = 'date'

            print(f"✅ Fetched {len(result)} prices for {ticker}")
            return result

        except Exception as e:
            print(f"❌ Yahoo Finance error for {ticker}: {e}")
            return None


class ProxyIndexEstimator:
    """Tier 2: Estimate mutual fund prices using proxy indices"""

    def __init__(self, yahoo_fetcher: YahooFinanceFetcher):
        self.yahoo_fetcher = yahoo_fetcher

    def estimate(
        self,
        fund_name: str,
        start_date: date,
        end_date: date,
        reference_price: float,
        reference_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Estimate mutual fund NAV using proxy index

        Args:
            fund_name: Full fund name
            start_date: Start date for estimation
            end_date: End date for estimation
            reference_price: Known NAV at reference date
            reference_date: Date of known NAV

        Returns:
            DataFrame with Date index and estimated prices
        """
        proxy_info = get_proxy_info(fund_name)

        if not proxy_info:
            print(f"⚠️ No proxy mapping for fund: {fund_name}")
            return None

        proxy_ticker = proxy_info['proxy']
        print(f"📊 Using proxy {proxy_ticker} for {fund_name[:30]}...")

        # Fetch proxy index prices
        # Need to include reference date
        fetch_start = min(start_date, reference_date)
        fetch_end = max(end_date, reference_date)

        proxy_prices = self.yahoo_fetcher.fetch(proxy_ticker, fetch_start, fetch_end)

        if proxy_prices is None:
            # Try alternative proxy
            if proxy_ticker in PROXY_ALTERNATIVES:
                alt_ticker = PROXY_ALTERNATIVES[proxy_ticker]
                print(f"🔄 Trying alternative proxy: {alt_ticker}")
                proxy_prices = self.yahoo_fetcher.fetch(alt_ticker, fetch_start, fetch_end)

            if proxy_prices is None:
                return None

        # Get proxy price at reference date
        try:
            ref_proxy_price = proxy_prices.loc[proxy_prices.index.date == reference_date, 'price'].iloc[0]
        except (IndexError, KeyError):
            # If exact date not found, use nearest
            nearest_idx = proxy_prices.index.get_indexer([pd.Timestamp(reference_date)], method='nearest')[0]
            ref_proxy_price = proxy_prices.iloc[nearest_idx]['price']

        # Calculate estimated NAVs
        estimated_prices = []

        for idx, row in proxy_prices.iterrows():
            price_date = idx.date()

            if price_date < start_date or price_date > end_date:
                continue

            # Calculate return ratio
            return_ratio = row['price'] / ref_proxy_price

            # Apply to reference NAV
            estimated_nav = reference_price * return_ratio

            # Adjust for expense ratio (annual fee)
            days_diff = (price_date - reference_date).days
            years_diff = days_diff / 365.25
            expense_adjustment = (1 - proxy_info['expense_ratio'] / 100) ** years_diff

            estimated_nav *= expense_adjustment

            estimated_prices.append({
                'date': price_date,
                'price': estimated_nav
            })

        if not estimated_prices:
            return None

        result = pd.DataFrame(estimated_prices)
        result.set_index('date', inplace=True)

        print(f"✅ Estimated {len(result)} prices for {fund_name[:30]}...")
        return result


class LinearInterpolator:
    """Tier 3: Linear interpolation between transaction prices"""

    def interpolate(
        self,
        transactions: List[Transaction],
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Interpolate prices between known transaction points

        Args:
            transactions: List of transactions with prices
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with Date index and interpolated prices
        """
        if not transactions:
            return None

        # Extract known points (date, price)
        known_points = []
        for tx in transactions:
            if tx.quantity > 0:
                price = tx.amount_jpy / tx.quantity
                known_points.append((tx.transaction_date, price))

        if len(known_points) < 2:
            # Need at least 2 points for interpolation
            if len(known_points) == 1:
                # Constant price
                _, constant_price = known_points[0]
                dates = pd.date_range(start_date, end_date, freq='D')
                result = pd.DataFrame({
                    'price': [constant_price] * len(dates)
                }, index=dates)
                result.index.name = 'date'
                return result
            return None

        # Sort by date
        known_points.sort(key=lambda x: x[0])

        # Create date range
        dates = pd.date_range(start_date, end_date, freq='D')

        # Build series indexed by dates and interpolate
        known_series = pd.Series(
            {pd.to_datetime(d): price for d, price in known_points},
            dtype=float
        )
        full_series = known_series.reindex(dates)
        full_series = full_series.interpolate(method='linear')
        full_series = full_series.bfill().ffill()

        result = pd.DataFrame({'price': full_series}, index=dates)
        result.index.name = 'date'

        print(f"⚠️ Used interpolation: {len(result)} prices")
        return result


class ExchangeRateService:
    """Fetch USD/JPY exchange rates"""

    def __init__(self, yahoo_fetcher: YahooFinanceFetcher):
        self.yahoo_fetcher = yahoo_fetcher

    def get_rates(
        self,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Fetch USD/JPY exchange rate history

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with Date index and exchange rate
        """
        rates = self.yahoo_fetcher.fetch("USDJPY=X", start_date, end_date)

        if rates is None:
            print("⚠️ Failed to fetch USD/JPY rates, using fallback")
            # Fallback: Use current rate from config or hardcoded
            return None

        rates.columns = ['rate']
        return rates


class HistoricalPriceService:
    """
    Main coordinator for historical price fetching

    Uses multi-tier approach:
    1. Yahoo Finance (direct)
    2. Proxy indices (mutual funds)
    3. Linear interpolation (fallback)
    """

    def __init__(self, db: Session):
        self.db = db
        self.yahoo_fetcher = YahooFinanceFetcher()
        self.proxy_estimator = ProxyIndexEstimator(self.yahoo_fetcher)
        self.interpolator = LinearInterpolator()
        self.fx_service = ExchangeRateService(self.yahoo_fetcher)

    def get_price_history(
        self,
        symbol: str,
        name: str,
        start_date: date,
        end_date: date,
        portfolio_id: str
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Get historical price data for an asset

        Args:
            symbol: Asset symbol
            name: Asset name
            start_date: Start date
            end_date: End date
            portfolio_id: Portfolio ID (for transaction lookup)

        Returns:
            Tuple of (DataFrame with prices, source_type)
            source_type: 'yahoo', 'proxy', 'interpolated', or 'none'
        """
        # Tier 1: Try Yahoo Finance (direct)
        yahoo_ticker = get_yahoo_ticker(symbol)

        if yahoo_ticker:
            print(f"🔍 Tier 1: Yahoo Finance for {symbol}")
            prices = self.yahoo_fetcher.fetch(yahoo_ticker, start_date, end_date)
            if prices is not None:
                return prices, 'yahoo'

        # Tier 2: Try Proxy Index (for mutual funds)
        proxy_info = get_proxy_info(name)

        if proxy_info:
            print(f"🔍 Tier 2: Proxy estimation for {name[:30]}")

            # Get a reference transaction to establish baseline
            transactions = (
                self.db.query(Transaction)
                .filter(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.symbol == symbol
                )
                .order_by(Transaction.transaction_date)
                .all()
            )

            if transactions:
                # Use first transaction as reference
                ref_tx = transactions[0]
                ref_price = ref_tx.amount_jpy / ref_tx.quantity if ref_tx.quantity > 0 else 0
                ref_date = ref_tx.transaction_date

                prices = self.proxy_estimator.estimate(
                    name,
                    start_date,
                    end_date,
                    ref_price,
                    ref_date
                )

                if prices is not None:
                    return prices, 'proxy'

        # Tier 3: Fallback to Linear Interpolation
        print(f"🔍 Tier 3: Interpolation for {symbol}")

        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.symbol == symbol
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        prices = self.interpolator.interpolate(transactions, start_date, end_date)

        if prices is not None:
            return prices, 'interpolated'

        # All tiers failed
        print(f"❌ All tiers failed for {symbol}")
        return None, 'none'

    def get_exchange_rate_history(
        self,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Get USD/JPY exchange rate history

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with exchange rates
        """
        return self.fx_service.get_rates(start_date, end_date)
