"""
Historical Price Fetcher

Multi-tier approach:
1. Yahoo Finance (direct tickers)
2. Official NAV (for mutual funds)
3. Linear interpolation (fallback)
"""

import time
import random
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Tuple
from functools import wraps
from threading import Lock, Event
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.services.ticker_mappings import get_yahoo_ticker
from app.db.models.transaction import Transaction
from app.services.alt_price_fetcher import SecondaryPriceFetcher
from app.services.nav_fetcher import ToshinNavFetcher
from app.services.yahoo_scraper_enhanced import YahooScraperFetcher
from app.services.alias_resolver import resolve_alias
from app.services.price_cache_service import PriceCacheService


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

    def __init__(self, yahoo_fetcher: YahooFinanceFetcher, alt_fetcher: Optional[SecondaryPriceFetcher] = None):
        self.yahoo_fetcher = yahoo_fetcher
        self.alt_fetcher = alt_fetcher

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
            # Try alternative provider tickers
            if self.alt_fetcher:
                for fx_ticker in ["USD/JPY", "USDJPY"]:
                    alt = self.alt_fetcher.fetch(fx_ticker, start_date, end_date)
                    if alt is not None:
                        alt.columns = ["rate"]
                        return alt
            print("⚠️ Failed to fetch USD/JPY rates, using fallback")
            return None

        rates.columns = ['rate']
        return rates


