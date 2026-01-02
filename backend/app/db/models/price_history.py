"""Price History Model"""
from sqlalchemy import Column, String, Date, Numeric, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class PriceHistory(Base):
    """
    Historical price data cache

    Stores scraped/fetched price data to avoid repeated scraping
    """
    __tablename__ = "price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    symbol = Column(String(100), nullable=False, index=True)
    ticker = Column(String(100), nullable=False, index=True)

    # Price data
    date = Column(Date, nullable=False, index=True)
    price = Column(Numeric(20, 4), nullable=False)
    nav = Column(Numeric(20, 4), nullable=True)
    diff = Column(Numeric(20, 4), nullable=True)
    aum_million = Column(Numeric(20, 4), nullable=True)

    # Metadata
    source = Column(String(50), nullable=False, index=True)
    currency = Column(String(10), default='JPY')

    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('symbol', 'ticker', 'date', 'source', name='uq_price_history_symbol_ticker_date_source'),
        Index('idx_price_history_symbol_date', 'symbol', 'date'),
        Index('idx_price_history_ticker_date', 'ticker', 'date'),
        Index('idx_price_history_source', 'source'),
    )
