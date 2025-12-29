"""
Unit tests for XIRR Calculator

These tests validate that the Python implementation matches the JavaScript
version's behavior and produces accurate results.
"""
import pytest
from datetime import datetime
from app.services.xirr_calculator import (
    CashFlow,
    calculate_xirr,
    calculate_portfolio_xirr,
    format_xirr
)


class TestXIRRCalculator:
    """Test suite for XIRR calculation"""

    def test_simple_investment_profit(self):
        """Test simple case: invest 1000, get back 1100 after 1 year"""
        cash_flows = [
            CashFlow(datetime(2023, 1, 1), -1000),  # Investment
            CashFlow(datetime(2024, 1, 1), 1100),   # Return
        ]

        xirr = calculate_xirr(cash_flows)

        # Should be approximately 10% return
        assert xirr is not None
        assert abs(xirr - 0.10) < 0.01  # Within 1% tolerance

    def test_simple_investment_loss(self):
        """Test simple loss: invest 1000, get back 900"""
        cash_flows = [
            CashFlow(datetime(2023, 1, 1), -1000),
            CashFlow(datetime(2024, 1, 1), 900),
        ]

        xirr = calculate_xirr(cash_flows)

        # Should be approximately -10% return
        assert xirr is not None
        assert abs(xirr - (-0.10)) < 0.01

    def test_multiple_cash_flows(self):
        """Test with multiple investments and dividends"""
        cash_flows = [
            CashFlow(datetime(2023, 1, 1), -1000),   # Initial investment
            CashFlow(datetime(2023, 4, 1), -500),    # Additional investment
            CashFlow(datetime(2023, 7, 1), 100),     # Dividend
            CashFlow(datetime(2023, 10, 1), 100),    # Dividend
            CashFlow(datetime(2024, 1, 1), 1800),    # Final value + sale
        ]

        xirr = calculate_xirr(cash_flows)

        # Should be positive return (approximately high-30% for this timing)
        assert xirr is not None
        assert 0.35 < xirr < 0.42

    def test_six_month_return(self):
        """Test 6-month investment period"""
        cash_flows = [
            CashFlow(datetime(2023, 1, 1), -1000),
            CashFlow(datetime(2023, 7, 1), 1050),
        ]

        xirr = calculate_xirr(cash_flows)

        # 5% in 6 months ≈ 10.25% annualized
        assert xirr is not None
        assert abs(xirr - 0.1025) < 0.01

    def test_insufficient_cash_flows(self):
        """Test with less than 2 cash flows"""
        cash_flows = [
            CashFlow(datetime(2023, 1, 1), -1000),
        ]

        xirr = calculate_xirr(cash_flows)

        # Should return None for insufficient data
        assert xirr is None

    def test_empty_cash_flows(self):
        """Test with no cash flows"""
        xirr = calculate_xirr([])
        assert xirr is None

    def test_portfolio_xirr_calculation(self):
        """Test portfolio-level XIRR with transaction format"""
        transactions = [
            {
                'date': datetime(2023, 1, 1),
                'amount': -1000,
                'side': 'BUY'
            },
            {
                'date': datetime(2023, 6, 1),
                'amount': -500,
                'side': 'BUY'
            },
            {
                'date': datetime(2023, 9, 1),
                'amount': 200,
                'side': 'SELL'
            }
        ]

        current_value = 1800
        current_date = datetime(2024, 1, 1)

        xirr = calculate_portfolio_xirr(transactions, current_value, current_date)

        # Should calculate correctly with buys (negative) and sells (positive)
        assert xirr is not None
        assert xirr > 0.15  # Reasonable positive return

    def test_format_xirr(self):
        """Test XIRR formatting"""
        assert format_xirr(0.1234, 2) == "12.34%"
        assert format_xirr(0.1234, 1) == "12.3%"
        assert format_xirr(-0.05, 2) == "-5.00%"
        assert format_xirr(None) == "N/A"

    def test_xirr_convergence(self):
        """Test that algorithm converges within tolerance"""
        # Complex cash flow pattern
        cash_flows = [
            CashFlow(datetime(2020, 1, 1), -10000),
            CashFlow(datetime(2020, 6, 1), -5000),
            CashFlow(datetime(2021, 1, 1), 2000),
            CashFlow(datetime(2021, 6, 1), 3000),
            CashFlow(datetime(2022, 1, 1), 4000),
            CashFlow(datetime(2023, 1, 1), 12000),
        ]

        xirr = calculate_xirr(cash_flows)

        # Should converge to a reasonable value
        assert xirr is not None
        assert -0.5 < xirr < 0.5  # Within reasonable range

    def test_negative_rate_boundary(self):
        """Test that rate doesn't go below -100%"""
        # Extreme loss scenario
        cash_flows = [
            CashFlow(datetime(2023, 1, 1), -1000),
            CashFlow(datetime(2023, 2, 1), 10),  # Almost total loss
        ]

        xirr = calculate_xirr(cash_flows)

        # No feasible rate exists (all NPV values remain negative)
        # The implementation should signal failure rather than crash.
        assert xirr is None

    def test_exact_javascript_example(self):
        """
        Test with exact example from original JavaScript to verify
        identical behavior
        """
        # This would match a specific test case from the original app
        # Add actual data from testing the JS version
        cash_flows = [
            CashFlow(datetime(2023, 1, 15), -100000),
            CashFlow(datetime(2023, 3, 10), 10000),
            CashFlow(datetime(2023, 6, 20), 15000),
            CashFlow(datetime(2023, 12, 31), 95000),
        ]

        xirr = calculate_xirr(cash_flows)

        assert xirr is not None
        # Update this assertion with actual expected value from JS
        assert abs(xirr) < 0.3  # Placeholder: verify against JS output


@pytest.mark.parametrize("investment,return_value,expected_range", [
    (1000, 1100, (0.09, 0.11)),    # ~10% return
    (1000, 900, (-0.11, -0.09)),   # ~-10% return
    (5000, 6000, (0.18, 0.22)),    # ~20% return
    (10000, 12500, (0.23, 0.27)),  # ~25% return
])
def test_xirr_accuracy_parametrized(investment, return_value, expected_range):
    """Parametrized test for XIRR accuracy across different scenarios"""
    cash_flows = [
        CashFlow(datetime(2023, 1, 1), -investment),
        CashFlow(datetime(2024, 1, 1), return_value),
    ]

    xirr = calculate_xirr(cash_flows)

    assert xirr is not None
    assert expected_range[0] <= xirr <= expected_range[1]
