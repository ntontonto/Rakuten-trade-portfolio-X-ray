"""
Alias resolver for symbols and fund names.

Purpose:
- Treat known fund codes/names as aliases to a canonical fetch symbol.
"""

from __future__ import annotations
from typing import Tuple


ALIAS_MAP = {
    # eMAXIS Slim funds
    "0331418A": "0331418A",  # 全世界株式(オルカン)
    "03311187": "03311187",  # 米国株式(S&P500)
    "0331A172": "0331A172",  # 先進国債券インデックス(除く日本)
    "0331219A": "0331219A",  # 先進国リートインデックス(除く日本)

    # Other mutual funds
    "25314203": "25314203",  # NZAM・ベータ 米国REIT
    "4731624C": "4731624C",  # たわらノーロード インド株式Nifty50
    "29314233": "29314233",  # ニッセイSOX指数インデックスファンド
    "03311112": "03311112",  # 三菱UFJ 純金ファンド(ファインゴールド)
    "04311181": "04311181",  # iFreeNEXT FANG+インデックス
    "01314133": "01314133",  # 野村Jリートファンド

    # Japanese ETFs (numeric tickers)
    "1326": "1326",  # SPDRゴールド・シェア
    "1542": "1542",  # 純銀上場信託
    "1674": "1674",  # WT白金上場投信
    "1693": "1693",  # WT銅上場投信
    "2516": "2516",  # 東証グロース250ETF
    "4755": "4755",  # 楽天グループ
}

NAME_ALIASES = {
    # eMAXIS Slim 全世界株式 (All Country / オルカン)
    "eMAXIS Slim 全世界株式(オール・カントリー)": "0331418A",
    "eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)": "0331418A",
    "オルカン": "0331418A",

    # eMAXIS Slim 米国株式 (S&P500)
    "eMAXIS Slim 米国株式(S&P500)": "03311187",
    "米国株式(S&P500)": "03311187",

    # eMAXIS Slim 先進国債券インデックス(除く日本)
    "eMAXIS Slim 先進国債券インデックス(除く日本)": "0331A172",
    "先進国債券インデックス(除く日本)": "0331A172",

    # eMAXIS Slim 先進国リートインデックス(除く日本)
    "eMAXIS Slim 先進国リートインデックス(除く日本)": "0331219A",
    "先進国リートインデックス(除く日本)": "0331219A",

    # NZAM・ベータ 米国REIT
    "NZAM・ベータ 米国REIT": "25314203",
    "NZAMベータ 米国REIT": "25314203",

    # たわらノーロード インド株式Nifty50
    "たわらノーロード インド株式Nifty50": "4731624C",
    "インド株式Nifty50": "4731624C",

    # ニッセイSOX指数インデックスファンド
    "ニッセイSOX指数インデックスファンド": "29314233",
    "SOX指数インデックスファンド": "29314233",

    # 三菱UFJ 純金ファンド(ファインゴールド)
    "三菱UFJ 純金ファンド(ファインゴールド)": "03311112",
    "純金ファンド(ファインゴールド)": "03311112",
    "ファインゴールド": "03311112",

    # iFreeNEXT FANG+インデックス
    "iFreeNEXT FANG+インデックス": "04311181",
    "FANG+インデックス": "04311181",

    # 野村Jリートファンド
    "野村Jリートファンド": "01314133",
    "Jリートファンド": "01314133",

    # Japanese ETFs
    "ＳＰＤＲゴールド・シェア（東証上場）": "1326",
    "ＳＰＤＲゴールド・シェア": "1326",
    "SPDRゴールド・シェア": "1326",
    "純銀上場信託（現物国内保管型）": "1542",
    "純銀上場信託": "1542",
    "ＷＴ白金上場投信（WisdomTree 白金）": "1674",
    "ＷＴ白金上場投信": "1674",
    "WisdomTree 白金": "1674",
    "ＷＴ銅上場投信（WisdomTree 銅）": "1693",
    "ＷＴ銅上場投信": "1693",
    "WisdomTree 銅": "1693",
    "東証グロース２５０ＥＴＦ": "2516",
    "東証グロース250ETF": "2516",
    "楽天グループ": "4755",
}


def resolve_alias(symbol: str, name: str) -> Tuple[str, str]:
    """
    Resolve to canonical fetch symbol/name.

    Returns:
        (fetch_symbol, fetch_name)
    """
    if symbol in ALIAS_MAP:
        return ALIAS_MAP[symbol], name

    for key, target in NAME_ALIASES.items():
        if key in name:
            return target, name

    return symbol, name
