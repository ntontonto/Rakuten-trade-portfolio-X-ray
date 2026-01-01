"""
Unit tests for HistoricalPriceService without hitting external APIs.

We stub Yahoo Finance and DB session to validate the tiered
logic (yahoo -> nav -> interpolation) and price interpolation behavior.
"""
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.price_fetcher import HistoricalPriceService


class FakeSession:
    """Minimal session stub to satisfy .query(...).filter(...).order_by(...).all()."""

    def __init__(self, items):
        self.items = items
        self._added = []

    def query(self, _model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self.items

    def first(self):
        """Return first item or None"""
        return None

    def add(self, obj):
        """Add object to session"""
        self._added.append(obj)

    def commit(self):
        """Commit transaction (no-op in mock)"""
        pass

    def rollback(self):
        """Rollback transaction (no-op in mock)"""
        pass


class StubFetcher:
    """Stub for YahooFinanceFetcher.fetch returning pre-seeded DataFrames."""

    def __init__(self, results):
        self.results = results
        self.calls = []

    def fetch(self, ticker, start_date, end_date):
        self.calls.append((ticker, start_date, end_date))
        return self.results.get(ticker)


@pytest.fixture
def sample_dates():
    return date(2024, 1, 1), date(2024, 1, 5)


def test_tier1_uses_yahoo_when_available(monkeypatch, sample_dates):
    """HistoricalPriceService should return Yahoo data when mapping and data exist."""
    start_date, end_date = sample_dates
    yahoo_df = pd.DataFrame({"price": [100, 101]}, index=pd.date_range(start_date, periods=2, freq="D"))

    service = HistoricalPriceService(db=FakeSession([]))
    stub_fetcher = StubFetcher({"VTI": yahoo_df})
    service.yahoo_fetcher = stub_fetcher

    # Force ticker mapping to succeed
    monkeypatch.setattr("app.services.price_fetcher.get_yahoo_ticker", lambda symbol: "VTI")

    prices, source = service.get_price_history(
        symbol="VTI",
        name="Vanguard",
        start_date=start_date,
        end_date=end_date,
        portfolio_id="p1",
    )

    assert source == "yahoo"
    assert prices is not None
    assert len(prices) == 2
    assert stub_fetcher.calls  # ensured call was made


def test_tier2_interpolates_when_no_sources(monkeypatch):
    """Service should fall back to linear interpolation using transaction prices."""
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)

    # Disable yahoo
    monkeypatch.setattr("app.services.price_fetcher.get_yahoo_ticker", lambda symbol: None)

    # Transactions on day 1 (price 100) and day 3 (price 200)
    tx1 = SimpleNamespace(transaction_date=start_date, amount_jpy=100, quantity=1)
    tx2 = SimpleNamespace(transaction_date=end_date, amount_jpy=200, quantity=1)
    service = HistoricalPriceService(db=FakeSession([tx1, tx2]))

    # Force yahoo fetcher to return None
    service.yahoo_fetcher = StubFetcher({})

    prices, source = service.get_price_history(
        symbol="NO_TICKER",
        name="Unknown Asset",
        start_date=start_date,
        end_date=end_date,
        portfolio_id="p1",
    )

    assert source == "interpolated"
    assert prices is not None
    # Interpolated series should form a straight line: 100, 150, 200
    values = prices["price"].tolist()
    assert len(values) == 3
    assert pytest.approx(values[0], rel=1e-6) == 100
    assert pytest.approx(values[1], rel=1e-6) == 150
    assert pytest.approx(values[2], rel=1e-6) == 200
