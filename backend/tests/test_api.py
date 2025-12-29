"""
API integration tests using FastAPI TestClient with an in-memory SQLite DB.

Alembic migrations are intentionally skipped; tables are created directly from
SQLAlchemy models for fast, isolated tests.
"""
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db_session
from app.db.base import Base
from app.db.models import Portfolio, Transaction
from app.services.portfolio_aggregator import PortfolioAggregator


# Create an in-memory SQLite engine for tests
SQLALCHEMY_TEST_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Share the same in-memory DB across connections
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


# Render PostgreSQL UUID columns as CHAR(36) when using SQLite for tests
@compiles(PGUUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):  # noqa: D401
    """Compile PostgreSQL UUID type for SQLite test DB."""
    return "CHAR(36)"


@pytest.fixture(autouse=True)
def reset_database():
    """Ensure a clean schema before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session bound to the in-memory test DB."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """
    FastAPI TestClient with dependency override to use the test session.
    """

    def override_get_db_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_xirr_endpoint(client):
    """POST /api/v1/analysis/xirr returns a successful calculation."""
    payload = {
        "cash_flows": [
            {"date": "2023-01-01", "amount": -1000},
            {"date": "2024-01-01", "amount": 1200},
        ],
        "guess": 0.1,
    }

    resp = client.post("/api/v1/analysis/xirr", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["xirr"] is not None
    assert data["xirr_percent"].endswith("%")


def test_portfolio_summary_flow(client, db_session):
    """
    Create a portfolio, seed transactions, aggregate holdings, and fetch summary.
    """
    # Create portfolio
    create_resp = client.post("/api/v1/portfolios", json={"name": "Test Portfolio"})
    assert create_resp.status_code == 201
    portfolio_id = UUID(create_resp.json()["id"])

    # Seed a BUY and a SELL to produce P&L/XIRR
    tx_buy = Transaction(
        portfolio_id=portfolio_id,
        transaction_date=date(2023, 1, 1),
        symbol="VTI",
        name="Vanguard Total Stock Market ETF",
        side="BUY",
        transaction_type="買",
        quantity=Decimal("10"),
        amount_jpy=Decimal("200000"),
        market="US",
        asset_class="Equity",
        raw_data={},
    )
    tx_sell = Transaction(
        portfolio_id=portfolio_id,
        transaction_date=date(2024, 1, 1),
        symbol="VTI",
        name="Vanguard Total Stock Market ETF",
        side="SELL",
        transaction_type="売",
        quantity=Decimal("5"),
        amount_jpy=Decimal("130000"),
        market="US",
        asset_class="Equity",
        raw_data={},
    )
    db_session.add_all([tx_buy, tx_sell])
    db_session.commit()

    # Aggregate into holdings
    aggregator = PortfolioAggregator(db_session)
    holdings = aggregator.process_portfolio(portfolio_id)
    assert holdings, "Holdings should be created from transactions"

    # Fetch summary endpoint
    summary_resp = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()

    assert UUID(summary["portfolio_id"]) == portfolio_id
    assert summary["holdings_count"] == len(holdings)
    assert summary["total_invested"] > 0
    assert summary["total_current_value"] >= 0


def test_upload_csv_creates_holdings(client):
    """
    POST /api/v1/upload/csv processes a simple transaction CSV and creates a portfolio.
    """
    csv_content = (
        "約定日,ティッカー,銘柄名,売買区分,数量［株］,受渡金額［円］,為替レート\n"
        "2023/01/01,VTI,Vanguard Total Stock,買,1,10000,130\n"
    )

    files = [
        ("files", ("transactions.csv", csv_content.encode("utf-8"), "text/csv")),
    ]

    resp = client.post("/api/v1/upload/csv", files=files)
    assert resp.status_code == 200
    body = resp.json()

    assert body["success"] is True
    assert body["transactions_imported"] == 1
    assert body["holdings_created"] >= 1
    assert "portfolio_id" in body and body["portfolio_id"]
