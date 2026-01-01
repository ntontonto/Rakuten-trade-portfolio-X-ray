"""Analysis and Charts Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, date, timedelta
from collections import defaultdict

from app.api.deps import get_db_session, get_portfolio
from app.db.models import Portfolio, Holding, Transaction
from app.schemas.analysis import (
    XIRRRequest,
    XIRRResponse,
    PortfolioMetrics,
    AllocationData,
    ChartData,
    PriceHistoryResponse,
    PortfolioTimelineResponse,
    PortfolioTimelinePoint
)
from app.services.xirr_calculator import CashFlow, calculate_xirr, format_xirr
from app.services.asset_classifier import get_asset_class_color, get_strategy_color
from app.services.portfolio_aggregator import PortfolioAggregator
from app.services.price_fetcher import HistoricalPriceService

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


def _build_quantity_map(transactions, start_date: date, end_date: date):
    """Build daily cumulative quantity map from transactions."""
    by_date = defaultdict(float)
    for tx in transactions:
        delta = float(tx.quantity)
        if tx.side == 'SELL':
            delta = -delta
        elif tx.side != 'BUY':
            delta = 0.0
        by_date[tx.transaction_date] += delta

    qty_map = {}
    current = 0.0
    current_date = start_date
    while current_date <= end_date:
        current += by_date.get(current_date, 0.0)
        qty_map[current_date] = current
        current_date += timedelta(days=1)

    return qty_map


def _build_price_map(
    price_service: HistoricalPriceService,
    holding: Holding,
    start_date: date,
    end_date: date,
    fx_map: Dict[date, float],
    transactions: List[Transaction]
):
    """Fetch price history once and convert to JPY map."""
    prices, source = price_service.get_price_history(
        symbol=holding.symbol,
        name=holding.name,
        start_date=start_date,
        end_date=end_date,
        portfolio_id=str(holding.portfolio_id)
    )
    price_map: Dict[date, float] = {}
    if prices is None or prices.empty:
        # Fallback: pure interpolation on transaction prices
        interp_df = price_service.interpolator.interpolate(transactions, start_date, end_date)
        if interp_df is None or interp_df.empty:
            return price_map, source
        prices = interp_df
        source = source or 'interpolated'

    # For US holdings, forward-fill missing FX rates to avoid gaps
    if holding.market == 'US' and fx_map:
        filled_fx_map = {}
        last_fx = None
        current_date = start_date
        while current_date <= end_date:
            if current_date in fx_map:
                last_fx = fx_map[current_date]
            if last_fx is not None:
                filled_fx_map[current_date] = last_fx
            current_date += timedelta(days=1)
        fx_map = filled_fx_map

    for idx, row in prices.iterrows():
        d = idx.date() if hasattr(idx, "date") else idx
        raw = float(row['price'])
        if holding.market == 'US':
            fx = fx_map.get(d)
            if fx:
                price_map[d] = raw * fx
        else:
            price_map[d] = raw
    return price_map, source


@router.get(
    "/portfolios/{portfolio_id}/holdings/{symbol}/history",
    response_model=PriceHistoryResponse
)
def get_holding_price_history(
    portfolio_id: UUID,
    symbol: str,
    start_date: date | None = None,
    end_date: date | None = None,
    frequency: str = "daily",  # 'daily', 'weekly', 'monthly'
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Get price/value history for a holding (JPY-converted when possible).

    Args:
        portfolio_id: Portfolio UUID
        symbol: Holding symbol
        start_date: Optional start date. If not provided, uses first transaction date.
        end_date: Optional end date. If not provided, uses today.
        frequency: Data frequency - 'daily' (default), 'weekly', or 'monthly'

    Returns:
        Price history with dates covering the actual transaction period
    """
    try:
        holding = (
            db.query(Holding)
            .filter(Holding.portfolio_id == portfolio.id, Holding.symbol == symbol)
            .first()
        )
        if not holding:
            raise HTTPException(
                status_code=404,
                detail=f"Holding {symbol} not found in portfolio {portfolio_id}"
            )

        transactions = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.id, Transaction.symbol == symbol)
            .order_by(Transaction.transaction_date)
            .all()
        )

        # Always default to today for end_date
        if not end_date:
            end_date = date.today()

        # Automatically use transaction period if start_date not provided
        if not start_date:
            # Prefer first_purchase_date from holding (pre-computed, faster)
            if holding.first_purchase_date:
                start_date = holding.first_purchase_date
            # Fallback to first transaction
            elif transactions:
                start_date = transactions[0].transaction_date
            # Last resort: use end_date (will result in single day)
            else:
                start_date = end_date

        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be on or before end_date"
            )

        price_service = HistoricalPriceService(db)
        prices, source = price_service.get_price_history(
            symbol=symbol,
            name=holding.name,
            start_date=start_date,
            end_date=end_date,
            portfolio_id=str(portfolio.id)
        )

        if prices is None or prices.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No price history available for {symbol}"
            )

        # Resample data based on frequency parameter
        if frequency == "weekly":
            # Resample to weekly (Friday close, or last available day of week)
            prices = prices.resample('W-FRI').last().dropna()
        elif frequency == "monthly":
            # Resample to monthly (month-end close)
            prices = prices.resample('M').last().dropna()

        # FX conversion for USD assets
        fx_rates = None
        fx_map = {}
        if holding.market == 'US':
            fx_rates = price_service.get_exchange_rate_history(start_date, end_date)
            if fx_rates is not None:
                # Build initial FX map from DataFrame
                raw_fx_map = {}
                for idx, row in fx_rates.iterrows():
                    d = idx.date() if hasattr(idx, "date") else idx
                    raw_fx_map[d] = float(row["rate"])

                # Forward-fill missing FX rates to avoid gaps
                last_fx = None
                current_date = start_date
                while current_date <= end_date:
                    if current_date in raw_fx_map:
                        last_fx = raw_fx_map[current_date]
                    if last_fx is not None:
                        fx_map[current_date] = last_fx
                    current_date += timedelta(days=1)

        qty_map = _build_quantity_map(transactions, start_date, end_date)
        currency = 'USD' if holding.market == 'US' else 'JPY'

        points = []
        for idx, row in prices.iterrows():
            point_date = idx.date() if hasattr(idx, "date") else idx
            price_raw = float(row['price'])
            fx_rate = fx_map.get(point_date) if holding.market == 'US' else None
            price_jpy = price_raw * fx_rate if fx_rate else (price_raw if holding.market != 'US' else None)
            quantity = qty_map.get(point_date)
            value_jpy = price_jpy * quantity if price_jpy is not None and quantity is not None else None

            points.append({
                "date": point_date,
                "price_raw": price_raw,
                "fx_rate": fx_rate,
                "price_jpy": price_jpy,
                "quantity": quantity,
                "value_jpy": value_jpy
            })

        return PriceHistoryResponse(
            source=source,
            currency=currency,
            points=points
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch holding history for {symbol}: {str(e)}"
        )


