"""Analysis and Charts Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID
from datetime import datetime
from collections import defaultdict

from app.api.deps import get_db_session, get_portfolio
from app.db.models import Portfolio, Holding, Transaction
from app.schemas.analysis import (
    XIRRRequest,
    XIRRResponse,
    PortfolioMetrics,
    AllocationData,
    ChartData
)
from app.services.xirr_calculator import CashFlow, calculate_xirr, format_xirr
from app.services.asset_classifier import get_asset_class_color, get_strategy_color
from app.services.portfolio_aggregator import PortfolioAggregator

router = APIRouter(tags=["analysis"])


@router.post("/analysis/xirr", response_model=XIRRResponse)
def calculate_xirr_endpoint(request: XIRRRequest):
    """
    Calculate XIRR from provided cash flows

    This is a standalone endpoint for XIRR calculation.
    For portfolio-level XIRR, use `/portfolios/{id}/summary`

    Example:
        ```json
        {
          "cash_flows": [
            {"date": "2023-01-01", "amount": -1000},
            {"date": "2023-06-01", "amount": 100},
            {"date": "2024-01-01", "amount": 1200}
          ]
        }
        ```
    """
    cash_flows = [
        CashFlow(
            date=datetime.combine(cf.date, datetime.min.time()),
            amount=cf.amount
        )
        for cf in request.cash_flows
    ]

    xirr = calculate_xirr(cash_flows, guess=request.guess)

    if xirr is None:
        return XIRRResponse(
            xirr=None,
            xirr_percent=None,
            success=False,
            message="XIRR calculation failed to converge. Check your cash flows."
        )

    return XIRRResponse(
        xirr=xirr,
        xirr_percent=format_xirr(xirr),
        success=True,
        message="XIRR calculated successfully"
    )


@router.get("/portfolios/{portfolio_id}/analysis/metrics", response_model=PortfolioMetrics)
def get_portfolio_metrics(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Get comprehensive portfolio metrics for dashboard

    Returns:
    - KPI metrics (XIRR, total value, P&L)
    - Asset allocation by class and strategy
    - XIRR by asset class
    - Monthly investment flow
    - Top 5 performers
    """
    aggregator = PortfolioAggregator(db)
    summary = aggregator.get_portfolio_summary(portfolio.id)

    # Get holdings
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio.id)
        .all()
    )

    # Allocation by asset class
    class_allocation = defaultdict(float)
    class_colors = []
    for h in holdings:
        class_allocation[h.asset_class or 'Other'] += float(h.current_value or 0)

    allocation_by_class = AllocationData(
        labels=list(class_allocation.keys()),
        values=list(class_allocation.values()),
        colors=[get_asset_class_color(c) for c in class_allocation.keys()]
    )

    # Allocation by strategy
    strategy_allocation = defaultdict(float)
    for h in holdings:
        strategy_allocation[h.strategy or 'Other'] += float(h.current_value or 0)

    allocation_by_strategy = AllocationData(
        labels=list(strategy_allocation.keys()),
        values=list(strategy_allocation.values()),
        colors=[get_strategy_color(s) for s in strategy_allocation.keys()]
    )

    # XIRR by asset class
    xirr_by_class = {}
    for asset_class in class_allocation.keys():
        class_holdings = [h for h in holdings if h.asset_class == asset_class]
        if not class_holdings:
            continue

        # Get all transactions for this asset class
        symbols = [h.symbol for h in class_holdings]
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.portfolio_id == portfolio.id,
                Transaction.symbol.in_(symbols)
            )
            .all()
        )

        # Build cash flows
        cash_flows = []
        for tx in transactions:
            if tx.side == 'BUY':
                cash_flows.append(CashFlow(
                    date=datetime.combine(tx.transaction_date, datetime.min.time()),
                    amount=-float(tx.amount_jpy)
                ))
            elif tx.side == 'SELL':
                cash_flows.append(CashFlow(
                    date=datetime.combine(tx.transaction_date, datetime.min.time()),
                    amount=float(tx.amount_jpy)
                ))

        # Add current value
        current_value = sum(float(h.current_value or 0) for h in class_holdings)
        if current_value > 0:
            cash_flows.append(CashFlow(date=datetime.now(), amount=current_value))

        xirr = calculate_xirr(cash_flows) or 0.0
        xirr_by_class[asset_class] = xirr

    # Monthly flow data
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.portfolio_id == portfolio.id,
            Transaction.side == 'BUY'
        )
        .all()
    )

    monthly_flow = defaultdict(lambda: {'core': 0.0, 'satellite': 0.0})
    for tx in transactions:
        month_key = tx.transaction_date.strftime('%Y-%m')
        holding = next((h for h in holdings if h.symbol == tx.symbol), None)
        strategy = holding.strategy if holding else 'satellite'

        if strategy == 'Core':
            monthly_flow[month_key]['core'] += float(tx.amount_jpy)
        else:
            monthly_flow[month_key]['satellite'] += float(tx.amount_jpy)

    # Top 5 performers by XIRR
    top_performers = sorted(
        [
            {
                'symbol': h.symbol,
                'name': h.name,
                'xirr': float(h.xirr or 0),
                'current_value': float(h.current_value or 0)
            }
            for h in holdings if h.xirr is not None
        ],
        key=lambda x: x['xirr'],
        reverse=True
    )[:5]

    # Calculate scatter data (holding period vs XIRR)
    scatter_data = [
        {
            'symbol': h.symbol,
            'name': h.name,
            'holding_days': h.holding_days or 0,
            'xirr': float(h.xirr or 0),
            'current_value': float(h.current_value or 0)
        }
        for h in holdings if h.xirr is not None
    ]

    # Calculate realized P&L by class (placeholder for now)
    realized_pl_by_class = {}
    for asset_class in class_allocation.keys():
        class_holdings = [h for h in holdings if h.asset_class == asset_class]
        realized_pl_by_class[asset_class] = sum(
            float(h.realized_pl or 0) for h in class_holdings
        )

    # Win rate calculation
    total_holdings = len(holdings)
    winning_holdings = len([h for h in holdings if (h.xirr or 0) > 0])
    win_rate = {
        'total': total_holdings,
        'winning': winning_holdings,
        'rate': winning_holdings / total_holdings if total_holdings > 0 else 0
    }

    # Cumulative strategy performance (placeholder)
    cumulative_strategy = {
        'months': [],
        'core': [],
        'satellite': []
    }

    return PortfolioMetrics(
        total_xirr=summary['total_xirr'],
        total_current_value=summary['total_current_value'],
        total_invested=summary['total_invested'],
        points_invested=summary['points_invested'],
        total_invested_with_points=summary['total_invested_with_points'],
        total_unrealized_pl=summary['total_unrealized_pl'],
        total_realized_pl=summary['total_realized_pl'],
        return_rate=summary['return_rate'],
        allocation_by_class=allocation_by_class,
        allocation_by_strategy=allocation_by_strategy,
        xirr_by_class=xirr_by_class,
        monthly_flow=dict(monthly_flow),
        top_performers=top_performers,
        realized_pl_by_class=realized_pl_by_class,
        cumulative_strategy=cumulative_strategy,
        win_rate=win_rate,
        scatter_data=scatter_data
    )


