"""
Price Cache Service

Manages historical price data caching to improve performance
"""
import time
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.db.models.price_history import PriceHistory
from app.services.yahoo_scraper_enhanced import YahooScraperFetcher


class PriceCacheService:
    """Service for caching and retrieving historical price data"""

    # Maximum date range to fetch at once (to avoid Yahoo anti-bot)
    MAX_FETCH_DAYS = 730  # ~2 years

    # Prioritize recent data - fetch this much first
    PRIORITY_FETCH_DAYS = 365  # 1 year

    # Backfill in chunks to avoid anti-bot
    BACKFILL_CHUNK_DAYS = 365  # Backfill in 1-year chunks

    def __init__(self, db: Session):
        self.db = db
        self.scraper = YahooScraperFetcher(headless=True, debug=False)

    def get_price_history(
        self,
        symbol: str,
        ticker: str,
        start_date: date,
        end_date: date,
        source: str = 'scraped',
        force_refresh: bool = False
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Get price history with intelligent caching

        Args:
            symbol: Original symbol (e.g., "eMAXIS Slim 全世界株式...")
            ticker: Yahoo ticker (e.g., "0331418A")
            start_date: Start date for data
            end_date: End date for data
            source: Expected source type
            force_refresh: If True, bypass cache and scrape fresh data

        Returns:
            Tuple of (DataFrame with price data, actual source used)
        """
        # Limit date range to avoid Yahoo anti-bot protection
        days_requested = (end_date - start_date).days
        print(f"📦 [Cache] Fetching {ticker} ({start_date} to {end_date}, {days_requested} days)")

        if force_refresh:
            print(f"🔄 [Cache] Force refresh requested - bypassing cache")
            return self._scrape_and_cache_smart(symbol, ticker, start_date, end_date, source)

        # Check cache first
        cached_df = self._get_cached_data(symbol, ticker, start_date, end_date, source)

        if cached_df is not None and len(cached_df) > 0:
            # Check if cache is complete and fresh
            is_complete = self._is_cache_complete(cached_df, start_date, end_date)
            is_fresh = self._is_cache_fresh(cached_df, end_date)

            if is_complete and is_fresh:
                print(f"✅ [Cache] Hit - returning {len(cached_df)} cached rows")
                return cached_df, 'cache'
            elif is_complete and not is_fresh:
                print(f"⚠️ [Cache] Stale - updating recent data")
                # Update forward (get new data since last cached date)
                self._update_forward(symbol, ticker, source)
                # Re-fetch from cache
                cached_df = self._get_cached_data(symbol, ticker, start_date, end_date, source)
                if cached_df is not None and len(cached_df) > 0:
                    print(f"✅ [Cache] Updated - returning {len(cached_df)} rows")
                    return cached_df, 'cache'
            else:
                print(f"⚠️ [Cache] Incomplete - but using cached data")
                # Cache is incomplete, but we have data
                # Only try to fill forward gaps (recent data), not backward gaps
                # Backward gaps likely mean data doesn't exist for those dates

                last_cached = cached_df.index[-1].date()
                today = date.today()
                # Only update forward if we're missing trading days (not just today)
                if last_cached < end_date and (end_date - last_cached).days > 1 and last_cached < today - timedelta(days=1):
                    # Fill recent forward gaps (but not today, which may not have data yet)
                    print(f"📈 [Cache] Updating recent data: {last_cached} to {min(end_date, today - timedelta(days=1))}")
                    self._update_forward(symbol, ticker, source)
                    # Re-fetch to get updated data
                    cached_df = self._get_cached_data(symbol, ticker, start_date, end_date, source)

                if cached_df is not None and len(cached_df) > 0:
                    print(f"✅ [Cache] Returning {len(cached_df)} cached rows (incomplete range)")
                    return cached_df, 'cache'

        # Cache miss - prioritize recent data first
        print(f"❌ [Cache] Miss - fetching data incrementally")
        return self._scrape_and_cache_smart(symbol, ticker, start_date, end_date, source)

    def _get_cached_data(
        self,
        symbol: str,
        ticker: str,
        start_date: date,
        end_date: date,
        source: str
    ) -> Optional[pd.DataFrame]:
        """Query price_history table for cached data"""
        try:
            records = (
                self.db.query(PriceHistory)
                .filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.ticker == ticker,
                        PriceHistory.source == source,
                        PriceHistory.date >= start_date,
                        PriceHistory.date <= end_date
                    )
                )
                .order_by(PriceHistory.date)
                .all()
            )

            if not records:
                return None

            # Convert to DataFrame
            data = []
            for rec in records:
                data.append({
                    'date': rec.date,
                    'price': float(rec.price) if rec.price else None,
                    'nav': float(rec.nav) if rec.nav else None,
                    'diff': float(rec.diff) if rec.diff else None,
                    'aum_million': float(rec.aum_million) if rec.aum_million else None,
                    'last_verified_at': rec.last_verified_at
                })

            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            return df

        except Exception as e:
            print(f"⚠️ [Cache] Error querying cache: {e}")
            return None

    def _is_cache_complete(self, cached_df: pd.DataFrame, start_date: date, end_date: date) -> bool:
        """Check if cached data covers the full requested range"""
        if cached_df is None or len(cached_df) == 0:
            return False

        first_cached = cached_df.index[0].date()
        last_cached = cached_df.index[-1].date()

        # Check if cache covers the range
        return first_cached <= start_date and last_cached >= end_date

    def _is_cache_fresh(self, cached_df: pd.DataFrame, end_date: date) -> bool:
        """
        Check if cached data is fresh enough

        New strategy:
        - Historical data (>30 days old): Always fresh (unchanging)
        - Recent data (≤30 days): Verify once per day
        - Today's data: Verify once per hour
        """
        if cached_df is None or len(cached_df) == 0:
            return False

        from datetime import timezone
        now = datetime.now(timezone.utc)
        today = now.date()

        # Get recent rows (last 30 days)
        cutoff_date = today - timedelta(days=30)
        recent_rows = cached_df[cached_df.index.date >= cutoff_date]

        if len(recent_rows) == 0:
            # No recent data → all historical → always fresh
            return True

        for idx, row in recent_rows.iterrows():
            row_date = idx.date()
            age_days = (today - row_date).days

            if pd.isna(row.get('last_verified_at')):
                return False  # Never verified

            last_verified = row['last_verified_at']
            if not isinstance(last_verified, datetime):
                return False

            # Ensure last_verified is timezone-aware
            if last_verified.tzinfo is None:
                last_verified = last_verified.replace(tzinfo=timezone.utc)

            hours_since_verification = (now - last_verified).total_seconds() / 3600

            # Relaxed freshness rules
            if age_days == 0 and hours_since_verification > 1:
                return False  # Today: re-verify hourly
            elif age_days <= 7 and hours_since_verification > 24:
                return False  # Last week: re-verify daily (not 6 hours!)
            elif age_days <= 30 and hours_since_verification > 168:  # 7 days
                return False  # Last month: re-verify weekly
            # Historical data (>30 days): always fresh

        return True

    def _identify_missing_ranges(
        self,
        cached_df: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> List[Tuple[date, date]]:
        """Identify gaps in cached data"""
        if cached_df is None or len(cached_df) == 0:
            return [(start_date, end_date)]

        missing_ranges = []
        cached_dates = set(cached_df.index.date)

        # Check if we need data before first cached date
        first_cached = cached_df.index[0].date()
        if start_date < first_cached:
            missing_ranges.append((start_date, first_cached - timedelta(days=1)))

        # Check if we need data after last cached date
        last_cached = cached_df.index[-1].date()
        if end_date > last_cached:
            missing_ranges.append((last_cached + timedelta(days=1), end_date))

        return missing_ranges

    def _scrape_and_cache(
        self,
        symbol: str,
        ticker: str,
        start_date: date,
        end_date: date,
        source: str
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """Scrape new data and store in cache"""
        try:
            print(f"🔍 [Cache] Scraping {ticker} from {start_date} to {end_date}")

            # Scrape data
            scraped_df = self.scraper.fetch(ticker, start_date, end_date, frequency='daily')

            if scraped_df is None or len(scraped_df) == 0:
                print(f"⚠️ [Cache] No data scraped")
                return None, source

            print(f"✅ [Cache] Scraped {len(scraped_df)} rows")

            # Store in cache
            self._store_price_data(symbol, ticker, scraped_df, source)

            return scraped_df, source

        except Exception as e:
            print(f"❌ [Cache] Error scraping: {e}")
            return None, source

    def _scrape_and_cache_smart(
        self,
        symbol: str,
        ticker: str,
        start_date: date,
        end_date: date,
        source: str
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Smart scraping with automatic multi-phase backfill

        Strategy:
        1. Fetch recent priority period immediately (1 year)
        2. If older data needed, schedule incremental backfill
        3. Return complete data to user
        """
        days_requested = (end_date - start_date).days

        # If request is within safe limits, fetch directly
        if days_requested <= self.PRIORITY_FETCH_DAYS:
            print(f"🎯 [Cache] Range is safe ({days_requested} days), fetching directly")
            return self._scrape_and_cache(symbol, ticker, start_date, end_date, source)

        # For large ranges: fetch recent priority period first
        print(f"📊 [Cache] Large range ({days_requested} days) - multi-phase strategy")

        priority_start = end_date - timedelta(days=self.PRIORITY_FETCH_DAYS)
        if priority_start < start_date:
            priority_start = start_date

        # Phase 1: Fetch recent data (immediate response)
        scraped_df, _ = self._scrape_and_cache(symbol, ticker, priority_start, end_date, source)

        if scraped_df is None or len(scraped_df) == 0:
            print(f"⚠️ [Cache] Failed to fetch recent data")
            return None, source

        print(f"✅ [Cache] Phase 1: Fetched recent {len(scraped_df)} rows")

        # Phase 2: Backfill older data (if needed)
        if priority_start > start_date:
            older_data_needed_days = (priority_start - start_date).days
            print(f"📥 [Cache] Phase 2: Backfilling {older_data_needed_days} days of older data")

            # Backfill in reverse chronological order (chunks)
            self._backfill_older_data_chunked(
                symbol, ticker, start_date, priority_start - timedelta(days=1), source
            )

            # Re-fetch merged data from cache
            merged_df = self._get_cached_data(symbol, ticker, start_date, end_date, source)
            if merged_df is not None and len(merged_df) > len(scraped_df):
                print(f"✅ [Cache] Phase 2 complete: Total {len(merged_df)} rows")
                return merged_df, source

        # Return what we have (Phase 1 data)
        return scraped_df, source

    def _backfill_older_data_chunked(
        self,
        symbol: str,
        ticker: str,
        start_date: date,
        end_date: date,
        source: str
    ) -> int:
        """
        Backfill older data in reverse chronological chunks

        Strategy:
        - Work backwards from end_date to start_date
        - Fetch in BACKFILL_CHUNK_DAYS chunks (e.g., 365 days)
        - Stop if scraping fails (avoid triggering anti-bot)

        Returns:
            Total number of rows backfilled
        """
        total_backfilled = 0
        current_end = end_date

        while current_end >= start_date:
            # Calculate chunk range
            chunk_start = max(start_date, current_end - timedelta(days=self.BACKFILL_CHUNK_DAYS) + timedelta(days=1))

            print(f"📥 [Cache] Backfilling chunk: {chunk_start} to {current_end}")

            try:
                # Scrape chunk
                chunk_df, _ = self._scrape_and_cache(symbol, ticker, chunk_start, current_end, source)

                if chunk_df is not None and len(chunk_df) > 0:
                    total_backfilled += len(chunk_df)
                    print(f"✅ [Cache] Backfilled {len(chunk_df)} rows ({chunk_start} to {current_end})")
                else:
                    print(f"⚠️ [Cache] No data in chunk ({chunk_start} to {current_end}), stopping backfill")
                    break

                # Move to next chunk (earlier dates)
                current_end = chunk_start - timedelta(days=1)

                # Small delay to avoid anti-bot (only for multi-chunk backfills)
                if current_end >= start_date:
                    time.sleep(2)  # 2 second pause between chunks

            except Exception as e:
                print(f"❌ [Cache] Backfill failed at {chunk_start}: {e}, stopping")
                break

        print(f"📦 [Cache] Backfill complete: {total_backfilled} total rows added")
        return total_backfilled

    def _fill_gaps_incrementally(
        self,
        symbol: str,
        ticker: str,
        start_date: date,
        end_date: date,
        source: str
    ):
        """Fill missing date ranges incrementally (in chunks)"""
        try:
            # Get what's already cached
            cached_df = self._get_cached_data(symbol, ticker, start_date, end_date, source)

            if cached_df is None or len(cached_df) == 0:
                # No cache at all - fetch recent data first
                priority_start = max(start_date, end_date - timedelta(days=self.PRIORITY_FETCH_DAYS))
                self._scrape_and_cache(symbol, ticker, priority_start, end_date, source)
                return

            # Identify gaps
            first_cached = cached_df.index[0].date()
            last_cached = cached_df.index[-1].date()

            # Fill forward gap (newer data)
            if last_cached < end_date:
                print(f"📈 [Cache] Filling forward gap: {last_cached + timedelta(days=1)} to {end_date}")
                self._scrape_and_cache(symbol, ticker, last_cached + timedelta(days=1), end_date, source)

            # Fill backward gap (older data) - but limit to avoid anti-bot
            if first_cached > start_date:
                # Only fetch a chunk of old data at a time
                chunk_start = max(start_date, first_cached - timedelta(days=self.PRIORITY_FETCH_DAYS))
                if chunk_start < first_cached:
                    print(f"📉 [Cache] Filling backward gap (limited): {chunk_start} to {first_cached - timedelta(days=1)}")
                    self._scrape_and_cache(symbol, ticker, chunk_start, first_cached - timedelta(days=1), source)
                else:
                    print(f"⏸️ [Cache] Backward gap too large, skipping for now (will fetch incrementally later)")

        except Exception as e:
            print(f"❌ [Cache] Error filling gaps: {e}")

    def _store_price_data(
        self,
        symbol: str,
        ticker: str,
        df: pd.DataFrame,
        source: str
    ):
        """Store price data in cache"""
        try:
            now = datetime.now()
            stored_count = 0
            updated_count = 0

            for idx, row in df.iterrows():
                price_date = idx.date() if hasattr(idx, 'date') else idx

                # Check if record already exists
                existing = (
                    self.db.query(PriceHistory)
                    .filter(
                        and_(
                            PriceHistory.symbol == symbol,
                            PriceHistory.ticker == ticker,
                            PriceHistory.date == price_date,
                            PriceHistory.source == source
                        )
                    )
                    .first()
                )

                price_val = float(row['price']) if 'price' in row and pd.notna(row['price']) else None
                nav_val = float(row['nav']) if 'nav' in row and pd.notna(row['nav']) else None
                diff_val = float(row['diff']) if 'diff' in row and pd.notna(row['diff']) else None
                aum_val = float(row['aum_million']) if 'aum_million' in row and pd.notna(row['aum_million']) else None

                if existing:
                    # Update existing record
                    existing.price = price_val
                    existing.nav = nav_val
                    existing.diff = diff_val
                    existing.aum_million = aum_val
                    existing.updated_at = now
                    existing.last_verified_at = now
                    updated_count += 1
                else:
                    # Insert new record
                    new_record = PriceHistory(
                        symbol=symbol,
                        ticker=ticker,
                        date=price_date,
                        price=price_val,
                        nav=nav_val,
                        diff=diff_val,
                        aum_million=aum_val,
                        source=source,
                        currency='JPY',
                        last_verified_at=now
                    )
                    self.db.add(new_record)
                    stored_count += 1

            self.db.commit()
            print(f"💾 [Cache] Stored {stored_count} new, updated {updated_count} existing rows")

        except Exception as e:
            print(f"❌ [Cache] Error storing data: {e}")
            self.db.rollback()

    def _update_forward(self, symbol: str, ticker: str, source: str) -> int:
        """Scrape new data since last cached date"""
        try:
            # Get latest cached date
            latest = (
                self.db.query(func.max(PriceHistory.date))
                .filter(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.ticker == ticker,
                        PriceHistory.source == source
                    )
                )
                .scalar()
            )

            if latest is None:
                print(f"⚠️ [Cache] No cached data found for forward update")
                return 0

            today = date.today()
            if latest >= today:
                print(f"✅ [Cache] Already up to date")
                return 0

            # Scrape from latest + 1 day to today
            start_date = latest + timedelta(days=1)
            print(f"🔄 [Cache] Updating forward from {start_date} to {today}")

            scraped_df, _ = self._scrape_and_cache(symbol, ticker, start_date, today, source)

            if scraped_df is not None:
                return len(scraped_df)

            return 0

        except Exception as e:
            print(f"❌ [Cache] Error in forward update: {e}")
            return 0

    def clear_cache(self, symbol: Optional[str] = None, ticker: Optional[str] = None):
        """Clear cached data (for testing or manual refresh)"""
        try:
            query = self.db.query(PriceHistory)

            if symbol:
                query = query.filter(PriceHistory.symbol == symbol)
            if ticker:
                query = query.filter(PriceHistory.ticker == ticker)

            deleted = query.delete()
            self.db.commit()

            print(f"🗑️ [Cache] Cleared {deleted} cached records")
            return deleted

        except Exception as e:
            print(f"❌ [Cache] Error clearing cache: {e}")
            self.db.rollback()
            return 0
