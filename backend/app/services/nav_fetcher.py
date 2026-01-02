"""
Official NAV fetcher for Japanese mutual funds (投信協会).

Workflow:
1. Map fund name -> ISIN.
2. Look for a local NAV CSV (env TOSHIN_NAV_DIR or inputs/nav_cache/{isin}.csv).
3. (Optional) Attempt remote download (left as extension point).
4. Return DataFrame with Date index and 'price' column (JPY NAV).
"""
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Optional, Dict

import pandas as pd

# Fund name to ISIN mapping (extend as needed)
FUND_ISIN_MAP: Dict[str, str] = {
    "eMAXIS Slim 米国株式(S&P500)": "JP90C000J7J5",
    "eMAXIS Slim 全世界株式(オール・カントリー)": "JP90C000H5S9",
    "eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)": "JP90C000H5S9",
    "三菱UFJ 純金ファンド(ファインゴールド)": "JP90C0003K84",
    "eMAXIS Slim 先進国リートインデックス": "JP90C000M4F5",
    "eMAXIS Slim 先進国リートインデックス(除く日本)": "JP90C000M4F5",
    "野村Jリートファンド": "JP90C0008K80",
    "NZAM・ベータ 米国REIT": "JP3027680009",
    "eMAXIS Slim 先進国債券インデックス(除く日本)": "JP90C000H5R1",
    "たわらノーロード インド株式Nifty50": "JP90C000N7F5",
    "ニッセイSOX指数インデックスファンド(米国半導体株)＜購入・換金手数料なし＞": "JP90C000E8T2",
    "iFreeNEXT FANG+インデックス": "JP90C000JDW4",
}


def normalize_name(name: str) -> str:
    return (name or "").strip().upper().replace(" ", "")


class ToshinNavFetcher:
    """
    Fetch NAV history for JP mutual funds from local cache or external source.

    External fetch is intentionally left as an extension hook; by default we
    rely on locally provided CSVs to avoid brittle scraping.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.getenv("TOSHIN_NAV_DIR") or os.path.join("inputs", "nav_cache")

    def get_isin(self, fund_name: str) -> Optional[str]:
        # Exact match
        if fund_name in FUND_ISIN_MAP:
            return FUND_ISIN_MAP[fund_name]
        # Fuzzy (normalize)
        norm = normalize_name(fund_name)
        for k, v in FUND_ISIN_MAP.items():
            if normalize_name(k) in norm or norm in normalize_name(k):
                return v
        return None

    def fetch(self, fund_name: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        isin = self.get_isin(fund_name)
        if not isin:
            return None

        # 1) Local cache first
        nav_df = self._fetch_local(isin, start_date, end_date)
        if nav_df is not None:
            return nav_df

        # 2) External fetch could be implemented here (left as extension)
        # nav_df = self._fetch_remote(isin, start_date, end_date)

        return nav_df

    def _fetch_local(self, isin: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        csv_path = os.path.join(self.cache_dir, f"{isin}.csv")
        if not os.path.exists(csv_path):
            return None
        try:
            df = pd.read_csv(csv_path)
            # Expect columns: Date, NAV (flexible casing)
            date_col = None
            nav_col = None
            for col in df.columns:
                c = col.lower()
                if "date" in c or "基準日" in c:
                    date_col = col
                if "nav" in c or "基準価額" in c:
                    nav_col = col
            if date_col is None or nav_col is None:
                return None
            df[date_col] = pd.to_datetime(df[date_col]).dt.date
            df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
            if df.empty:
                return None
            out = pd.DataFrame({"price": df[nav_col].astype(float)}, index=pd.to_datetime(df[date_col]))
            out.index.name = "date"
            return out
        except Exception as exc:
            print(f"❌ Failed to read NAV cache for {isin}: {exc}")
            return None
