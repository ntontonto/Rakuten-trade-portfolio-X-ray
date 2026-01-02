"""Analysis and Chart Schemas"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date


class CashFlowItem(BaseModel):
    """Single cash flow for XIRR calculation"""
    date: date
    amount: float


class XIRRRequest(BaseModel):
    """Request schema for XIRR calculation"""
    cash_flows: List[CashFlowItem] = Field(..., min_length=2)
    guess: float = Field(default=0.1, description="Initial guess for XIRR")

    class Config:
        json_schema_extra = {
            "example": {
                "cash_flows": [
                    {"date": "2023-01-01", "amount": -1000},
                    {"date": "2023-06-01", "amount": 100},
                    {"date": "2024-01-01", "amount": 1200}
                ],
                "guess": 0.1
            }
        }


class XIRRResponse(BaseModel):
    """Response schema for XIRR calculation"""
    xirr: Optional[float] = Field(None, description="Calculated XIRR (decimal)")
    xirr_percent: Optional[str] = Field(None, description="Formatted XIRR as percentage")
    success: bool = Field(..., description="Whether calculation succeeded")
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "xirr": 0.1234,
                "xirr_percent": "12.34%",
                "success": True,
                "message": "XIRR calculated successfully"
            }
        }


class AllocationData(BaseModel):
    """Allocation breakdown by category"""
    labels: List[str]
    values: List[float]
    colors: List[str]


class ChartData(BaseModel):
    """Generic chart data response"""
    chart_type: str = Field(..., description="Type of chart: pie, bar, line, scatter, etc.")
    data: Dict[str, Any] = Field(..., description="Chart-specific data structure")


class PortfolioMetrics(BaseModel):
    """Comprehensive portfolio metrics for dashboard"""
    # KPI Metrics
    total_xirr: float
    total_current_value: float
    total_invested: float
    points_invested: float
    total_invested_with_points: float
    total_unrealized_pl: float
    total_realized_pl: float
    return_rate: float

    # Allocations
    allocation_by_class: AllocationData
    allocation_by_strategy: AllocationData

    # Performance by Class
    xirr_by_class: Dict[str, float]

    # Monthly Flow Data
    monthly_flow: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Monthly investment flow: {YYYY-MM: {core: xxx, satellite: yyy}}"
    )

    # Top Performers
    top_performers: List[Dict[str, Any]] = Field(
        ...,
        description="Top 5 holdings by XIRR"
    )

    # Additional chart data
    realized_pl_by_class: Optional[Dict[str, float]] = Field(
        default={},
        description="Realized P&L by asset class"
    )
    cumulative_strategy: Optional[Dict[str, Any]] = Field(
        default={},
        description="Cumulative strategy performance over time"
    )
    win_rate: Optional[Dict[str, Any]] = Field(
        default={},
        description="Win rate data"
    )
    scatter_data: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="Scatter plot data: holding period vs XIRR"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_xirr": 0.1234,
                "total_current_value": 5000000,
                "total_invested": 4200000,
                "total_unrealized_pl": 800000,
                "total_realized_pl": 50000,
                "return_rate": 0.1905,
                "allocation_by_class": {
                    "labels": ["Equity", "Bond", "REIT"],
                    "values": [3000000, 1500000, 500000],
                    "colors": ["#3b82f6", "#10b981", "#f59e0b"]
                },
                "allocation_by_strategy": {
                    "labels": ["Core", "Satellite"],
                    "values": [4000000, 1000000],
                    "colors": ["#6366f1", "#f43f5e"]
                },
                "xirr_by_class": {
                    "Equity": 0.15,
                    "Bond": 0.05,
                    "REIT": 0.08
                },
                "monthly_flow": {
                    "2023-01": {"core": 100000, "satellite": 50000},
                    "2023-02": {"core": 150000, "satellite": 30000}
                },
                "top_performers": [
                    {"symbol": "VTI", "name": "Vanguard Total Stock", "xirr": 0.25},
                    {"symbol": "BND", "name": "Vanguard Total Bond", "xirr": 0.08}
                ]
            }
        }


class PriceHistoryPoint(BaseModel):
    """Single data point for a holding's price/value history"""
    date: date
    price_jpy: Optional[float] = Field(
        None, description="Price converted to JPY when available"
    )
    price_raw: float = Field(
        ..., description="Raw price in the asset's trading currency"
    )
    fx_rate: Optional[float] = Field(
        None, description="FX rate used (JPY per unit of raw currency)"
    )
    quantity: Optional[float] = Field(
        None, description="Quantity held on this date (after transactions)"
    )
    value_jpy: Optional[float] = Field(
        None, description="Position value in JPY (price_jpy * quantity)"
    )


class PriceHistoryResponse(BaseModel):
    """Price history response for a holding"""
    source: str = Field(..., description="Data source: yahoo, nav, interpolated, none")
    currency: str = Field(..., description="Raw price currency, e.g., USD or JPY")
    points: List[PriceHistoryPoint]

    class Config:
        json_schema_extra = {
            "example": {
                "source": "yahoo",
                "currency": "USD",
                "points": [
                    {
                        "date": "2024-01-01",
                        "price_raw": 100.5,
                        "fx_rate": 150.2,
                        "price_jpy": 15030.1,
                        "quantity": 12.3,
                        "value_jpy": 184869.23
                    }
                ]
            }
        }


class PortfolioTimelinePoint(BaseModel):
    """Daily portfolio timeline point"""
    date: date
    invested_cumulative_jpy: float
    total_value_jpy: float


class PortfolioTimelineResponse(BaseModel):
    """Daily cumulative invested vs total portfolio value"""
    points: List[PortfolioTimelinePoint]

    class Config:
        json_schema_extra = {
            "example": {
                "points": [
                    {
                        "date": "2024-01-01",
                        "invested_cumulative_jpy": 100000,
                        "total_value_jpy": 105000
                    },
                    {
                        "date": "2024-01-02",
                        "invested_cumulative_jpy": 150000,
                        "total_value_jpy": 152500
                    }
                ]
            }
        }


class InvestmentTimelinePoint(BaseModel):
    """Per-day invested vs valuation for a holding"""
    date: date
    invested_cumulative_jpy: float
    value_jpy: float


class InvestmentTimelineResponse(BaseModel):
    """Daily investment vs valuation timeline for a holding"""
    points: List[InvestmentTimelinePoint]

    class Config:
        json_schema_extra = {
            "example": {
                "points": [
                    {"date": "2024-01-01", "invested_cumulative_jpy": 100000, "value_jpy": 102500},
                    {"date": "2024-01-02", "invested_cumulative_jpy": 120000, "value_jpy": 125000}
                ]
            }
        }
