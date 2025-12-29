"""
XIRR (Extended Internal Rate of Return) Calculator

Ported from JavaScript implementation (index.html lines 414-447)
Uses Newton-Raphson iterative method to calculate annualized return rate
"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import math


class CashFlow:
    """Represents a single cash flow event"""
    def __init__(self, date: datetime, amount: float):
        self.date = date
        self.amount = float(amount)

    def __repr__(self):
        return f"CashFlow(date={self.date.date()}, amount={self.amount})"


def calculate_xirr(
    cash_flows: List[CashFlow],
    guess: float = 0.1,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Optional[float]:
    """
    Calculate XIRR using Newton-Raphson method

    This implementation exactly matches the JavaScript version to ensure
    financial calculation accuracy.

    Args:
        cash_flows: List of CashFlow objects (must be at least 2)
        guess: Initial guess for the rate (default: 0.1 = 10%)
        max_iterations: Maximum number of iterations (default: 100)
        tolerance: Convergence tolerance (default: 1e-6)

    Returns:
        XIRR as a decimal (e.g., 0.1234 = 12.34%) or None if calculation fails

    Example:
        >>> cfs = [
        ...     CashFlow(datetime(2023, 1, 1), -1000),  # Investment
        ...     CashFlow(datetime(2023, 6, 1), 100),    # Dividend
        ...     CashFlow(datetime(2024, 1, 1), 1200),   # Final value
        ... ]
        >>> xirr = calculate_xirr(cfs)
        >>> print(f"{xirr * 100:.2f}%")  # e.g., "15.23%"
    """
    # Validation
    if len(cash_flows) < 2:
        return 0.0

    # Sort cash flows by date (ascending)
    sorted_cfs = sorted(cash_flows, key=lambda cf: cf.date)

    # Get first date as reference point (t0)
    t0 = sorted_cfs[0].date

    def normalize_time(date: datetime) -> float:
        """Convert date to years from t0 (matches JS logic)"""
        days_diff = (date - t0).days
        # Use 365 days per year (same as JS: 1000 * 60 * 60 * 24 * 365)
        return days_diff / 365.0

    # Newton-Raphson iteration
    rate = guess

    for iteration in range(max_iterations):
        # Calculate function value (NPV) and derivative
        f_value = 0.0
        f_derivative = 0.0

        for cf in sorted_cfs:
            t = normalize_time(cf.date)
            discount_factor = math.pow(1 + rate, t)

            # NPV contribution
            f_value += cf.amount / discount_factor

            # Derivative contribution
            f_derivative -= (t * cf.amount) / (discount_factor * (1 + rate))

        # Check convergence on function value
        if abs(f_value) < tolerance:
            return rate

        # Check for zero derivative (prevent division by zero)
        if abs(f_derivative) < tolerance:
            return None

        # Newton-Raphson update: x_new = x - f(x) / f'(x)
        new_rate = rate - (f_value / f_derivative)

        # Check convergence on rate change
        if abs(new_rate - rate) < tolerance:
            return new_rate

        # Update rate
        rate = new_rate

        # Prevent rate from going below -100% (matches JS logic)
        if rate <= -1:
            rate = -0.99

    # Failed to converge
    return None


def calculate_portfolio_xirr(
    transactions: List[dict],
    current_value: float,
    current_date: Optional[datetime] = None
) -> Optional[float]:
    """
    Calculate XIRR for an entire portfolio

    Args:
        transactions: List of transaction dicts with 'date', 'amount', 'side'
        current_value: Current market value of portfolio
        current_date: Date to use as current (defaults to today)

    Returns:
        Portfolio XIRR as decimal or None
    """
    if current_date is None:
        current_date = datetime.now()

    # Build cash flows from transactions
    cash_flows = []

    for tx in transactions:
        amount = tx['amount']
        if tx['side'] == 'BUY':
            amount = -abs(amount)  # Outflow
        else:  # SELL
            amount = abs(amount)   # Inflow

        cash_flows.append(CashFlow(tx['date'], amount))

    # Add current value as final inflow
    if current_value > 0:
        cash_flows.append(CashFlow(current_date, current_value))

    return calculate_xirr(cash_flows)


def format_xirr(xirr: Optional[float], decimal_places: int = 2) -> str:
    """Format XIRR as percentage string"""
    if xirr is None:
        return "N/A"
    return f"{xirr * 100:.{decimal_places}f}%"
