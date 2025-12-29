"""
Ticker and Proxy Index Mappings

Maps Rakuten Securities symbols to:
- Yahoo Finance tickers (for direct price lookup)
- Proxy indices (for mutual fund approximation)
"""

# Tier 1: Direct Yahoo Finance ticker mappings
TICKER_TO_YAHOO = {
    # US Stocks - direct mapping
    "PLTR": "PLTR",
    "PLUG": "PLUG",
    "MU": "MU",
    "MGA": "MGA",
    "EGHT": "8X8",
    "QUBT": "QUBT",

    # US ETFs
    "QQQ": "QQQ",
    "DIA": "DIA",
    "TQQQ": "TQQQ",
    "IYR": "IYR",
    "EPHE": "EPHE",

    # Japanese ETFs - add .T suffix for Tokyo Stock Exchange
    "1326": "1326.T",  # SPDR Gold Share
    "1542": "1542.T",  # Pure Silver Trust
    "1543": "1543.T",  # Pure Palladium Trust
    "1674": "1674.T",  # WisdomTree Platinum
    "1693": "1693.T",  # WisdomTree Copper
    "1628": "1628.T",  # iShares Transport & Logistics
    "2516": "2516.T",  # Tokyo Growth 250 ETF
    "4755": "4755.T",  # Rakuten Group
}

# Tier 2: Mutual Fund to Proxy Index Mappings
FUND_TO_PROXY = {
    # eMAXIS Slim Series (most popular Japanese index funds)
    "eMAXIS Slim 米国株式(S&P500)": {
        "proxy": "^GSPC",  # S&P 500 Index
        "name": "S&P 500",
        "currency": "USD",
        "correlation": 0.99,  # Expected correlation
        "expense_ratio": 0.0968,  # 0.0968% annual fee
    },

    "eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)": {
        "proxy": "ACWI",  # MSCI All Country World Index ETF
        "name": "MSCI ACWI",
        "currency": "USD",
        "correlation": 0.98,
        "expense_ratio": 0.0572,
    },

    "eMAXIS Slim 先進国リートインデックス(除く日本)": {
        "proxy": "VNQI",  # Vanguard Global ex-US Real Estate ETF
        "name": "Global REIT ex-Japan",
        "currency": "USD",
        "correlation": 0.95,
        "expense_ratio": 0.1540,
    },

    "eMAXIS Slim 先進国債券インデックス(除く日本)": {
        "proxy": "BNDX",  # Vanguard Total International Bond ETF
        "name": "Developed Market Bonds",
        "currency": "USD",
        "correlation": 0.92,
        "expense_ratio": 0.1540,
    },

    # Gold Funds
    "三菱UFJ 純金ファンド(ファインゴールド)": {
        "proxy": "GLD",  # SPDR Gold Trust
        "name": "Gold",
        "currency": "USD",
        "correlation": 0.99,
        "expense_ratio": 0.990,
    },

    # FANG+ Index
    "iFreeNEXT FANG+インデックス": {
        "proxy": "^NYFANG",  # NYSE FANG+ Index
        "name": "FANG+ Index",
        "currency": "USD",
        "correlation": 0.97,
        "expense_ratio": 0.7755,
    },

    # India Equity
    "たわらノーロード インド株式Nifty50": {
        "proxy": "INDA",  # iShares MSCI India ETF
        "name": "India Equity",
        "currency": "USD",
        "correlation": 0.95,
        "expense_ratio": 0.385,
    },

    # Semiconductor
    "ニッセイSOX指数インデックスファンド(米国半導体株)＜購入・換金手数料なし＞": {
        "proxy": "SOXX",  # iShares Semiconductor ETF
        "name": "Semiconductors",
        "currency": "USD",
        "correlation": 0.98,
        "expense_ratio": 0.1859,
    },

    # US REIT
    "NZAM・ベータ 米国REIT": {
        "proxy": "VNQ",  # Vanguard Real Estate ETF
        "name": "US REIT",
        "currency": "USD",
        "correlation": 0.97,
        "expense_ratio": 0.330,
    },

    # Japan REIT
    "野村Jリートファンド": {
        "proxy": "1343.T",  # NEXT FUNDS Tokyo Stock Exchange REIT Index ETF
        "name": "Japan REIT",
        "currency": "JPY",
        "correlation": 0.95,
        "expense_ratio": 1.045,
    },
}

# Alternative proxies (if primary fails)
PROXY_ALTERNATIVES = {
    "^GSPC": "SPY",  # S&P 500 ETF as alternative
    "ACWI": "VT",    # Vanguard Total World Stock ETF
    "^NYFANG": "FNGU",  # MicroSectors FANG+
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


def get_proxy_info(fund_name: str) -> dict:
    """
    Get proxy index information for a mutual fund

    Args:
        fund_name: Full fund name

    Returns:
        Proxy info dict or None
    """
    # Exact match
    if fund_name in FUND_TO_PROXY:
        return FUND_TO_PROXY[fund_name]

    # Partial match (for name variations)
    fund_name_normalized = fund_name.upper().replace(" ", "")
    for known_fund, proxy_info in FUND_TO_PROXY.items():
        known_normalized = known_fund.upper().replace(" ", "")
        if known_normalized in fund_name_normalized or fund_name_normalized in known_normalized:
            return proxy_info

    return None


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
