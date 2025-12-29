"""Transaction Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    id: UUID
    portfolio_id: UUID
    transaction_date: date
    symbol: str
    name: str
    side: str = Field(..., description="BUY, SELL, or OTHER")
    transaction_type: Optional[str] = Field(None, description="Original transaction type from CSV")
    quantity: Decimal
    amount_jpy: Decimal
    market: str = Field(..., description="US, JP, or INVST")
    asset_class: Optional[str] = Field(None, description="Equity, Bond, REIT, or Commodity")
    raw_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174001",
                "transaction_date": "2023-01-15",
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "side": "BUY",
                "transaction_type": "買",
                "quantity": "10.0",
                "amount_jpy": "250000.0",
                "market": "US",
                "asset_class": "Equity"
            }
        }
