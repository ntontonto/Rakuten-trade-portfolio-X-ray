"""Transaction Model"""
import uuid
from sqlalchemy import Column, String, Date, Numeric, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Transaction(Base):
    """
    Transaction represents a single buy/sell/dividend event

    Captures all transaction history from CSV imports
    """
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)

    # Core Fields
    transaction_date = Column(Date, nullable=False)
    symbol = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Transaction Details
    side = Column(String(10), nullable=False)  # 'BUY', 'SELL', 'OTHER'
    transaction_type = Column(String(50), nullable=True)  # Original transaction type from CSV (買, 売, etc.)
    quantity = Column(Numeric(18, 6), nullable=False)
    amount_jpy = Column(Numeric(18, 2), nullable=False)

    # Classification
    market = Column(String(10), nullable=False)  # 'US', 'JP', 'INVST'
    asset_class = Column(String(20), nullable=True)  # 'Equity', 'Bond', 'REIT', 'Commodity'

    # Raw Data (JSONB for flexibility)
    # Stores original CSV row for reference
    raw_data = Column(JSON, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_transaction_portfolio_symbol', 'portfolio_id', 'symbol'),
        Index('idx_transaction_date', 'transaction_date'),
    )

    def __repr__(self):
        return f"<Transaction(symbol='{self.symbol}', side='{self.side}', date={self.transaction_date})>"
