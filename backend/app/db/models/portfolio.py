"""Portfolio Model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Portfolio(Base):
    """
    Portfolio represents a collection of investments

    A user can have multiple portfolios (e.g., retirement, taxable, etc.)
    """
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Future: FK to users table
    name = Column(String(255), nullable=False, default="Main Portfolio")

    # Metadata (JSONB for flexibility)
    # Stores: exchange_rates, settings, custom_mappings, etc.
    metadata_json = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"
