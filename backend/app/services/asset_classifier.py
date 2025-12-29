"""
Asset Classification Service

Classifies securities into asset classes and investment strategies

Ported from JavaScript (index.html lines 451-457, 745-755)
"""
import re
from typing import Optional


def classify_asset(name: str, ticker: Optional[str] = None) -> str:
    """
    Classify asset into one of: Equity, Bond, REIT, Commodity

    Args:
        name: Asset name
        ticker: Optional ticker symbol

    Returns:
        Asset class string

    Examples:
        >>> classify_asset("SPDR Gold Trust", "GLD")
        'Commodity'
        >>> classify_asset("eMAXIS Slim 先進国リートインデックス")
        'REIT'
        >>> classify_asset("Vanguard Total Bond Market ETF", "BND")
        'Bond'
        >>> classify_asset("Apple Inc", "AAPL")
        'Equity'
    """
    # Combine name and ticker for matching
    search_text = (name or '').upper()
    if ticker:
        search_text += ' ' + ticker.upper()

    # Commodity patterns
    commodity_patterns = [
        r'GOLD', r'GLD', r'IAU', r'SLV', r'金', r'プラチナ', r'コモディティ',
        r'COMMODITY', r'貴金属', r'シルバー'
    ]
    if any(re.search(pattern, search_text) for pattern in commodity_patterns):
        return 'Commodity'

    # REIT patterns
    reit_patterns = [
        r'REIT', r'リート', r'不動産', r'REAL ESTATE', r'不動産投資'
    ]
    if any(re.search(pattern, search_text) for pattern in reit_patterns):
        return 'REIT'

    # Bond patterns
    bond_patterns = [
        r'BOND', r'債券', r'AGG', r'BND', r'TLT', r'国債', r'社債',
        r'TREASURY', r'FIXED INCOME'
    ]
    if any(re.search(pattern, search_text) for pattern in bond_patterns):
        return 'Bond'

    # Default to Equity
    return 'Equity'


def classify_strategy(
    market: str,
    holding_days: int,
    qty: float,
    is_held: Optional[bool] = None
) -> str:
    """
    Classify investment strategy: Core (long-term) or Satellite (short-term)

    Rules (from JS lines 745-755):
    - Investment trusts (INVST) are always Core
    - Assets held for >= 365 days are Core
    - Currently held assets (qty > 0) are Core
    - Others are Satellite

    Args:
        market: Market type ('US', 'JP', 'INVST')
        holding_days: Number of days held
        qty: Current quantity held
        is_held: Optional override for held status

    Returns:
        'Core' or 'Satellite'

    Examples:
        >>> classify_strategy('INVST', 100, 1000)
        'Core'
        >>> classify_strategy('US', 400, 50)
        'Core'
        >>> classify_strategy('JP', 30, 0)
        'Satellite'
    """
    # Investment trusts are always Core
    if market == 'INVST':
        return 'Core'

    # Determine if currently held
    if is_held is None:
        is_held = qty > 0.0001

    # Long-term holdings or currently held positions are Core
    if is_held or holding_days >= 365:
        return 'Core'

    # Short-term, sold positions are Satellite
    return 'Satellite'


def get_asset_class_color(asset_class: str) -> str:
    """
    Get color code for asset class visualization

    Args:
        asset_class: Asset class name

    Returns:
        Hex color code
    """
    colors = {
        'Equity': '#3b82f6',     # Blue
        'Bond': '#10b981',       # Emerald
        'REIT': '#f59e0b',       # Amber
        'Commodity': '#eab308'   # Yellow
    }
    return colors.get(asset_class, '#64748b')  # Default: Slate


def get_strategy_color(strategy: str) -> str:
    """
    Get color code for strategy visualization

    Args:
        strategy: Strategy name

    Returns:
        Hex color code
    """
    colors = {
        'Core': '#6366f1',       # Indigo
        'Satellite': '#f43f5e'   # Rose
    }
    return colors.get(strategy, '#64748b')  # Default: Slate