@router.get("/portfolios/{portfolio_id}/charts/allocation-by-class", response_model=ChartData)
def get_allocation_by_class(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Get asset allocation by class for pie chart"""
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()

    class_allocation = defaultdict(float)
    for h in holdings:
        class_allocation[h.asset_class or 'Other'] += float(h.current_value or 0)

    return ChartData(
        chart_type="pie",
        data={
            "labels": list(class_allocation.keys()),
            "values": list(class_allocation.values()),
            "colors": [get_asset_class_color(c) for c in class_allocation.keys()]
        }
    )


@router.get("/portfolios/{portfolio_id}/charts/allocation-by-strategy", response_model=ChartData)
def get_allocation_by_strategy(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Get asset allocation by strategy (Core/Satellite) for pie chart"""
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()

    strategy_allocation = defaultdict(float)
    for h in holdings:
        strategy_allocation[h.strategy or 'Other'] += float(h.current_value or 0)

    return ChartData(
        chart_type="pie",
        data={
            "labels": list(strategy_allocation.keys()),
            "values": list(strategy_allocation.values()),
            "colors": [get_strategy_color(s) for s in strategy_allocation.keys()]
        }
    )


@router.get("/portfolios/{portfolio_id}/charts/monthly-flow", response_model=ChartData)
def get_monthly_flow(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """Get monthly investment flow for stacked bar chart"""
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.portfolio_id == portfolio.id,
            Transaction.side == 'BUY'
        )
        .all()
    )

    monthly_flow = defaultdict(lambda: {'core': 0.0, 'satellite': 0.0})
    for tx in transactions:
        month_key = tx.transaction_date.strftime('%Y-%m')
        holding = next((h for h in holdings if h.symbol == tx.symbol), None)
        strategy = holding.strategy if holding else 'satellite'

        if strategy == 'Core':
            monthly_flow[month_key]['core'] += float(tx.amount_jpy)
        else:
            monthly_flow[month_key]['satellite'] += float(tx.amount_jpy)

    months = sorted(monthly_flow.keys())

    return ChartData(
        chart_type="bar",
        data={
            "labels": months,
            "datasets": [
                {
                    "label": "Core",
                    "data": [monthly_flow[m]['core'] for m in months],
                    "backgroundColor": get_strategy_color('Core')
                },
                {
                    "label": "Satellite",
                    "data": [monthly_flow[m]['satellite'] for m in months],
                    "backgroundColor": get_strategy_color('Satellite')
                }
            ]
        }
    )


@router.get("/portfolios/{portfolio_id}/charts/top-performers", response_model=ChartData)
def get_top_performers(
    portfolio: Portfolio = Depends(get_portfolio),
    limit: int = 5,
    db: Session = Depends(get_db_session)
):
    """Get top N performers by XIRR for bar chart"""
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio.id)
        .filter(Holding.xirr.isnot(None))
        .order_by(Holding.xirr.desc())
        .limit(limit)
        .all()
    )

    return ChartData(
        chart_type="bar",
        data={
            "labels": [h.name[:20] for h in holdings],  # Truncate long names
            "values": [float(h.xirr * 100) for h in holdings],  # Convert to percentage
            "symbols": [h.symbol for h in holdings]
        }
    )
