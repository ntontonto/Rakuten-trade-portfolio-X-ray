"""
XIRR (Extended Internal Rate of Return) Calculator

Ported from JavaScript implementation (index.html lines 414-447)
Uses Newton-Raphson iterative method to calculate annualized return rate
"""
from datetime import datetime
from typing import List, Optional
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
    value_tolerance: float = 1e-8,
    rate_tolerance: float = 1e-8,
    derivative_epsilon: float = 1e-12,
    debug: bool = False
) -> Optional[float]:
    """
    Calculate XIRR using Newton-Raphson with a safe bisection fallback.

    This implementation exactly matches the JavaScript version to ensure
    financial calculation accuracy.

    Args:
        cash_flows: List of CashFlow objects (must be at least 2)
        guess: Initial guess for the rate (default: 0.1 = 10%)
        max_iterations: Maximum number of iterations (default: 100)
        value_tolerance: Convergence tolerance for f(r)
        rate_tolerance: Convergence tolerance for rate delta
        derivative_epsilon: Threshold to detect a near-zero derivative
        debug: When True, prints iteration diagnostics

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
    # Validation: need at least two flows and mixed signs
    if len(cash_flows) < 2:
        if debug:
            print("XIRR abort: fewer than 2 cash flows")
        return None

    has_positive = any(cf.amount > 0 for cf in cash_flows)
    has_negative = any(cf.amount < 0 for cf in cash_flows)
    if not (has_positive and has_negative):
        if debug:
            print("XIRR abort: cash flows are not mixed sign")
        return None

    # Sort cash flows by date (ascending)
    sorted_cfs = sorted(cash_flows, key=lambda cf: cf.date)

    # Get first date as reference point (t0)
    t0 = sorted_cfs[0].date

    def normalize_time(date: datetime) -> float:
        """Convert date to years from t0 using total seconds (JS parity)."""
        seconds_diff = (date - t0).total_seconds()
        # JS: (d - t0) / (1000 * 60 * 60 * 24 * 365)
        return seconds_diff / (86400 * 365)

    def npv_and_derivative(rate: float):
        """Compute NPV and its derivative; guard invalid rates."""
        if rate <= -1.0:
            return None, None
        f_value = 0.0
        f_derivative = 0.0
        base = 1 + rate
        if base <= 0:
            return None, None
        for cf in sorted_cfs:
            t = normalize_time(cf.date)
            discount = math.pow(base, t)
            f_value += cf.amount / discount
            f_derivative -= (t * cf.amount) / (discount * base)
        return f_value, f_derivative

    # Clamp initial guess to safe bounds
    rate = max(guess, -0.9999)
    prev_rates = []

    for iteration in range(max_iterations):
        # Calculate function value (NPV) and derivative
        f_value, f_derivative = npv_and_derivative(rate)
        if f_value is None or f_derivative is None or not math.isfinite(f_value) or not math.isfinite(f_derivative):
            if debug:
                print(f"Newton abort at iter {iteration}: invalid f/df (rate={rate})")
            return _xirr_bisection(sorted_cfs, normalize_time, value_tolerance, rate_tolerance, debug)

        if debug:
            print(f"[Newton] iter={iteration} rate={rate} f={f_value} df={f_derivative}")

        # Check convergence on function value
        if abs(f_value) < value_tolerance:
            return rate

        # Check for zero derivative (prevent division by zero)
        if abs(f_derivative) < derivative_epsilon:
            if debug:
                print(f"Derivative too small at iter {iteration}, fallback to bisection")
            return _xirr_bisection(sorted_cfs, normalize_time, value_tolerance, rate_tolerance, debug)

        # Newton-Raphson update: x_new = x - f(x) / f'(x)
        new_rate = rate - (f_value / f_derivative)

        # Check convergence on rate change
        if abs(new_rate - rate) < rate_tolerance:
            return new_rate

        # Detect oscillation/divergence
        prev_rates.append(rate)
        if len(prev_rates) >= 3 and any(abs(new_rate - r) < rate_tolerance for r in prev_rates[-3:]):
            if debug:
                print("Detected oscillation, fallback to bisection")
            return _xirr_bisection(sorted_cfs, normalize_time, value_tolerance, rate_tolerance, debug)

        # Update rate with bounds
        rate = max(new_rate, -0.9999)
        if not math.isfinite(rate) or rate <= -1:
            if debug:
                print("Rate became invalid, fallback to bisection")
            return _xirr_bisection(sorted_cfs, normalize_time, value_tolerance, rate_tolerance, debug)

    # Newton failed to converge; try bracketing
    if debug:
        print("Newton did not converge within max iterations, fallback to bisection")
    return _xirr_bisection(sorted_cfs, normalize_time, value_tolerance, rate_tolerance, debug)


def calculate_portfolio_xirr(
    transactions: List[dict],
    current_value: float,
    snapshot_date: Optional[datetime] = None
) -> Optional[float]:
    """
    Calculate XIRR for an entire portfolio

    Args:
        transactions: List of transaction dicts with 'date', 'amount', 'side'
                      Amounts MUST already be signed (+/-); this function will not infer sign.
        current_value: Current market value of portfolio
        snapshot_date: Explicit snapshot date for the terminal cash flow

    Returns:
        Portfolio XIRR as decimal or None
    """
    if snapshot_date is None:
        # Terminal date must be explicit to avoid time drift vs JS
        return None

    # Build cash flows from transactions
    cash_flows = []

    for tx in transactions:
        amount = tx['amount']  # Amounts must already be signed (+/-)
        if amount == 0:
            continue
        side = tx.get('side')
        if side and side not in {'BUY', 'SELL'}:
            # Ambiguous side; refuse to proceed silently
            return None

        cash_flows.append(CashFlow(tx['date'], amount))

    # Add current value as final inflow
    if current_value > 0:
        cash_flows.append(CashFlow(snapshot_date, current_value))

    return calculate_xirr(cash_flows)


def format_xirr(xirr: Optional[float], decimal_places: int = 2) -> str:
    """Format XIRR as percentage string"""
    if xirr is None:
        return "N/A"
    return f"{xirr * 100:.{decimal_places}f}%"


def _xirr_bisection(
    cash_flows: List[CashFlow],
    normalize_time_fn,
    value_tolerance: float,
    rate_tolerance: float,
    debug: bool = False
) -> Optional[float]:
    """
    Robust fallback using bisection over a bounded interval to find a sign change.
    """
    def f(rate: float) -> Optional[float]:
        if rate <= -1.0:
            return None
        base = 1 + rate
        if base <= 0:
            return None
        total = 0.0
        for cf in cash_flows:
            t = normalize_time_fn(cf.date)
            try:
                total += cf.amount / math.pow(base, t)
            except (OverflowError, ValueError):
                return None
        return total

    low, high = -0.9999, 10.0
    samples = 200
    bracket = None
    prev_rate = low
    prev_value = f(prev_rate)

    for i in range(1, samples + 1):
        r = low + (high - low) * (i / samples)
        val = f(r)
        if val is None or prev_value is None:
            prev_rate, prev_value = r, val
            continue
        if val == 0:
            return r
        if prev_value * val < 0:
            bracket = (prev_rate, r)
            break
        prev_rate, prev_value = r, val

    if bracket is None:
        if debug:
            print("Bisection abort: no sign change found in [-0.9999, 10.0]")
        return None

    a, b = bracket
    fa, fb = f(a), f(b)
    if fa is None or fb is None:
        return None

    for _ in range(200):
        mid = (a + b) / 2
        fm = f(mid)
        if fm is None:
            return None
        if debug:
            print(f"[Bisection] a={a} b={b} mid={mid} f(mid)={fm}")
        if abs(fm) < value_tolerance or (b - a) / 2 < rate_tolerance:
            return mid
        if fa * fm < 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm

    return None
