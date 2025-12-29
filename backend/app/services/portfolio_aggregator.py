"""
Portfolio Aggregator Service

Aggregates transactions into holdings with calculated metrics

Ported from JavaScript (index.html lines 699-874)
"""
from datetime import datetime, date
from typing import List, Dict, Optional
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models import Portfolio, Transaction, Holding
from app.services.xirr_calculator import CashFlow, calculate_xirr
from app.services.asset_classifier import classify_asset, classify_strategy


class PortfolioAggregator:
    """Aggregates transactions into current holdings with performance metrics"""

    def __init__(self, db: Session):
        self.db = db

    def _normalize_portfolio_id(self, portfolio_id) -> UUID:
        """Accept UUID or string and return UUID instance for queries."""
        return portfolio_id if isinstance(portfolio_id, UUID) else UUID(str(portfolio_id))

    def process_portfolio(self, portfolio_id: str) -> List[Holding]:
        """
        Process all transactions for a portfolio and create/update holdings

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            List of updated Holding objects
        """
        pid = self._normalize_portfolio_id(portfolio_id)

        # Fetch all transactions for this portfolio
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == pid)
            .order_by(Transaction.transaction_date)
            .all()
        )

        if not transactions:
            return []

        # Group transactions by symbol
        holdings_map: Dict[str, Dict] = {}

        for tx in transactions:
            symbol = tx.symbol
            if symbol not in holdings_map:
                holdings_map[symbol] = {
                    'symbol': symbol,
                    'name': tx.name,
                    'market': tx.market,
                    'asset_class': tx.asset_class or classify_asset(tx.name, tx.symbol),
                    'qty': Decimal('0'),
                    'invested': Decimal('0'),
                    'realized_pl': Decimal('0'),
                    'first_date': tx.transaction_date,
                    'last_date': tx.transaction_date,
                    'last_price': Decimal('0'),
                    'transactions': []
                }

            h = holdings_map[symbol]
            h['transactions'].append(tx)

            # Update dates
            if tx.transaction_date > h['last_date']:
                h['last_date'] = tx.transaction_date

            # Calculate unit price for this transaction
            unit_price = Decimal('0')
            if tx.quantity > 0:
                unit_price = tx.amount_jpy / tx.quantity

            if tx.side == 'BUY':
                h['qty'] += tx.quantity
                h['invested'] += tx.amount_jpy
                h['last_price'] = unit_price  # Track last purchase price

            elif tx.side == 'SELL':
                # Calculate realized P&L using FIFO average cost
                avg_cost = h['invested'] / (h['qty'] + tx.quantity) if (h['qty'] + tx.quantity) > 0 else Decimal('0')
                cost_basis = avg_cost * tx.quantity
                h['realized_pl'] += (tx.amount_jpy - cost_basis)

                # Update position
                h['qty'] -= tx.quantity
                h['invested'] -= cost_basis

        # Calculate holdings and metrics
        today = date.today()
        holdings_list = []

        for symbol, data in holdings_map.items():
            # Only create holdings for positions with qty > 0.0001
            if data['qty'] <= Decimal('0.0001'):
                continue

            holding_days = (today - data['first_date']).days

            # Classify strategy
            strategy = classify_strategy(
                market=data['market'],
                holding_days=holding_days,
                qty=float(data['qty']),
                is_held=True
            )

            # Calculate average cost
            avg_cost = data['invested'] / data['qty'] if data['qty'] > 0 else Decimal('0')

            # Check if holding already exists
            existing = (
                self.db.query(Holding)
                .filter(
                    Holding.portfolio_id == pid,
                    Holding.symbol == symbol
                )
                .first()
            )

            if existing:
                # Update existing holding
                holding = existing
                holding.quantity = data['qty']
                holding.average_cost = avg_cost
                holding.invested_amount = data['invested']
                holding.realized_pl = data['realized_pl']
                holding.asset_class = data['asset_class']
                holding.strategy = strategy
                holding.first_purchase_date = data['first_date']
                holding.last_transaction_date = data['last_date']
                holding.holding_days = holding_days
            else:
                # Create new holding
                holding = Holding(
                    portfolio_id=pid,
                    symbol=symbol,
                    name=data['name'],
                    quantity=data['qty'],
                    average_cost=avg_cost,
                    current_price=data['last_price'],  # Default to last purchase price
                    invested_amount=data['invested'],
                    realized_pl=data['realized_pl'],
                    asset_class=data['asset_class'],
                    strategy=strategy,
                    market=data['market'],
                    first_purchase_date=data['first_date'],
                    last_transaction_date=data['last_date'],
                    holding_days=holding_days,
                    is_price_auto_updated=False
                )
                self.db.add(holding)

            holdings_list.append(holding)

        # Commit changes
        self.db.commit()

        # Calculate performance metrics for each holding
        self._calculate_performance_metrics(holdings_list)

        return holdings_list

    def _calculate_performance_metrics(self, holdings: List[Holding]):
        """
        Calculate XIRR and other performance metrics for holdings

        Args:
            holdings: List of Holding objects
        """
        for holding in holdings:
            # Build cash flows for XIRR calculation
            transactions = (
                self.db.query(Transaction)
                .filter(
                    Transaction.portfolio_id == holding.portfolio_id,
                    Transaction.symbol == holding.symbol
                )
                .order_by(Transaction.transaction_date)
                .all()
            )

            cash_flows = []
            for tx in transactions:
                if tx.side == 'BUY':
                    cash_flows.append(
                        CashFlow(
                            date=datetime.combine(tx.transaction_date, datetime.min.time()),
                            amount=-float(tx.amount_jpy)  # Outflow
                        )
                    )
                elif tx.side == 'SELL':
                    cash_flows.append(
                        CashFlow(
                            date=datetime.combine(tx.transaction_date, datetime.min.time()),
                            amount=float(tx.amount_jpy)  # Inflow
                        )
                    )

            # Add current value as final inflow
            if holding.current_price and holding.quantity > 0:
                holding.current_value = holding.current_price * holding.quantity
                holding.unrealized_pl = holding.current_value - holding.invested_amount

                cash_flows.append(
                    CashFlow(
                        date=datetime.now(),
                        amount=float(holding.current_value)
                    )
                )

                # Calculate XIRR
                xirr = calculate_xirr(cash_flows)
                holding.xirr = Decimal(str(xirr)) if xirr is not None else None
            else:
                holding.current_value = Decimal('0')
                holding.unrealized_pl = Decimal('0')
                holding.xirr = None

            holding.last_calculated_at = datetime.now()

        # Commit updates
        self.db.commit()

    def update_holding_price(
        self,
        portfolio_id: str,
        symbol: str,
        new_price: Decimal,
        auto_updated: bool = False
    ) -> Optional[Holding]:
        """
        Update current price for a holding and recalculate metrics

        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            new_price: New current price
            auto_updated: Whether price was auto-updated from balance CSV

        Returns:
            Updated Holding or None if not found
        """
        pid = self._normalize_portfolio_id(portfolio_id)

        holding = (
            self.db.query(Holding)
            .filter(
                Holding.portfolio_id == pid,
                Holding.symbol == symbol
            )
            .first()
        )

        if not holding:
            return None

        holding.current_price = new_price
        holding.is_price_auto_updated = auto_updated

        # Recalculate metrics
        self._calculate_performance_metrics([holding])

        return holding

    def get_portfolio_summary(self, portfolio_id: str) -> Dict:
        """
        Calculate portfolio-level summary metrics

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            Dict with summary metrics
        """
        pid = self._normalize_portfolio_id(portfolio_id)

        holdings = (
            self.db.query(Holding)
            .filter(Holding.portfolio_id == pid)
            .all()
        )

        total_invested = sum(h.invested_amount or Decimal('0') for h in holdings)
        total_current_value = sum(h.current_value or Decimal('0') for h in holdings)
        total_unrealized_pl = sum(h.unrealized_pl or Decimal('0') for h in holdings)
        total_realized_pl = sum(h.realized_pl or Decimal('0') for h in holdings)

        # Calculate portfolio-level XIRR
        all_transactions = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == pid)
            .order_by(Transaction.transaction_date)
            .all()
        )

        cash_flows = []
        for tx in all_transactions:
            if tx.side == 'BUY':
                cash_flows.append(
                    CashFlow(
                        date=datetime.combine(tx.transaction_date, datetime.min.time()),
                        amount=-float(tx.amount_jpy)
                    )
                )
            elif tx.side == 'SELL':
                cash_flows.append(
                    CashFlow(
                        date=datetime.combine(tx.transaction_date, datetime.min.time()),
                        amount=float(tx.amount_jpy)
                    )
                )

        # Add current total value
        if total_current_value > 0:
            cash_flows.append(
                CashFlow(date=datetime.now(), amount=float(total_current_value))
            )

        portfolio_xirr = calculate_xirr(cash_flows) or 0.0

        # Calculate simple return rate
        return_rate = 0.0
        if total_invested > 0:
            return_rate = float((total_current_value - total_invested) / total_invested)

        return {
            'portfolio_id': str(pid),
            'total_xirr': portfolio_xirr,
            'total_current_value': float(total_current_value),
            'total_invested': float(total_invested),
            'total_unrealized_pl': float(total_unrealized_pl),
            'total_realized_pl': float(total_realized_pl),
            'return_rate': return_rate,
            'holdings_count': len(holdings),
            'last_calculated_at': datetime.now()
        }