@router.get(
    "/portfolios/{portfolio_id}/timeline",
    response_model=PortfolioTimelineResponse
)
def get_portfolio_timeline(
    portfolio_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Daily cumulative invested value vs total evaluation value (JPY).
    """
    try:
        holdings: List[Holding] = (
            db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        )
        transactions: List[Transaction] = (
            db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.id)
            .order_by(Transaction.transaction_date)
            .all()
        )

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = transactions[0].transaction_date if transactions else end_date
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

        price_service = HistoricalPriceService(db)

        # FX map (USD -> JPY) fetched once
        fx_map: Dict[date, float] = {}
        if any(h.market == 'US' for h in holdings):
            fx_rates = price_service.get_exchange_rate_history(start_date, end_date)
            if fx_rates is not None:
                fx_map = {
                    (idx.date() if hasattr(idx, "date") else idx): float(row['rate'])
                    for idx, row in fx_rates.iterrows()
                }

        # Precompute per-holding quantity maps and price maps
        qty_maps: Dict[str, Dict[date, float]] = {}
        price_maps: Dict[str, Dict[date, float]] = {}
        for h in holdings:
            h_txs = [tx for tx in transactions if tx.symbol == h.symbol]
            qty_maps[h.symbol] = _build_quantity_map(h_txs, start_date, end_date)
            price_map, _ = _build_price_map(price_service, h, start_date, end_date, fx_map, h_txs)
            price_maps[h.symbol] = price_map

        # Invested cumulative per day
        invested_by_date = defaultdict(float)
        for tx in transactions:
            if tx.side == 'BUY':
                invested_by_date[tx.transaction_date] += float(tx.amount_jpy)

        points: List[PortfolioTimelinePoint] = []
        running_invested = 0.0
        current_date = start_date
        while current_date <= end_date:
            running_invested += invested_by_date.get(current_date, 0.0)

            total_value = 0.0
            for h in holdings:
                qty = qty_maps.get(h.symbol, {}).get(current_date, 0.0)
                if qty <= 0:
                    continue
                price_jpy = price_maps.get(h.symbol, {}).get(current_date)
                if price_jpy is None:
                    continue
                total_value += qty * price_jpy

            points.append(
                PortfolioTimelinePoint(
                    date=current_date,
                    invested_cumulative_jpy=running_invested,
                    total_value_jpy=total_value
                )
            )
            current_date += timedelta(days=1)

        return PortfolioTimelineResponse(points=points)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate portfolio timeline: {str(e)}"
        )
