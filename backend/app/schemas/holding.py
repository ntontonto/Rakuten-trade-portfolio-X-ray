"""Holding Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class HoldingUpdate(BaseModel):
    """Schema for updating a holding's current price"""
    current_price: Decimal = Field(..., gt=0, description="Current market price per unit")


class HoldingResponse(BaseModel):
    """Schema for holding response"""
    id: UUID
    portfolio_id: UUID
    symbol: str
    name: str
    quantity: Decimal
    average_cost: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    invested_amount: Optional[Decimal] = None
    points_invested: Optional[Decimal] = Field(None, description="Rakuten points used for this holding (BUYs)")
    invested_amount_with_points: Optional[Decimal] = Field(None, description="Invested amount including points")
    unrealized_pl: Optional[Decimal] = None
    realized_pl: Optional[Decimal] = None
    xirr: Optional[Decimal] = Field(None, description="Internal rate of return (decimal, e.g., 0.1234 = 12.34%)")
    asset_class: Optional[str] = None
    strategy: Optional[str] = Field(None, description="Core or Satellite")
    market: Optional[str] = None
    first_purchase_date: Optional[date] = None
    last_transaction_date: Optional[date] = None
    holding_days: Optional[int] = None
    is_price_auto_updated: bool = False

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174001",
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "quantity": "50.5",
                "average_cost": "220.50",
                "current_price": "250.00",
                "current_value": "12625.00",
                "invested_amount": "11135.25",
                "unrealized_pl": "1489.75",
                "realized_pl": "0.00",
                "xirr": "0.1234",
                "asset_class": "Equity",
                "strategy": "Core",
                "market": "US",
                "first_purchase_date": "2023-01-15",
                "last_transaction_date": "2023-06-20",
                "holding_days": 365,
                "is_price_auto_updated": True
            }
        }
