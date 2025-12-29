"""
Data Extractor for ML Features

Extracts time series and historical data from parsed CSV transactions
for use in ML forecasting, risk analysis, and portfolio optimization.
"""

from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import pandas as pd
from app.db.models.transaction import Transaction
from app.db.models.holding import Holding
from sqlalchemy.orm import Session


class DataExtractor:
    """Extracts ML-ready data from transaction history"""

    def __init__(self, db: Session):
        self.db = db

    def build_portfolio_timeseries(
        self,
        portfolio_id: str
    ) -> pd.DataFrame:
        """
        Build time series of total portfolio value from transactions.

        For each transaction date, calculates cumulative portfolio value.
        This is used for portfolio-level forecasting.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            DataFrame with columns: [date, total_value, invested, net_flow]
        """
        # Get all transactions sorted by date
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date)
            .all()
        )

        if not transactions:
            return pd.DataFrame(columns=['date', 'total_value', 'invested', 'net_flow'])

        # Build cumulative values
        records = []
        cumulative_invested = 0

        for tx in transactions:
            if tx.side == 'BUY':
                cumulative_invested += tx.amount_jpy
                net_flow = tx.amount_jpy
            elif tx.side == 'SELL':
                net_flow = -tx.amount_jpy
            else:
                net_flow = 0

            records.append({
                'date': tx.transaction_date,
                'invested': cumulative_invested,
                'net_flow': net_flow,
                'symbol': tx.symbol
            })

        df = pd.DataFrame(records)

        # Group by date (multiple transactions on same day)
        daily = df.groupby('date').agg({
            'invested': 'last',  # Take end-of-day invested amount
            'net_flow': 'sum'    # Sum all flows on that day
        }).reset_index()

        # Get current holdings to calculate total_value at each point
        # For historical points, we approximate using invested amount
        # (actual historical prices not available without external API)
        daily['total_value'] = daily['invested']  # Approximation

        return daily

    def build_monthly_cashflow(
        self,
        portfolio_id: str
    ) -> pd.DataFrame:
        """
        Build monthly cash flow pattern.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            DataFrame with columns: [month, invested, withdrawn, net_flow]
        """
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date)
            .all()
        )

        if not transactions:
            return pd.DataFrame(columns=['month', 'invested', 'withdrawn', 'net_flow'])

        records = []
        for tx in transactions:
            month = tx.transaction_date.strftime('%Y-%m')
            invested = tx.amount_jpy if tx.side == 'BUY' else 0
            withdrawn = tx.amount_jpy if tx.side == 'SELL' else 0

            records.append({
                'month': month,
                'invested': invested,
                'withdrawn': withdrawn
            })

        df = pd.DataFrame(records)

        monthly = df.groupby('month').agg({
            'invested': 'sum',
            'withdrawn': 'sum'
        }).reset_index()

        monthly['net_flow'] = monthly['invested'] - monthly['withdrawn']

        return monthly

    def extract_holding_transactions(
        self,
        portfolio_id: str,
        symbol: str
    ) -> pd.DataFrame:
        """
        Extract all transactions for a specific holding.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Asset symbol/ticker

        Returns:
            DataFrame with transaction history for this holding
        """
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.symbol == symbol
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        if not transactions:
            return pd.DataFrame()

        records = []
        for tx in transactions:
            # Calculate implied price
            price = tx.amount_jpy / tx.quantity if tx.quantity > 0 else 0

            records.append({
                'date': tx.transaction_date,
                'side': tx.side,
                'quantity': tx.quantity,
                'amount_jpy': tx.amount_jpy,
                'price': price
            })

        return pd.DataFrame(records)

    def calculate_volatility_proxy(
        self,
        portfolio_id: str,
        symbol: str
    ) -> float:
        """
        Calculate volatility proxy from transaction prices.

        Since we don't have daily prices, we use transaction price variance
        as a proxy for volatility.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Asset symbol

        Returns:
            Volatility score (0.0 to 1.0+)
        """
        df = self.extract_holding_transactions(portfolio_id, symbol)

        if len(df) < 2:
            return 0.0

        # Calculate coefficient of variation of prices
        prices = df['price']
        if prices.mean() == 0:
            return 0.0

        cv = prices.std() / prices.mean()

        # Normalize to 0-1 range (cap at 1.0)
        # CV > 0.5 is considered very volatile
        normalized = min(cv / 0.5, 1.0)

        return normalized

    def calculate_transaction_frequency(
        self,
        portfolio_id: str,
        symbol: str
    ) -> float:
        """
        Calculate transaction frequency score.

        Higher frequency = more active trading = potentially higher risk.

        Args:
            portfolio_id: Portfolio UUID
            symbol: Asset symbol

        Returns:
            Frequency score (transactions per month)
        """
        df = self.extract_holding_transactions(portfolio_id, symbol)

        if len(df) == 0:
            return 0.0

        # Calculate time span
        first_date = df['date'].min()
        last_date = df['date'].max()

        if first_date == last_date:
            return 1.0

        days = (last_date - first_date).days
        months = max(days / 30, 1)

        frequency = len(df) / months

        return frequency

    def detect_investment_pattern(
        self,
        portfolio_id: str
    ) -> Dict[str, any]:
        """
        Detect investment strategy pattern.

        Analyzes:
        - Dollar-Cost Averaging (regular monthly investments)
        - Lump Sum (large irregular investments)
        - Market Timing (irregular patterns)

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            Dict with pattern analysis
        """
        monthly_cf = self.build_monthly_cashflow(portfolio_id)

        if len(monthly_cf) == 0:
            return {
                'pattern': 'Unknown',
                'consistency': 0.0,
                'average_monthly': 0.0
            }

        # Calculate consistency (coefficient of variation)
        invested = monthly_cf['invested']
        avg_monthly = invested.mean()
        std_monthly = invested.std()

        if avg_monthly == 0:
            consistency = 0.0
        else:
            consistency = 1 - min(std_monthly / avg_monthly, 1.0)

        # Classify pattern
        if consistency > 0.8:
            pattern = 'Consistent DCA'
        elif consistency > 0.5:
            pattern = 'Regular with variations'
        else:
            pattern = 'Irregular (Lump Sum or Market Timing)'

        return {
            'pattern': pattern,
            'consistency': consistency,
            'average_monthly': avg_monthly,
            'months_active': len(monthly_cf)
        }

    def extract_risk_factors(
        self,
        portfolio_id: str,
        holding_id: str
    ) -> Dict[str, float]:
        """
        Extract all risk factors for a holding.

        Args:
            portfolio_id: Portfolio UUID
            holding_id: Holding UUID

        Returns:
            Dict with risk factor scores
        """
        holding = self.db.query(Holding).filter(Holding.id == holding_id).first()

        if not holding:
            return {}

        # Get all holdings for concentration calculation
        all_holdings = (
            self.db.query(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .all()
        )

        total_value = sum(h.current_value or 0 for h in all_holdings)

        # 1. Concentration Risk
        concentration = (holding.current_value or 0) / total_value if total_value > 0 else 0

        # 2. Volatility Proxy
        volatility = self.calculate_volatility_proxy(portfolio_id, holding.symbol)

        # 3. Transaction Frequency
        frequency = self.calculate_transaction_frequency(portfolio_id, holding.symbol)

        # 4. Asset Class Risk (base risk by class)
        asset_class_risk_map = {
            'Equity': 0.7,
            'REIT': 0.6,
            'Bond': 0.3,
            'Commodity': 0.8,
            'Cash': 0.1
        }
        asset_class_risk = asset_class_risk_map.get(holding.asset_class, 0.5)

        # 5. Holding Duration Score (longer = more stable)
        if holding.holding_days and holding.holding_days > 0:
            # Normalize: 1 year = low risk, < 30 days = high risk
            duration_risk = max(0, 1 - (holding.holding_days / 365))
        else:
            duration_risk = 1.0

        return {
            'concentration_risk': concentration,
            'volatility_proxy': volatility,
            'transaction_frequency': frequency,
            'asset_class_risk': asset_class_risk,
            'duration_risk': duration_risk
        }

    def calculate_composite_risk_score(
        self,
        risk_factors: Dict[str, float]
    ) -> Tuple[int, str]:
        """
        Calculate composite risk score from individual factors.

        Args:
            risk_factors: Dict of risk factor scores (0.0-1.0)

        Returns:
            Tuple of (risk_score 0-100, risk_level string)
        """
        # Weighted average
        weights = {
            'concentration_risk': 0.25,
            'volatility_proxy': 0.30,
            'transaction_frequency': 0.10,
            'asset_class_risk': 0.25,
            'duration_risk': 0.10
        }

        weighted_sum = 0
        total_weight = 0

        for factor, weight in weights.items():
            if factor in risk_factors:
                weighted_sum += risk_factors[factor] * weight
                total_weight += weight

        if total_weight == 0:
            return 50, 'Unknown'

        # Convert to 0-100 scale
        risk_score = int((weighted_sum / total_weight) * 100)

        # Classify risk level
        if risk_score < 30:
            risk_level = 'Low'
        elif risk_score < 60:
            risk_level = 'Medium'
        elif risk_score < 80:
            risk_level = 'Medium-High'
        else:
            risk_level = 'High'

        return risk_score, risk_level
