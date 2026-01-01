"""
Ticker Mappings

Maps Rakuten Securities symbols to Yahoo Finance tickers for direct price lookup.
"""

# Direct Yahoo Finance ticker mappings
TICKER_TO_YAHOO = {
    # US Stocks - direct mapping
    "PLTR": "PLTR",
    "PLUG": "PLUG",
    "MU": "MU",
    "MGA": "MGA",
    "EGHT": "EGHT",
    "QUBT": "QUBT",
    "IAU": "IAU",
    "TSM": "TSM",
    "HYLN": "HYLN",
    "FCEL": "FCEL",
    "IDEX": "IDEX",
    "CBAT": "CBAT",
    "CIFR": "CIFR",

    # US ETFs
    "QQQ": "QQQ",
    "DIA": "DIA",
    "TQQQ": "TQQQ",
    "IYR": "IYR",
    "EPHE": "EPHE",
    "GLD": "GLD",  # SPDR Gold Shares (US listing)

    # Japanese ETFs - add .T suffix for Tokyo Stock Exchange
    "1326": "1326.T",  # SPDR Gold Share
    "1309": "1309.T",  # NEXT FUNDS ChinaAMC CSI300
    "1615": "1615.T",  # NEXT FUNDS Bank
    "1678": "1678.T",  # NEXT FUNDS India Equity
    "1542": "1542.T",  # Pure Silver Trust
    "1543": "1543.T",  # Pure Palladium Trust
    "1674": "1674.T",  # WisdomTree Platinum
    "1693": "1693.T",  # WisdomTree Copper
    "1628": "1628.T",  # iShares Transport & Logistics
    "2516": "2516.T",  # Tokyo Growth 250 ETF
    "4755": "4755.T",  # Rakuten Group
    "4824": "4824.T",  # MediaSeek
}


def get_yahoo_ticker(symbol: str) -> str:
    """
    Get Yahoo Finance ticker for a symbol

    Args:
        symbol: Rakuten Securities symbol

    Returns:
        Yahoo Finance ticker or None
    """
    return TICKER_TO_YAHOO.get(symbol)


def is_us_security(symbol: str) -> bool:
    """
    Check if symbol is a US security

    Args:
        symbol: Security symbol

    Returns:
        True if US security
    """
    # US tickers are typically letters only (no numbers)
    return symbol.isalpha() and symbol.isupper()


def is_japanese_security(symbol: str) -> bool:
    """
    Check if symbol is a Japanese security

    Args:
        symbol: Security symbol

    Returns:
        True if Japanese security
    """
    # Japanese tickers are typically numeric
    return symbol.isdigit()
