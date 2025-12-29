"""Portfolio Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PortfolioBase(BaseModel):
    """Base portfolio schema"""
    name: str = Field(default="Main Portfolio", max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class PortfolioCreate(PortfolioBase):
    """Schema for creating a portfolio"""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio"""
    name: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response"""
    id: UUID
    user_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_json")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class PortfolioSummary(BaseModel):
    """Summary metrics for a portfolio"""
    portfolio_id: UUID
    total_xirr: float = Field(..., description="Overall portfolio XIRR (annualized return)")
    total_current_value: float = Field(..., description="Current market value in JPY")
    total_invested: float = Field(..., description="Total amount invested in JPY")
    total_unrealized_pl: float = Field(..., description="Unrealized profit/loss in JPY")
    total_realized_pl: float = Field(..., description="Realized profit/loss in JPY")
    return_rate: float = Field(..., description="Simple return rate (not annualized)")
    holdings_count: int = Field(..., description="Number of current holdings")
    last_calculated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_xirr": 0.1234,
                "total_current_value": 5000000,
                "total_invested": 4200000,
                "total_unrealized_pl": 800000,
                "total_realized_pl": 50000,
                "return_rate": 0.1905,
                "holdings_count": 15,
                "last_calculated_at": "2025-12-27T10:00:00Z"
            }
        }
