"""Prediction Model (for ML outputs)"""
import uuid
from sqlalchemy import Column, String, Date, Numeric, JSON, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Prediction(Base):
    """
    Prediction stores ML model outputs

    Supports multiple model types:
    - price_forecast: Future price predictions
    - risk_score: Risk analysis results
    - optimization: Portfolio optimization suggestions
    """
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=True)
    holding_id = Column(UUID(as_uuid=True), ForeignKey("holdings.id", ondelete="CASCADE"), nullable=True)

    # Prediction Details
    model_type = Column(String(50), nullable=False)  # 'price_forecast', 'risk_score', 'optimization'
    model_version = Column(String(50), nullable=True)  # e.g., "prophet-1.0", "xgboost-2.0"

    # Outputs (flexible JSONB)
    # For forecasts: {"dates": [...], "prices": [...], "lower_bounds": [...], "upper_bounds": [...]}
    # For risk: {"risk_score": 0.65, "risk_level": "high", "factors": [...]}
    # For optimization: {"suggestions": [...], "sharpe_improvement": 0.3}
    prediction_data = Column(JSON, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=True)  # Confidence score (0-1)

    # Time Series (for forecasts)
    forecast_horizon_days = Column(Integer, nullable=True)  # How many days ahead
    predicted_for_date = Column(Date, nullable=True)        # Specific prediction date

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When to refresh prediction

    # Relationships
    portfolio = relationship("Portfolio", back_populates="predictions")
    holding = relationship("Holding", back_populates="predictions")

    # Indexes for queries
    __table_args__ = (
        Index('idx_portfolio_predictions', 'portfolio_id', 'model_type'),
        Index('idx_holding_predictions', 'holding_id'),
        Index('idx_predictions_unexpired', 'portfolio_id', 'model_type', 'expires_at'),
    )

    def __repr__(self):
        return f"<Prediction(type='{self.model_type}', confidence={self.confidence})>"
