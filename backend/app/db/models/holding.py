"""Holding Model"""
import uuid
from sqlalchemy import Column, String, Date, Numeric, Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Holding(Base):
    """
    Holding represents current positions in the portfolio

    Aggregated from transactions and updated with current prices
    """
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)

    # Security Identification
    symbol = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Position Data
    quantity = Column(Numeric(18, 6), nullable=False, default=0)
    average_cost = Column(Numeric(18, 6), nullable=True)  # Average cost per unit
    current_price = Column(Numeric(18, 6), nullable=True)  # Current market price
    current_value = Column(Numeric(18, 2), nullable=True)  # quantity * current_price

    # Performance Metrics
    invested_amount = Column(Numeric(18, 2), nullable=True)  # Total invested (cost basis)
    unrealized_pl = Column(Numeric(18, 2), nullable=True)    # Current P&L (not sold)
    realized_pl = Column(Numeric(18, 2), nullable=True)      # Realized P&L (from sales)
    xirr = Column(Numeric(8, 6), nullable=True)              # Internal rate of return (decimal)

    # Classification
    asset_class = Column(String(20), nullable=True)  # 'Equity', 'Bond', 'REIT', 'Commodity'
    strategy = Column(String(20), nullable=True)     # 'Core', 'Satellite'
    market = Column(String(10), nullable=True)       # 'US', 'JP', 'INVST'

    # Metadata
    first_purchase_date = Column(Date, nullable=True)
    last_transaction_date = Column(Date, nullable=True)
    holding_days = Column(Integer, nullable=True)
    is_price_auto_updated = Column(Boolean, default=False)  # True if price from balance CSV

    # Timestamps
    last_calculated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    predictions = relationship("Prediction", back_populates="holding", cascade="all, delete-orphan")

    # Unique constraint: one holding per symbol per portfolio
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'symbol', name='uq_portfolio_symbol'),
    )

    def __repr__(self):
        return f"<Holding(symbol='{self.symbol}', qty={self.quantity}, value={self.current_value})>"
