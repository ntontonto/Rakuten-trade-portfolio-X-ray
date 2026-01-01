"""
Secondary market data fetcher with provider failover.

Supports:
- Twelve Data (preferred if API key provided)
- Alpha Vantage (fallback if Twelve Data not configured)

All calls are throttled with a simple in-process cache to reduce duplicate
requests for identical (ticker, start_date, end_date) ranges.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Optional, Tuple, Dict

import pandas as pd
import httpx


class SecondaryPriceFetcher:
    """Fetch daily prices from alternative providers."""

    def __init__(self):
        self.twelve_data_key = os.getenv("TWELVE_DATA_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self._cache: Dict[Tuple[str, date, date], Optional[pd.DataFrame]] = {}
        self._client = httpx.Client(timeout=15.0)

    def fetch(self, ticker: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """
        Try configured providers in order: Twelve Data -> Alpha Vantage.

        Returns DataFrame with Date index and 'price' column, or None on failure.
        """
        cache_key = (ticker, start_date, end_date)
        if cache_key in self._cache:
            return self._cache[cache_key]

        df = None
        if self.twelve_data_key:
            df = self._fetch_twelve_data(ticker, start_date, end_date)

        if df is None and self.alpha_vantage_key:
            df = self._fetch_alpha_vantage(ticker, start_date, end_date)

        self._cache[cache_key] = df
        return df

    def _fetch_twelve_data(self, ticker: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch via Twelve Data time_series endpoint."""
        try:
            params = {
                "symbol": ticker,
                "interval": "1day",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "apikey": self.twelve_data_key,
                "dp": 6,
                "order": "ASC",
            }
            resp = self._client.get("https://api.twelvedata.com/time_series", params=params)
            resp.raise_for_status()
            data = resp.json()
            values = data.get("values") or []
            if not values:
                return None
            records = []
            for row in values:
                # row["datetime"] format: "2024-01-01"
                d = datetime.fromisoformat(row["datetime"]).date()
                if d < start_date or d > end_date:
                    continue
                records.append({"date": d, "price": float(row["close"])})
            if not records:
                return None
            df = pd.DataFrame(records).set_index("date")
            df.index.name = "date"
            return df
        except Exception as exc:  # pragma: no cover - network path
            print(f"❌ Twelve Data fetch failed for {ticker}: {exc}")
            return None

    def _fetch_alpha_vantage(self, ticker: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """Fetch via Alpha Vantage TIME_SERIES_DAILY_ADJUSTED."""
        try:
            params = {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": ticker,
                "outputsize": "full",
                "apikey": self.alpha_vantage_key,
            }
            resp = self._client.get("https://www.alphavantage.co/query", params=params)
            resp.raise_for_status()
            data = resp.json()
            series = data.get("Time Series (Daily)") or {}
            if not series:
                return None
            records = []
            for day_str, row in series.items():
                d = datetime.fromisoformat(day_str).date()
                if d < start_date or d > end_date:
                    continue
                records.append({"date": d, "price": float(row["4. close"])})
            if not records:
                return None
            records.sort(key=lambda r: r["date"])
            df = pd.DataFrame(records).set_index("date")
            df.index.name = "date"
            return df
        except Exception as exc:  # pragma: no cover - network path
            print(f"❌ Alpha Vantage fetch failed for {ticker}: {exc}")
            return None
