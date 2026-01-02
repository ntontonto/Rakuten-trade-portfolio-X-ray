"""
Yahoo Finance scraper using Playwright (Chromium).

Designed to fetch daily historical prices when API access is unreliable.
Supports both Yahoo Finance Japan and Global sites.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional, List

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


# Japanese date format: 2024年12月30日
JP_DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def _normalize_jp_date(s: str) -> Optional[date]:
    m = JP_DATE_RE.search(s)
    if not m:
        return None
    y, mo, d = map(int, m.groups())
    return date(y, mo, d)


def _parse_number(text: str) -> Optional[float]:
    t = (text or "").strip().replace(",", "")
    if not t or t in {"-", "—"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


class YahooScraperFetcher:
    """Scrape Yahoo Finance (JP site for numeric/JP tickers, global site otherwise)."""

    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug

    def _build_url(self, ticker: str) -> str:
        """
        Build Yahoo Finance URL based on ticker format
        
        Rules:
        - .T suffix → Yahoo Finance Japan (remove .T)
        - Pure digits → Yahoo Finance Japan
        - Starts with digits + letter (e.g., 0331418A) → Yahoo Finance Japan
        - Otherwise → Yahoo Finance Global
        """
        # JP site for .T tickers
        if ticker.endswith(".T"):
            code = ticker.replace(".T", "")
            return f"https://finance.yahoo.co.jp/quote/{code}/history"
        
        # JP site for pure numeric codes
        if ticker.isdigit():
            return f"https://finance.yahoo.co.jp/quote/{ticker}/history"
        
        # JP site for fund codes like "0331418A" (digits + single letter)
        if len(ticker) > 1 and ticker[:-1].isdigit() and ticker[-1].isalpha():
            return f"https://finance.yahoo.co.jp/quote/{ticker}/history"
        
        # Global site for everything else
        return f"https://finance.yahoo.com/quote/{ticker}/history"
    
    def _log(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[YahooScraper] {message}")

    def fetch(self, ticker: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        """
        Fetch historical prices from Yahoo Finance
        
        Args:
            ticker: Ticker symbol (e.g., "0331418A", "1326", "PLTR")
            start_date: Start date for price history
            end_date: End date for price history
            
        Returns:
            DataFrame with date index and 'price' column, or None if failed
        """
        url = self._build_url(ticker)
        self._log(f"Fetching {ticker} from {url}")
        records: List[dict] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                self._log(f"Loading page...")
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1500)  # Increased wait time
                self._log(f"Page loaded")
            except PWTimeout:
                self._log(f"Timeout loading page")
                browser.close()
                return None
            except Exception as e:
                self._log(f"Error loading page: {e}")
                browser.close()
                return None

            # Try to click period buttons on JP site (10年 > 5年 > 3年)
            for label in ("10年", "5年", "3年"):
                btn = page.get_by_text(label, exact=True)
                if btn.count() > 0:
                    try:
                        self._log(f"Clicking {label} button")
                        btn.first.click(timeout=2000)
                        page.wait_for_timeout(1000)
                        break
                    except PWTimeout:
                        self._log(f"Timeout clicking {label} button")
                        pass
                    except Exception as e:
                        self._log(f"Error clicking {label} button: {e}")
                        pass

            # Try multiple table selectors (Yahoo Finance has different layouts)
            table_selectors = [
                "table",  # Generic table
                "table.padst-basic-table",  # Specific Yahoo JP class
                "table.historical-data-table",  # Alternative class
                "[data-test='historical-prices'] table",  # Global site
            ]
            
            rows_locator = None
            for selector in table_selectors:
                try:
                    test_rows = page.locator(f"{selector} tr")
                    count = test_rows.count()
                    if count > 0:
                        self._log(f"Found {count} rows with selector: {selector}")
                        rows_locator = test_rows
                        break
                except Exception as e:
                    self._log(f"Selector {selector} failed: {e}")
                    continue
            
            if rows_locator is None:
                self._log("No table found with any selector")
                # Save screenshot for debugging if not headless
                if self.debug and not self.headless:
                    page.screenshot(path=f"debug_{ticker}.png")
                browser.close()
                return None

            # Parse table rows
            n = rows_locator.count()
            self._log(f"Parsing {n} table rows")
            
            for i in range(n):
                try:
                    tr = rows_locator.nth(i)
                    cells = tr.locator("td")
                    cell_count = cells.count()
                    
                    # Skip header rows (usually have <th> tags or < 2 cells)
                    if cell_count < 2:
                        continue

                    # First column: Date
                    date_text = cells.nth(0).inner_text().strip()
                    
                    # Skip if first cell doesn't look like a date
                    if not any(char.isdigit() for char in date_text):
                        continue
                    
                    # Try Japanese date format first
                    parsed_date = _normalize_jp_date(date_text)
                    
                    # Try ISO format
                    if not parsed_date:
                        try:
                            parsed_date = datetime.fromisoformat(date_text).date()
                        except Exception:
                            pass
                    
                    # Try other common formats (MM/DD/YYYY, etc.)
                    if not parsed_date:
                        for fmt in ["%m/%d/%Y", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%d"]:
                            try:
                                parsed_date = datetime.strptime(date_text, fmt).date()
                                break
                            except Exception:
                                continue
                    
                    if not parsed_date:
                        self._log(f"Could not parse date: {date_text}")
                        continue

                    # Filter by date range
                    if parsed_date < start_date or parsed_date > end_date:
                        continue

                    # Second column is usually the price/NAV for JP mutual funds
                    # For stocks it might be the closing price
                    # Try cell 1 first (NAV/Close), then last cell as fallback
                    price = None
                    
                    if cell_count >= 2:
                        price_text = cells.nth(1).inner_text().strip()
                        price = _parse_number(price_text)
                    
                    # If cell 1 didn't work, try last column
                    if price is None and cell_count > 2:
                        price_text = cells.nth(cell_count - 1).inner_text().strip()
                        price = _parse_number(price_text)
                    
                    if price is None or price <= 0:
                        self._log(f"Invalid price at row {i}: {date_text}")
                        continue

                    records.append({"date": parsed_date, "price": price})
                    
                except Exception as e:
                    self._log(f"Error parsing row {i}: {e}")
                    continue

            self._log(f"Found {len(records)} valid records")
            browser.close()

        if not records:
            self._log("No records extracted")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(records).drop_duplicates(subset=["date"]).sort_values("date")
        df.set_index(pd.to_datetime(df["date"]), inplace=True)
        df.index.name = "date"
        df = df[["price"]]
        
        self._log(f"Returning DataFrame with {len(df)} rows")
        return df
