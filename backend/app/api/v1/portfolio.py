"""Portfolio CRUD Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db_session, get_portfolio
from app.db.models import Portfolio, Holding
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioSummary
)
from app.schemas.holding import HoldingResponse, HoldingUpdate
from app.services.portfolio_aggregator import PortfolioAggregator

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """List all portfolios"""
    portfolios = db.query(Portfolio).offset(skip).limit(limit).all()
    return portfolios


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_in: PortfolioCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new portfolio"""
    portfolio = Portfolio(
        name=portfolio_in.name,
        metadata_json=portfolio_in.metadata
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio_detail(
    portfolio: Portfolio = Depends(get_portfolio)
):
    """Get portfolio details by ID"""
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_in: PortfolioUpdate,
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Update portfolio"""
    if portfolio_in.name is not None:
        portfolio.name = portfolio_in.name
    if portfolio_in.metadata is not None:
        portfolio.metadata_json = portfolio_in.metadata

    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Delete portfolio"""
    db.delete(portfolio)
    db.commit()
    return None


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Get portfolio summary with key metrics"""
    aggregator = PortfolioAggregator(db)
    summary = aggregator.get_portfolio_summary(portfolio.id)
    return summary


@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
def get_holdings(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Get all holdings for a portfolio"""
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio.id)
        .all()
    )
    return holdings


@router.put("/{portfolio_id}/holdings/{symbol}/price", response_model=HoldingResponse)
def update_holding_price(
    portfolio_id: UUID,
    symbol: str,
    price_update: HoldingUpdate,
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Update current price for a holding

    Triggers XIRR recalculation
    """
    aggregator = PortfolioAggregator(db)
    holding = aggregator.update_holding_price(
        portfolio_id,
        symbol,
        price_update.current_price,
        auto_updated=False
    )

    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {symbol} not found in portfolio {portfolio_id}"
        )

    return holding


@router.post("/{portfolio_id}/holdings/bulk-update-prices")
def bulk_update_prices(
    portfolio_id: UUID,
    updates: dict,  # {symbol: new_price}
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Bulk update prices for multiple holdings

    Example:
        {
            "VTI": 250.50,
            "BND": 75.25,
            "GLD": 180.00
        }
    """
    aggregator = PortfolioAggregator(db)
    results = []

    for symbol, price in updates.items():
        holding = aggregator.update_holding_price(
            portfolio_id,
            symbol,
            price,
            auto_updated=False
        )
        if holding:
            results.append({
                "symbol": symbol,
                "success": True,
                "new_price": float(price)
            })
        else:
            results.append({
                "symbol": symbol,
                "success": False,
                "error": "Holding not found"
            })

    return {
        "updated": len([r for r in results if r['success']]),
        "failed": len([r for r in results if not r['success']]),
        "results": results
    }