class HistoricalPriceService:
    """
    Main coordinator for historical price fetching

    Uses multi-tier approach:
    1. Yahoo Finance (direct)
    2. Official NAV (for mutual funds)
    3. Linear interpolation (fallback)
    """

    def __init__(self, db: Session):
        self.db = db
        self.yahoo_fetcher = YahooFinanceFetcher()
        self.alt_fetcher = SecondaryPriceFetcher()
        self.interpolator = LinearInterpolator()
        self.fx_service = ExchangeRateService(self.yahoo_fetcher, self.alt_fetcher)
        self.nav_fetcher = ToshinNavFetcher()
        self.scraper = YahooScraperFetcher()
        self.cache_service = PriceCacheService(db)  # NEW: Database cache
        self._cache = {}  # simple in-process cache keyed by (symbol, start, end)
        self._inflight: Dict[Tuple[str, date, date], Event] = {}
        self._inflight_lock = Lock()
        self._failures: Dict[Tuple[str, str], Tuple[int, float]] = {}  # (symbol, source) -> (count, last_ts)

    def _with_retry(self, func, max_attempts: int = 2, base_delay: float = 0.5):
        """Simple retry with jitter to avoid hammering sources."""
        attempt = 0
        while attempt < max_attempts:
            try:
                return func()
            except Exception:
                attempt += 1
                if attempt >= max_attempts:
                    raise
                sleep_for = base_delay * (2 ** (attempt - 1)) + random.random() * 0.2
                time.sleep(sleep_for)

    def _get_tx_bounds(self, symbol: str, portfolio_id: str) -> Tuple[Optional[date], Optional[date]]:
        """Find first/last transaction dates for clamping fetch windows."""
        tx = (
            self.db.query(Transaction.transaction_date)
            .filter(Transaction.portfolio_id == portfolio_id, Transaction.symbol == symbol)
            .order_by(Transaction.transaction_date)
            .all()
        )
        if not tx:
            return None, None
        def _extract(obj):
            # Support ORM tuples or SimpleNamespace in tests
            if hasattr(obj, "transaction_date"):
                return getattr(obj, "transaction_date")
            try:
                return obj[0]
            except Exception:
                return None

        first = _extract(tx[0])
        last = _extract(tx[-1])
        return first, last

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
            source_type: 'scraped', 'yahoo', 'alt', 'nav', 'interpolated', or 'none'
        """
        # Resolve aliases (e.g., オルカン fund code/name -> canonical fetch symbol)
        fetch_symbol, fetch_name = resolve_alias(symbol, name)

        # Clamp date range to transaction window to avoid unnecessary fetch
        tx_first, tx_last = self._get_tx_bounds(symbol, portfolio_id)
        effective_start = max(start_date, tx_first) if tx_first else start_date
        effective_end = end_date if not tx_last else max(end_date, tx_last)

        cache_key = (fetch_symbol, effective_start, effective_end)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Deduplicate concurrent in-process fetches for the same window
        with self._inflight_lock:
            if cache_key in self._inflight:
                evt = self._inflight[cache_key]
                created = False
            else:
                evt = Event()
                self._inflight[cache_key] = evt
                created = True
        if not created:
            # Another thread is fetching; wait briefly for result to land in cache
            evt.wait(timeout=5)
            return self._cache.get(cache_key, (None, 'none'))
        if evt.is_set():
            # Another thread already finished while we were here
            return self._cache.get(cache_key, (None, 'none'))

        # Circuit breaker: skip network-heavy sources on repeated recent failures
        def _is_open(src: str) -> bool:
            count, last_ts = self._failures.get((fetch_symbol, src), (0, 0.0))
            cooldown = 60  # seconds
            return count >= 3 and (time.time() - last_ts) < cooldown

        # NEW: Check database cache first (try all data sources in priority order)
        # If no mapping found and symbol looks JP numeric, default to .T
        yahoo_ticker = get_yahoo_ticker(fetch_symbol)
        if not yahoo_ticker:
            if fetch_symbol.endswith(".T"):
                yahoo_ticker = fetch_symbol
            elif fetch_symbol.isdigit():
                yahoo_ticker = f"{fetch_symbol}.T"
            else:
                yahoo_ticker = fetch_symbol

        # Try data sources in order of preference: scraped > nav > yahoo > alt > interpolated
        for source_type in ['scraped', 'nav', 'yahoo', 'alt', 'interpolated']:
            cached_data, cache_source = self.cache_service.get_price_history(
                symbol=fetch_symbol,
                ticker=yahoo_ticker,
                start_date=effective_start,
                end_date=effective_end,
                source=source_type
            )
            if cached_data is not None and cache_source == 'cache':
                print(f"✅ Cache hit: {len(cached_data)} rows from '{source_type}' source")
                self._cache[cache_key] = (cached_data, source_type)
                evt.set()
                with self._inflight_lock:
                    self._inflight.pop(cache_key, None)
                return cached_data, source_type

        # Tier 0: Official NAV cache
        nav_prices = None
        if not _is_open('nav'):
            try:
                nav_prices = self._with_retry(
                    lambda: self.nav_fetcher.fetch(fetch_name, effective_start, effective_end)
                )
            except Exception:
                self._failures[(fetch_symbol, 'nav')] = (self._failures.get((fetch_symbol, 'nav'), (0, 0.0))[0] + 1, time.time())
        if nav_prices is not None:
            print(f"📊 Using official NAV for {fetch_name[:30]}...")
            self._cache[cache_key] = (nav_prices, 'nav')
            # Store NAV data in cache
            self.cache_service._store_price_data(fetch_symbol, yahoo_ticker, nav_prices, 'nav')
            return nav_prices, 'nav'

        # Tier 1: Scrape Yahoo Finance (JP/Global)
        scraped = None
        if not _is_open('scraped'):
            print(f"🔍 Tier 1: Yahoo scrape for {fetch_symbol} ({yahoo_ticker})")
            try:
                scraped = self._with_retry(
                    lambda: self.scraper.fetch(yahoo_ticker, effective_start, effective_end)
                )
                if scraped is None:
                    print(f"⚠️  Scraper returned None for {yahoo_ticker}")
            except Exception as e:
                print(f"❌ Scraper error for {yahoo_ticker}: {e}")
                self._failures[(fetch_symbol, 'scraped')] = (self._failures.get((fetch_symbol, 'scraped'), (0, 0.0))[0] + 1, time.time())
        if scraped is not None:
            self._cache[cache_key] = (scraped, 'scraped')
            # Store scraped data in cache
            self.cache_service._store_price_data(fetch_symbol, yahoo_ticker, scraped, 'scraped')
            evt.set()
            with self._inflight_lock:
                self._inflight.pop(cache_key, None)
            return scraped, 'scraped'

        # Tier 2: Yahoo Finance API (yfinance)
        # Skip yfinance for Japanese stocks (doesn't support .T suffix well)
        yf_ticker = get_yahoo_ticker(fetch_symbol)
        yf_ticker = yahoo_ticker
        if yf_ticker and yf_ticker.endswith('.T'):
            print(f"⏭️  Skipping yfinance for Japanese ticker {yf_ticker} (not supported)")
        elif yf_ticker and not _is_open('yahoo'):
            print(f"🔍 Tier 2: Yahoo Finance API for {fetch_symbol}")
            try:
                prices = self._with_retry(
                    lambda: self.yahoo_fetcher.fetch(yf_ticker, effective_start, effective_end)
                )
            except Exception:
                prices = None
                self._failures[(fetch_symbol, 'yahoo')] = (self._failures.get((fetch_symbol, 'yahoo'), (0, 0.0))[0] + 1, time.time())
            if prices is not None:
                self._cache[cache_key] = (prices, 'yahoo')
                # Store yfinance data in cache
                self.cache_service._store_price_data(fetch_symbol, yf_ticker, prices, 'yahoo')
                evt.set()
                with self._inflight_lock:
                    self._inflight.pop(cache_key, None)
                return prices, 'yahoo'

        # Tier 3: Alternative provider (Twelve Data / Alpha Vantage)
        # Skip alt providers for Japanese stocks (don't support .T suffix)
        if yf_ticker and yf_ticker.endswith('.T'):
            print(f"⏭️  Skipping alt provider for Japanese ticker {yf_ticker} (not supported)")
        elif yf_ticker and not _is_open('alt'):
            print(f"🔍 Tier 3: Alternative provider for {fetch_symbol}")
            try:
                alt_prices = self._with_retry(
                    lambda: self.alt_fetcher.fetch(yf_ticker, effective_start, effective_end)
                )
            except Exception:
                alt_prices = None
                self._failures[(fetch_symbol, 'alt')] = (self._failures.get((fetch_symbol, 'alt'), (0, 0.0))[0] + 1, time.time())
            if alt_prices is not None:
                self._cache[cache_key] = (alt_prices, 'alt')
                # Store alternative provider data in cache
                self.cache_service._store_price_data(fetch_symbol, yf_ticker, alt_prices, 'alt')
                evt.set()
                with self._inflight_lock:
                    self._inflight.pop(cache_key, None)
                return alt_prices, 'alt'

        # Tier 4: Fallback to Linear Interpolation
        print(f"🔍 Tier 4: Interpolation for {symbol}")

        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.symbol == symbol
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        prices = self.interpolator.interpolate(transactions, effective_start, effective_end)

        if prices is not None:
            self._cache[cache_key] = (prices, 'interpolated')
            # Store interpolated data in cache for future use
            self.cache_service._store_price_data(fetch_symbol, yahoo_ticker, prices, 'interpolated')
            evt.set()
            with self._inflight_lock:
                self._inflight.pop(cache_key, None)
            return prices, 'interpolated'

        # All tiers failed
        print(f"❌ All tiers failed for {symbol}")
        evt.set()
        with self._inflight_lock:
            self._inflight.pop(cache_key, None)
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
