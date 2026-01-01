"""
Yahoo Finance scraper using Playwright (Chromium).

Enhanced version with support for:
- Daily (日次) and Weekly (週間) data
- Custom calculation start date
- Better error handling and debugging
"""
from __future__ import annotations

import os
import re
import time
from datetime import date, datetime, timedelta
from typing import Optional, List, Literal

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


# Japanese date format: 2024年12月30日
JP_DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")

# Frequency types
FrequencyType = Literal["daily", "weekly"]


def _normalize_jp_date(s: str) -> Optional[date]:
    m = JP_DATE_RE.search(s)
    if not m:
        return None
    y, mo, d = map(int, m.groups())
    return date(y, mo, d)


def _parse_number(text: str) -> Optional[float]:
    t = (text or "").strip().replace(",", "")
    if not t or t in {"-", "—", ""}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


class YahooScraperFetcher:
    """
    Scrape Yahoo Finance with enhanced features
    
    Features:
    - Support for daily and weekly data
    - Custom calculation start date
    - Better debugging and error handling
    """

    def __init__(self, headless: bool = True, debug: bool = False, debug_dir: str = "/tmp/yahoo_scraper_debug"):
        self.headless = headless
        self.debug = debug
        self.debug_dir = debug_dir
        if debug:
            os.makedirs(debug_dir, exist_ok=True)

    def _build_url(self, ticker: str, frequency: FrequencyType = "daily") -> str:
        """
        Build Yahoo Finance URL based on ticker format and frequency
        
        Args:
            ticker: Ticker symbol
            frequency: "daily" or "weekly"
            
        Rules:
        - .T suffix → Yahoo Finance Japan (remove .T)
        - Pure digits → Yahoo Finance Japan
        - Starts with digits + letter (e.g., 0331418A) → Yahoo Finance Japan
        - Otherwise → Yahoo Finance Global
        """
        # Determine base URL
        base_url = None
        
        if ticker.endswith(".T"):
            code = ticker.replace(".T", "")
            base_url = f"https://finance.yahoo.co.jp/quote/{code}/history"
        elif ticker.isdigit():
            base_url = f"https://finance.yahoo.co.jp/quote/{ticker}/history"
        elif len(ticker) > 1 and ticker[:-1].isdigit() and ticker[-1].isalpha():
            base_url = f"https://finance.yahoo.co.jp/quote/{ticker}/history"
        else:
            base_url = f"https://finance.yahoo.com/quote/{ticker}/history"
        
        # Add frequency parameter for Yahoo Finance Japan
        if "yahoo.co.jp" in base_url and frequency == "weekly":
            # Yahoo Finance Japan uses 'w' for weekly
            base_url += "?frequency=w"
        
        return base_url
    
    def _log(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[YahooScraper] {message}")

    # ===== Phase 1: Enhanced Dynamic Content Detection =====

    def _wait_for_table_ready(self, page, timeout_ms=10000) -> bool:
        """
        Wait for table to be fully loaded with stable row count

        Returns:
            True if table loaded successfully, False if timeout
        """
        try:
            # Wait for table element to exist
            page.wait_for_selector("table", timeout=timeout_ms)

            # Wait for stable row count (no changes for 500ms)
            start_time = time.time()
            last_count = 0
            stable_ms = 0
            required_stability_ms = 500

            while (time.time() - start_time) * 1000 < timeout_ms:
                current_count = page.locator("table tr").count()

                if current_count == last_count and current_count > 0:
                    stable_ms += 100
                    if stable_ms >= required_stability_ms:
                        self._log(f"Table stable with {current_count} rows")
                        return True
                else:
                    stable_ms = 0
                    last_count = current_count

                page.wait_for_timeout(100)

            # Timeout reached but we have some rows
            if last_count > 0:
                self._log(f"Table load timeout but found {last_count} rows")
                return True

            return False

        except Exception as e:
            self._log(f"Error waiting for table: {e}")
            return False

    # ===== Phase 2: Multi-Strategy Frequency Selection =====

    def _select_frequency(self, page, frequency: FrequencyType) -> bool:
        """
        Try multiple strategies to select weekly frequency

        Returns:
            True if selection verified, False otherwise
        """
        if frequency != "weekly":
            return True  # Daily is default

        self._log("Attempting to select weekly frequency...")

        # Strategy 1: Select dropdown (most reliable for Yahoo Japan)
        if self._try_select_dropdown(page):
            self._log("Weekly selected via dropdown")
            return True

        # Strategy 2: Check if URL parameter already worked
        if "frequency=w" in page.url or "period=w" in page.url:
            self._log("Weekly frequency in URL")
            if self._verify_frequency_selection(page, "週間"):
                return True

        # Strategy 3: Radio buttons
        if self._try_radio_buttons(page):
            self._log("Weekly selected via radio button")
            return True

        # Strategy 4: React component
        if self._try_react_component(page):
            self._log("Weekly selected via React component")
            return True

        # Strategy 5: Button element
        if self._try_frequency_button(page):
            self._log("Weekly selected via button")
            return True

        self._log("WARNING: Could not confirm weekly frequency selection")
        return False

    def _verify_frequency_selection(self, page, expected_text: str) -> bool:
        """Verify that frequency selection worked by checking UI state and URL"""
        try:
            # Check for selected/active state with expected text
            active_selectors = [
                f"*[aria-selected='true']:has-text('{expected_text}')",
                f"*.selected:has-text('{expected_text}')",
                f"*.active:has-text('{expected_text}')",
                f"input[checked]:has-text('{expected_text}')"
            ]

            for selector in active_selectors:
                if page.locator(selector).count() > 0:
                    self._log(f"Verified weekly selection: found {selector}")
                    return True

            # Check URL contains frequency parameter
            if "frequency=w" in page.url or "period=w" in page.url:
                self._log("Verified weekly selection: URL parameter")
                return True

            return False

        except Exception as e:
            self._log(f"Verification failed: {e}")
            return False

    def _try_select_dropdown(self, page) -> bool:
        """Try to find and use <select> element"""
        try:
            selects = page.locator("select")
            for i in range(selects.count()):
                select = selects.nth(i)
                options_text = select.inner_text()
                if "週間" in options_text or "weekly" in options_text.lower():
                    self._log(f"Found frequency select dropdown")
                    try:
                        # Try selecting by value first (more reliable)
                        select.select_option(value="weekly")
                        self._log("Selected 'weekly' from dropdown")
                        page.wait_for_timeout(500)

                        # Look for and click the display button (表示)
                        display_buttons = [
                            "a:has-text('表示')",
                            "button:has-text('表示')",
                            "[data-cl-params*='display']"
                        ]

                        # Set up network listener to capture API calls
                        api_response = None

                        def handle_response(response):
                            nonlocal api_response
                            if "/bff-pc/v1/main/fund/price/history/" in response.url:
                                self._log(f"Captured BFF API call: {response.url}")
                                api_response = response

                        page.on("response", handle_response)

                        for btn_selector in display_buttons:
                            btn = page.locator(btn_selector)
                            if btn.count() > 0:
                                self._log(f"Clicking '表示' button")
                                try:
                                    # Click the button
                                    btn.first.click()
                                    # Wait for API response
                                    page.wait_for_timeout(2000)

                                    if api_response:
                                        self._log(f"BFF API response received, status: {api_response.status}")
                                        # Wait for table to update
                                        page.wait_for_timeout(1000)
                                        self._wait_for_table_ready(page)
                                        return True
                                    else:
                                        # Old behavior: wait for navigation
                                        page.wait_for_load_state("networkidle", timeout=15000)
                                        page.wait_for_timeout(1000)
                                        self._wait_for_table_ready(page)
                                        return True
                                except Exception as e:
                                    self._log(f"Error after clicking display button: {e}")
                                    continue
                                finally:
                                    page.remove_listener("response", handle_response)

                        # If no display button found, try verification anyway
                        page.wait_for_timeout(1500)
                        return self._verify_frequency_selection(page, "週間")

                    except Exception as e:
                        self._log(f"Error in dropdown selection: {e}")
                        # Try with label as fallback
                        try:
                            select.select_option(label="週間")
                            page.wait_for_timeout(1500)
                            return self._verify_frequency_selection(page, "週間")
                        except:
                            pass
        except Exception as e:
            self._log(f"Select dropdown strategy failed: {e}")
        return False

    def _try_radio_buttons(self, page) -> bool:
        """Try to find and click radio button for weekly"""
        try:
            # Look for radio inputs with weekly value
            radios = page.locator("input[type='radio']")
            for i in range(radios.count()):
                radio = radios.nth(i)
                value = radio.get_attribute("value") or ""

                if "week" in value.lower() or value.lower() == "w":
                    radio.click()
                    page.wait_for_timeout(1500)
                    return self._verify_frequency_selection(page, "週間")

            # Try clicking label with "週間" text
            labels = page.locator("label:has-text('週間')")
            if labels.count() > 0:
                labels.first.click()
                page.wait_for_timeout(1500)
                return self._verify_frequency_selection(page, "週間")

        except Exception as e:
            self._log(f"Radio button strategy failed: {e}")
        return False

    def _try_react_component(self, page) -> bool:
        """Try to click React component for weekly"""
        try:
            selectors = [
                "button:has-text('週間')",
                "div[role='button']:has-text('週間')",
                "span[role='button']:has-text('週間')",
                "a:has-text('週間')",
                "[data-frequency='weekly']",
                "[data-period='weekly']"
            ]

            for selector in selectors:
                elements = page.locator(selector)
                if elements.count() > 0:
                    elements.first.click()
                    page.wait_for_timeout(1500)
                    if self._verify_frequency_selection(page, "週間"):
                        return True
        except Exception as e:
            self._log(f"React component strategy failed: {e}")
        return False

    def _try_frequency_button(self, page) -> bool:
        """Try to click a frequency toggle button"""
        try:
            buttons = page.locator("button")
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                text = btn.inner_text().strip()
                if text in ["週間", "Weekly", "W"]:
                    btn.click()
                    page.wait_for_timeout(1500)
                    return self._verify_frequency_selection(page, "週間")
        except Exception as e:
            self._log(f"Button strategy failed: {e}")
        return False

    # ===== Phase 3: Improved Pagination State Verification =====

    def _capture_page_state(self, page) -> dict:
        """
        Capture current page state for comparison

        Returns dict with first_date, row_count, pagination_text, url
        """
        try:
            # Get first date in table
            first_cell = page.locator("table tr td").first
            first_date = first_cell.inner_text() if first_cell.count() > 0 else ""

            # Get row count
            row_count = page.locator("table tr").count()

            # Get pagination info (e.g., "1〜20/ 243件")
            pagination_text = ""
            page_info = page.locator("*:has-text('〜')")
            if page_info.count() > 0:
                pagination_text = page_info.first.inner_text()

            return {
                "first_date": first_date,
                "row_count": row_count,
                "pagination_text": pagination_text,
                "url": page.url
            }
        except Exception as e:
            self._log(f"Error capturing page state: {e}")
            return {}

    def _verify_page_changed(self, page, before_state: dict, max_wait_ms=5000) -> bool:
        """
        Verify that page content actually changed after clicking next

        Checks if first date, pagination text, or URL changed
        """
        start_time = time.time()

        while (time.time() - start_time) * 1000 < max_wait_ms:
            page.wait_for_timeout(200)
            after_state = self._capture_page_state(page)

            # Check if any state changed
            if after_state.get("first_date") != before_state.get("first_date"):
                self._log("Page changed: first date different")
                return True

            if after_state.get("pagination_text") != before_state.get("pagination_text"):
                self._log("Page changed: pagination text different")
                return True

            if after_state.get("url") != before_state.get("url"):
                self._log("Page changed: URL different")
                return True

        return False

    def _find_next_button(self, page):
        """
        Find the next button using multiple strategies

        Returns Playwright element or None
        """
        selectors = [
            "p:has-text('次へ')",  # Yahoo Finance uses <p> for pagination
            ".pager p:has-text('次へ')",  # More specific for Yahoo Finance
            "a:has-text('次へ')",
            "button:has-text('次へ')",
            "[aria-label='次へ']",
            "[aria-label='Next']",
            ".pagination a:has-text('次へ')",
            "a[rel='next']",
            "div[role='button']:has-text('次へ')",
            "span[role='button']:has-text('次へ')"
        ]

        for selector in selectors:
            elements = page.locator(selector)
            if elements.count() > 0:
                self._log(f"Found next button with selector: {selector}")
                return elements.first

        return None

    def _is_button_disabled(self, button) -> bool:
        """Check if button is disabled through various methods"""
        try:
            # Check disabled attribute
            if button.get_attribute("disabled") is not None:
                return True

            # Check aria-disabled
            if button.get_attribute("aria-disabled") == "true":
                return True

            # Check class names
            class_list = button.get_attribute("class") or ""
            if any(cls in class_list for cls in ["disabled", "inactive", "off"]):
                return True

            # Check for pointer-events: none (CSS disabled)
            try:
                pointer_events = button.evaluate("el => window.getComputedStyle(el).pointerEvents")
                if pointer_events == "none":
                    return True
            except:
                pass

            return False
        except Exception as e:
            self._log(f"Error checking button state: {e}")
            return False

    # ===== Phase 4: Enhanced Debug Mode =====

    def _debug_snapshot(self, page, stage: str, ticker: str):
        """
        Save debug snapshot (screenshot + HTML) if debug mode enabled

        Args:
            stage: e.g., "initial_load", "after_weekly_select", "page_2"
        """
        if not self.debug:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{ticker}_{stage}_{timestamp}"

        try:
            # Screenshot
            screenshot_path = os.path.join(self.debug_dir, f"{base_name}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            self._log(f"Screenshot saved: {screenshot_path}")

            # HTML dump
            html_path = os.path.join(self.debug_dir, f"{base_name}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            self._log(f"HTML saved: {html_path}")

            # Page state info
            info_path = os.path.join(self.debug_dir, f"{base_name}_info.txt")
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"URL: {page.url}\n")
                f.write(f"Title: {page.title()}\n")
                f.write(f"Table rows: {page.locator('table tr').count()}\n")
                f.write(f"Stage: {stage}\n")
                f.write(f"Timestamp: {timestamp}\n")

        except Exception as e:
            self._log(f"Error saving debug snapshot: {e}")

    def _debug_element_info(self, page, description: str):
        """Log information about page elements for debugging"""
        if not self.debug:
            return

        self._log(f"\n=== Debug: {description} ===")
        self._log(f"URL: {page.url}")

        try:
            # Check for select elements
            selects = page.locator("select").count()
            self._log(f"Select elements: {selects}")

            # Check for radio buttons
            radios = page.locator("input[type='radio']").count()
            self._log(f"Radio buttons: {radios}")

            # Check for tables
            tables = page.locator("table").count()
            self._log(f"Tables: {tables}")

            # Check for pagination
            next_btns = page.locator("*:has-text('次へ')").count()
            self._log(f"'次へ' elements: {next_btns}")
        except Exception as e:
            self._log(f"Error in debug element info: {e}")

        self._log("=== End Debug ===\n")

    def _parse_bff_response(self, bff_records: List[dict], start_date: date, end_date: date) -> List[dict]:
        """
        Parse BFF API response into our standard record format

        Expected BFF format (example):
        {
            "date": "2025-12-29",
            "nav": 33428,
            "diff": 2,
            "aum": 9058989
        }
        """
        parsed_records = []

        for item in bff_records:
            try:
                # Parse date (various formats possible)
                date_str = item.get("date") or item.get("日付") or item.get("tradeDate")
                if not date_str:
                    continue

                # Try parsing different date formats
                parsed_date = None
                # Try YYYY-MM-DD
                try:
                    parsed_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                except:
                    pass

                # Try YYYYMMDD
                if not parsed_date:
                    try:
                        parsed_date = datetime.strptime(str(date_str), "%Y%m%d").date()
                    except:
                        pass

                # Try Japanese format
                if not parsed_date:
                    parsed_date = _normalize_jp_date(str(date_str))

                if not parsed_date:
                    self._log(f"Could not parse date: {date_str}")
                    continue

                # Filter by date range
                if parsed_date < start_date or parsed_date > end_date:
                    continue

                # Parse NAV (multiple possible field names)
                nav = (
                    item.get("nav") or
                    item.get("基準価額") or
                    item.get("basePrice") or
                    item.get("price")
                )

                if nav is not None:
                    nav = float(str(nav).replace(",", ""))

                if not nav or nav <= 0:
                    continue

                # Parse diff
                diff = item.get("diff") or item.get("前日差") or item.get("change")
                if diff is not None:
                    diff = float(str(diff).replace(",", ""))

                # Parse AUM (in millions)
                aum = item.get("aum") or item.get("純資産") or item.get("netAssets")
                if aum is not None:
                    aum = float(str(aum).replace(",", ""))

                parsed_records.append({
                    "date": parsed_date,
                    "price": nav,
                    "nav": nav,
                    "diff": diff,
                    "aum_million": aum
                })

            except Exception as e:
                self._log(f"Error parsing BFF record: {e}")
                continue

        self._log(f"Parsed {len(parsed_records)} records from BFF API")
        return parsed_records

    def _convert_to_dataframe(self, records: List[dict], calc_start_date: Optional[date] = None) -> Optional[pd.DataFrame]:
        """Convert records to DataFrame with standard formatting"""
        if not records:
            self._log("No records to convert")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(records)

        # Deduplicate by date (keep first occurrence)
        original_len = len(df)
        df = df.drop_duplicates(subset=["date"], keep="first")
        deduped_len = len(df)
        if original_len != deduped_len:
            self._log(f"Deduplicated: {original_len} → {deduped_len} rows ({original_len - deduped_len} duplicates removed)")

        # Sort by date
        df = df.sort_values("date")

        # Set date index
        df.set_index(pd.to_datetime(df["date"]), inplace=True)
        df.index.name = "date"

        # Keep all columns (price, nav, diff, aum_million)
        available_cols = ["price", "nav", "diff", "aum_million"]
        cols_to_keep = [col for col in available_cols if col in df.columns]
        df = df[cols_to_keep]

        # Apply calculation start date filter if provided
        if calc_start_date:
            original_len = len(df)
            df = df[df.index.date >= calc_start_date]
            filtered_len = len(df)
            self._log(f"Filtered by calc_start_date: {original_len} → {filtered_len} rows")

        self._log(f"Returning DataFrame with {len(df)} rows")
        if len(df) > 0:
            self._log(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
            self._log(f"NAV range: ¥{df['price'].min():.2f} to ¥{df['price'].max():.2f}")

        return df

    def _fetch_via_bff_api(
        self,
        page,
        ticker: str,
        start_date: date,
        end_date: date,
        frequency: FrequencyType = "daily"
    ) -> Optional[List[dict]]:
        """
        Fetch data using Yahoo Finance BFF API directly

        Returns list of records if successful, None otherwise
        """
        # Build BFF API URL
        timeframe_map = {"daily": "daily", "weekly": "weekly"}
        timeframe = timeframe_map.get(frequency, "daily")

        from_date_str = start_date.strftime("%Y%m%d")
        to_date_str = end_date.strftime("%Y%m%d")

        # Try to fetch all pages
        all_records = []
        page_num = 1
        max_pages = 50

        while page_num <= max_pages:
            api_url = (
                f"https://finance.yahoo.co.jp/bff-pc/v1/main/fund/price/history/{ticker}"
                f"?displayedMaxPage=5&fromDate={from_date_str}&page={page_num}&size=20"
                f"&timeFrame={timeframe}&toDate={to_date_str}"
            )

            self._log(f"Trying BFF API: page {page_num}")
            self._log(f"URL: {api_url}")

            try:
                # Use page.evaluate to fetch from within browser context (has cookies)
                result = page.evaluate(f"""
                    async () => {{
                        try {{
                            const response = await fetch('{api_url}');
                            const status = response.status;
                            if (status === 200) {{
                                const data = await response.json();
                                return {{ status, data }};
                            }} else {{
                                return {{ status, data: null }};
                            }}
                        }} catch (error) {{
                            return {{ status: 0, error: error.message }};
                        }}
                    }}
                """)

                status = result.get("status", 0)

                if status == 200:
                    data = result.get("data")
                    self._log(f"BFF API success: {status}")

                    # Parse response structure
                    if isinstance(data, dict):
                        # Extract items/rows from response
                        items = data.get("items", []) or data.get("rows", []) or data.get("data", [])

                        if items:
                            self._log(f"Found {len(items)} items on page {page_num}")
                            all_records.extend(items)

                            # Check if there are more pages
                            total_pages = data.get("totalPage", 1)
                            if page_num >= total_pages:
                                self._log(f"Reached last page ({page_num}/{total_pages})")
                                break
                        else:
                            self._log(f"No items in response for page {page_num}")
                            break
                    else:
                        self._log(f"Unexpected response format")
                        break

                    page_num += 1

                elif status == 401:
                    self._log(f"BFF API requires authentication (401)")
                    return None
                elif status == 404:
                    self._log(f"BFF API endpoint not found (404)")
                    return None
                elif status == 0:
                    error_msg = result.get("error", "Unknown error")
                    self._log(f"BFF API fetch error: {error_msg}")
                    return None
                else:
                    self._log(f"BFF API error: {status}")
                    return None

            except Exception as e:
                self._log(f"Error calling BFF API: {e}")
                return None

        if all_records:
            self._log(f"BFF API total: {len(all_records)} records from {page_num - 1} pages")
            return all_records

        return None

    def _get_first_date_in_table(self, page) -> Optional[str]:
        """Get the first date from the history table"""
        try:
            # Yahoo Finance Japan structure: table td.date__3Kj4
            first_row = page.locator("table tbody tr").first
            if first_row.count() > 0:
                date_cell = first_row.locator("td").first
                return date_cell.inner_text().strip()
            return None
        except:
            return None

    def _set_date_range(self, page, start_date: date, end_date: date, ticker: str = "unknown") -> bool:
        """
        Set custom date range on Yahoo Finance Japan page

        Args:
            page: Playwright page object
            start_date: Start date for history
            end_date: End date for history

        Returns:
            True if date range was set successfully, False otherwise
        """
        try:
            # Format dates as YYYY/MM/DD (Yahoo Finance Japan format)
            start_str = start_date.strftime('%Y/%m/%d')
            end_str = end_date.strftime('%Y/%m/%d')

            self._log(f"Attempting to set date range: {start_str} to {end_str}")

            # Strategy 1: Try flatpickr API via JavaScript
            try:
                # Set start date
                page.evaluate(f"""
                    const fromInput = document.querySelector('#historyTermFromDate');
                    if (fromInput && fromInput._flatpickr) {{
                        fromInput._flatpickr.setDate('{start_str}', true);
                    }}
                """)

                # Set end date
                page.evaluate(f"""
                    const toInput = document.querySelector('#historyTermToDate');
                    if (toInput && toInput._flatpickr) {{
                        toInput._flatpickr.setDate('{end_str}', true);
                    }}
                """)

                self._log("Set dates via flatpickr API")

            except Exception as e:
                self._log(f"Flatpickr API failed: {e}, trying alternative method")

                # Strategy 2: Click and fill
                page.click('#historyTermFromDate')
                page.wait_for_timeout(300)
                page.fill('#historyTermFromDate', start_str)

                page.click('#historyTermToDate')
                page.wait_for_timeout(300)
                page.fill('#historyTermToDate', end_str)

                self._log("Set dates via click and fill")

            # Capture state before clicking display
            before_state = self._capture_page_state(page)

            # Find and click "表示" (Display) button
            display_btn = page.locator("a:has-text('表示')").first
            if display_btn.count() == 0:
                self._log("Display button not found")
                return False

            self._log("Clicking '表示' button")
            display_btn.click(timeout=3000)

            # Wait for page to update (either navigation or AJAX)
            # Try waiting for navigation first
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except:
                # If no navigation, just wait for timeout
                page.wait_for_timeout(2000)

            # Verify page changed
            if not self._verify_page_changed(page, before_state, max_wait_ms=5000):
                self._log("WARNING: Page may not have updated after clicking display")

            # Wait for table to be ready with new data
            if not self._wait_for_table_ready(page):
                self._log("WARNING: Table may not be fully loaded after date change")

                # Check if there's an error message on the page
                try:
                    error_msg = page.locator("text=/不正なアクセス|エラー|データがありません/").first
                    if error_msg.count() > 0:
                        self._log(f"ERROR PAGE DETECTED: {error_msg.inner_text()}")
                except:
                    pass

                # Take debug snapshot to see what the page looks like
                self._debug_snapshot(page, "after_date_set_failed", ticker)
                return False

            # Verify the date range by checking first date in table
            first_date = self._get_first_date_in_table(page)
            if first_date:
                self._log(f"First date in table after update: {first_date}")

            return True

        except Exception as e:
            self._log(f"Error setting date range: {e}")
            return False

    def fetch(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        frequency: FrequencyType = "daily",
        calc_start_date: Optional[date] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical prices from Yahoo Finance
        
        Args:
            ticker: Ticker symbol (e.g., "0331418A", "1326", "PLTR")
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            frequency: "daily" or "weekly" data
            calc_start_date: If provided, filter data from this date for calculations
                            (useful when you want to fetch all data but only use recent data for calcs)
            
        Returns:
            DataFrame with date index and 'price' column, or None if failed
        """
        url = self._build_url(ticker, frequency)
        self._log(f"Fetching {ticker} ({frequency}) from {url}")
        self._log(f"Date range: {start_date} to {end_date}")
        if calc_start_date:
            self._log(f"Calculation start: {calc_start_date}")
        
        records: List[dict] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                self._log(f"Loading page...")
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                # Enhanced wait strategy: wait for network idle
                page.wait_for_load_state("networkidle", timeout=10000)
                self._log(f"Page loaded, waiting for table...")
                # Wait for table to be ready with stable row count
                if not self._wait_for_table_ready(page):
                    self._log("WARNING: Table may not be fully loaded")
                self._log(f"Page ready for parsing")

                # Debug snapshot after initial load
                self._debug_snapshot(page, "initial_load", ticker)
                self._debug_element_info(page, "After initial load")

                # DISABLED: Setting custom date range triggers Yahoo anti-bot protection
                # Yahoo Finance Japan provides ~1 year of data by default
                # For older data, system will use linear interpolation between transactions
                # if "yahoo.co.jp" in url and start_date and end_date:
                #     self._log(f"Setting custom date range on page: {start_date} to {end_date}")
                #     date_set_success = self._set_date_range(page, start_date, end_date, ticker)
                #
                #     if date_set_success:
                #         self._log("✅ Date range set successfully")
                #         self._debug_snapshot(page, "after_date_set", ticker)
                #         # Wait for page to reload with new date range
                #         if not self._wait_for_table_ready(page):
                #             self._log("WARNING: Table may not be fully loaded after date change")
                #     else:
                #         self._log("⚠️ Failed to set date range, continuing with default (may have limited data)")

            except PWTimeout:
                self._log(f"Timeout loading page")
                browser.close()
                return None
            except Exception as e:
                self._log(f"Error loading page: {e}")
                browser.close()
                return None

            # For Yahoo Finance Japan funds, try BFF API first (more reliable)
            if "yahoo.co.jp" in url and (ticker[:-1].isdigit() if ticker else False):
                self._log("Detected Yahoo Finance Japan fund - trying BFF API")
                bff_records = self._fetch_via_bff_api(page, ticker, start_date, end_date, frequency)

                if bff_records:
                    # Successfully got data from BFF API
                    self._log(f"BFF API returned {len(bff_records)} records")
                    browser.close()

                    # Convert BFF API response to our standard format
                    records = self._parse_bff_response(bff_records, start_date, end_date)
                    if records:
                        # Skip HTML scraping and jump to DataFrame conversion
                        df = self._convert_to_dataframe(records, calc_start_date)
                        return df
                    else:
                        self._log("BFF API data parse failed, falling back to HTML scraping")
                else:
                    self._log("BFF API failed, falling back to HTML scraping")

            # Fallback: For Yahoo Finance Japan, try to select frequency using multiple strategies
            if "yahoo.co.jp" in url and frequency == "weekly":
                success = self._select_frequency(page, frequency)
                # Wait for page to update after selection
                if success:
                    self._wait_for_table_ready(page)
                # Debug snapshot after frequency selection
                self._debug_snapshot(page, "after_frequency_select", ticker)
                if not success:
                    self._log("WARNING: Could not verify weekly selection, continuing anyway")

            # Try to click period buttons on JP site (10年 > 5年 > 3年)
            for label in ("10年", "5年", "3年", "1年"):
                btn = page.get_by_text(label, exact=True)
                if btn.count() > 0:
                    try:
                        self._log(f"Clicking {label} button")
                        btn.first.click(timeout=2000)
                        page.wait_for_timeout(1000)
                        break
                    except Exception as e:
                        self._log(f"Could not click {label}: {e}")

            # Pagination loop - collect data from all pages
            page_num = 1
            max_pages = 50  # Safety limit
            
            while page_num <= max_pages:
                self._log(f"Processing page {page_num}...")
                
                # Try multiple table selectors
                table_selectors = [
                    "table",
                    "table.padst-basic-table",
                    "table.historical-data-table",
                    "[data-test='historical-prices'] table",
                ]
                
                rows_locator = None
                for selector in table_selectors:
                    try:
                        test_rows = page.locator(f"{selector} tr")
                        count = test_rows.count()
                        if count > 0:
                            if page_num == 1:
                                self._log(f"Found {count} rows with selector: {selector}")
                            rows_locator = test_rows
                            break
                    except Exception:
                        continue
                
                if rows_locator is None:
                    self._log(f"No table found on page {page_num}")
                    break

                # Parse table rows on current page
                n = rows_locator.count()
                self._log(f"Parsing {n} table rows on page {page_num}")
                
                rows_on_page = 0
                for i in range(n):
                    try:
                        tr = rows_locator.nth(i)
                        cells = tr.locator("td")
                        cell_count = cells.count()
                        
                        if cell_count < 2:
                            continue

                        # Parse date
                        date_text = cells.nth(0).inner_text().strip()
                        if not any(char.isdigit() for char in date_text):
                            continue
                        
                        parsed_date = _normalize_jp_date(date_text)
                        if not parsed_date:
                            for fmt in ["%m/%d/%Y", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%d"]:
                                try:
                                    parsed_date = datetime.strptime(date_text, fmt).date()
                                    break
                                except Exception:
                                    continue
                        
                        if not parsed_date:
                            continue

                        # Filter by date range
                        if parsed_date < start_date or parsed_date > end_date:
                            continue

                        # Parse NAV (基準価額) - typically in column 1
                        nav = None
                        if cell_count >= 2:
                            nav_text = cells.nth(1).inner_text().strip()
                            nav = _parse_number(nav_text)
                        
                        if nav is None and cell_count > 2:
                            nav_text = cells.nth(cell_count - 1).inner_text().strip()
                            nav = _parse_number(nav_text)
                        
                        if nav is None or nav <= 0:
                            continue

                        # Parse diff (前日比) - typically in column 2
                        diff = None
                        if cell_count >= 3:
                            diff_text = cells.nth(2).inner_text().strip()
                            diff = _parse_number(diff_text)
                        
                        # Parse AUM (純資産) - typically in column 3
                        aum = None
                        if cell_count >= 4:
                            aum_text = cells.nth(3).inner_text().strip()
                            aum = _parse_number(aum_text)

                        records.append({
                            "date": parsed_date,
                            "price": nav,  # Keep 'price' for backward compatibility
                            "nav": nav,
                            "diff": diff,
                            "aum_million": aum
                        })
                        rows_on_page += 1
                        
                    except Exception as e:
                        self._log(f"Error parsing row {i} on page {page_num}: {e}")
                        continue

                self._log(f"Found {rows_on_page} valid records on page {page_num}")

                # Debug snapshot for each page
                self._debug_snapshot(page, f"page_{page_num}", ticker)

                # Try to find and click "次へ" (next) button with state verification
                try:
                    # Capture state before clicking
                    before_state = self._capture_page_state(page)

                    # Find next button
                    next_btn = self._find_next_button(page)
                    if next_btn is None:
                        self._log("No next button found - last page reached")
                        break

                    # Check if button is disabled
                    if self._is_button_disabled(next_btn):
                        self._log("Next button is disabled - last page reached")
                        break

                    # Click the button
                    self._log(f"Clicking '次へ' button to go to page {page_num + 1}")
                    next_btn.click(timeout=3000)

                    # Verify page actually changed
                    if not self._verify_page_changed(page, before_state):
                        self._log("Page did not change after clicking next - last page reached")
                        break

                    # Wait for new data to load
                    if not self._wait_for_table_ready(page):
                        self._log("WARNING: Table may not be fully loaded on new page")

                except Exception as e:
                    self._log(f"Error during pagination: {e}")
                    break
                
                page_num += 1

            self._log(f"Pagination complete. Total records: {len(records)}")
            browser.close()

        if not records:
            self._log("No records extracted")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Deduplicate by date (keep first occurrence)
        original_len = len(df)
        df = df.drop_duplicates(subset=["date"], keep="first")
        deduped_len = len(df)
        if original_len != deduped_len:
            self._log(f"Deduplicated: {original_len} → {deduped_len} rows ({original_len - deduped_len} duplicates removed)")
        
        # Sort by date
        df = df.sort_values("date")
        
        # Set date index
        df.set_index(pd.to_datetime(df["date"]), inplace=True)
        df.index.name = "date"
        
        # Keep all columns (price, nav, diff, aum_million)
        # Note: 'price' and 'nav' have the same value for backward compatibility
        available_cols = ["price", "nav", "diff", "aum_million"]
        cols_to_keep = [col for col in available_cols if col in df.columns]
        df = df[cols_to_keep]
        
        # Apply calculation start date filter if provided
        if calc_start_date:
            original_len = len(df)
            df = df[df.index.date >= calc_start_date]
            filtered_len = len(df)
            self._log(f"Filtered by calc_start_date: {original_len} → {filtered_len} rows")
        
        self._log(f"Returning DataFrame with {len(df)} rows")
        if len(df) > 0:
            self._log(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
            self._log(f"NAV range: ¥{df['price'].min():.2f} to ¥{df['price'].max():.2f}")
        
        return df

    def fetch_with_lookback(
        self,
        ticker: str,
        end_date: date,
        lookback_days: int = 365,
        frequency: FrequencyType = "daily",
        calc_start_date: Optional[date] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data with lookback period from end date
        
        Args:
            ticker: Ticker symbol
            end_date: End date (typically today)
            lookback_days: Number of days to look back (default: 365 = 1 year)
            frequency: "daily" or "weekly"
            calc_start_date: Optional start date for calculations
            
        Returns:
            DataFrame with historical prices
        """
        start_date = end_date - timedelta(days=lookback_days)
        self._log(f"Lookback: {lookback_days} days ({start_date} to {end_date})")
        
        return self.fetch(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            calc_start_date=calc_start_date
        )

    def fetch_and_save_csv(
        self,
        ticker: str,
        output_path: str,
        start_date: date,
        end_date: date,
        frequency: FrequencyType = "daily",
        calc_start_date: Optional[date] = None
    ) -> bool:
        """
        Fetch historical data and save as CSV
        
        Args:
            ticker: Ticker symbol (e.g., "0331418A")
            output_path: Path to save CSV file
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            frequency: "daily" or "weekly"
            calc_start_date: Optional filter for calculation start date
            
        Returns:
            True if successful, False otherwise
            
        CSV Format:
            code,date,nav,diff,aum_million
            0331418A,2024-12-30,33250.0,125.0,450000.0
        """
        df = self.fetch(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            calc_start_date=calc_start_date
        )
        
        if df is None or len(df) == 0:
            self._log(f"No data to save for {ticker}")
            return False
        
        # Prepare CSV data
        csv_df = df.copy()
        csv_df['code'] = ticker
        csv_df['date'] = csv_df.index.date
        
        # Reorder columns
        columns = ['code', 'date']
        if 'nav' in csv_df.columns:
            columns.append('nav')
        if 'diff' in csv_df.columns:
            columns.append('diff')
        if 'aum_million' in csv_df.columns:
            columns.append('aum_million')
        
        csv_df = csv_df[columns]
        
        # Save to CSV
        try:
            csv_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            self._log(f"Saved {len(csv_df)} rows to {output_path}")
            return True
        except Exception as e:
            self._log(f"Error saving CSV: {e}")
            return False
