"""
CSV Parser for Rakuten Securities Files

Handles:
- Shift_JIS encoding detection
- Transaction history (US stocks, JP stocks, Investment trusts)
- Asset balance data
- Exchange rate extraction
- Unit conversions (口 → divide by 10,000)
- Name mappings

Ported from JavaScript implementation (index.html lines 450-697)
"""
import io
import re
import csv
import pandas as pd
import chardet
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app.utils.currency import parse_currency, normalize_japanese_text
from app.config import settings


class CSVParser:
    """Parser for Rakuten Securities CSV files"""

    def __init__(self):
        self.name_mappings = settings.NAME_MAPPINGS

    def detect_encoding(self, file_content: bytes) -> str:
        """
        Detect file encoding (usually Shift_JIS for Rakuten CSVs)

        Args:
            file_content: Raw file bytes

        Returns:
            Detected encoding name
        """
        result = chardet.detect(file_content)
        encoding = result.get('encoding', 'shift_jis')

        # Default to shift_jis if detection fails
        if encoding is None or encoding.lower() not in ['shift_jis', 'utf-8', 'cp932']:
            encoding = 'shift_jis'

        return encoding

    def apply_name_mapping(self, name: str) -> str:
        """
        Apply name mappings to standardize fund names

        Args:
            name: Original fund/asset name

        Returns:
            Mapped name or original if no mapping exists
        """
        if not name:
            return ""

        trimmed = name.strip()
        return self.name_mappings.get(trimmed, trimmed)

    def parse_asset_balance(self, file_content: bytes, encoding: str) -> Tuple[List[Dict], Dict[str, float]]:
        """
        Parse asset balance CSV

        Extracts:
        - Current holdings with quantities and market values
        - Exchange rates (USD/JPY)

        Args:
            file_content: Raw file bytes
            encoding: File encoding

        Returns:
            Tuple of (holdings_list, exchange_rates_dict)
        """
        holdings = []
        exchange_rates = {}

        # Read as raw lines to handle irregular structure
        text = file_content.decode(encoding)
        lines = text.split('\n')

        # Parse line by line
        import csv
        data = []
        for line in lines:
            try:
                # Use Python csv module for proper parsing
                row = next(csv.reader([line]))
                data.append(row)
            except:
                data.append([line])  # Fallback for malformed lines

        # Column indices (to be detected)
        col_map = {
            'type': -1,
            'code': -1,
            'name': -1,
            'qty': -1,
            'qty_unit': -1,
            'price': -1,
            'price_unit': -1,
            'value': -1
        }

        header_found = False
        header_row_idx = -1

        for i, row in enumerate(data):
            if pd.isna(row).all():  # Skip empty rows
                continue

            row_str = ','.join([str(x) for x in row if pd.notna(x)])

            # 1. Exchange Rate Extraction
            if '参考為替レート' in row_str:
                # Look ahead for USD rate
                for j in range(1, min(5, len(data) - i)):
                    if i + j < len(data):
                        rate_row = data[i + j]
                        # Find USD or 米ドル
                        for idx, cell in enumerate(rate_row):
                            if pd.notna(cell) and ('USD' in str(cell) or '米ドル' in str(cell)):
                                if idx + 1 < len(rate_row) and pd.notna(rate_row[idx + 1]):
                                    rate = parse_currency(str(rate_row[idx + 1]))
                                    if rate > 0:
                                        exchange_rates['USD'] = rate
                                        print(f"為替レート検出: 1 USD = {rate} JPY")
                                break

            # 2. Find Portfolio Header
            if not header_found:
                has_type = any('種別' in str(cell) for cell in row if pd.notna(cell))
                has_name = any('銘柄' in str(cell) for cell in row if pd.notna(cell))

                if has_type and has_name:
                    header_found = True
                    header_row_idx = i

                    # Map columns
                    for idx, cell in enumerate(row):
                        if pd.isna(cell):
                            continue
                        cell_str = str(cell)

                        if '種別' in cell_str:
                            col_map['type'] = idx
                        if 'コード' in cell_str or 'ティッカー' in cell_str:
                            col_map['code'] = idx
                        if cell_str in ['銘柄', '銘柄名', 'ファンド名']:
                            col_map['name'] = idx
                        if '数量' in cell_str or ('保有' in cell_str and '数量' in cell_str):
                            col_map['qty'] = idx
                        if '現在値' in cell_str:
                            col_map['price'] = idx
                        if '時価評価額' in cell_str and '円' in cell_str:
                            col_map['value'] = idx

                    # Detect unit columns (usually next to qty/price)
                    if col_map['qty'] != -1 and idx + 1 < len(row):
                        if pd.notna(row[col_map['qty'] + 1]) and '単位' in str(row[col_map['qty'] + 1]):
                            col_map['qty_unit'] = col_map['qty'] + 1

                    if col_map['price'] != -1 and col_map['price'] + 1 < len(row):
                        if pd.notna(row[col_map['price'] + 1]) and '単位' in str(row[col_map['price'] + 1]):
                            col_map['price_unit'] = col_map['price'] + 1

                    print(f"資産詳細ヘッダーを検出: QtyIdx={col_map['qty']}, UnitIdx={col_map['qty_unit']}, ValIdx={col_map['value']}")

                continue

            # 3. Read Data Rows
            if not header_found or col_map['type'] == -1:
                continue

            if col_map['type'] >= len(row):
                continue

            asset_type = row[col_map['type']] if col_map['type'] < len(row) else None
            if pd.isna(asset_type) or asset_type == '':
                continue

            # Extract values
            try:
                qty = parse_currency(str(row[col_map['qty']])) if col_map['qty'] != -1 and col_map['qty'] < len(row) else 0
                value = parse_currency(str(row[col_map['value']])) if col_map['value'] != -1 and col_map['value'] < len(row) else 0

                # Unit conversion: If unit is "口", divide qty by 10,000
                if col_map['qty_unit'] != -1 and col_map['qty_unit'] < len(row):
                    unit = str(row[col_map['qty_unit']]).strip() if pd.notna(row[col_map['qty_unit']]) else ''
                    if unit == '口':
                        qty = qty / 10000

                if value > 0:
                    holdings.append({
                        'type': str(asset_type),
                        'code': str(row[col_map['code']]) if col_map['code'] != -1 and col_map['code'] < len(row) and pd.notna(row[col_map['code']]) else None,
                        'name': str(row[col_map['name']]) if col_map['name'] != -1 and col_map['name'] < len(row) and pd.notna(row[col_map['name']]) else None,
                        'qty': qty,
                        'value': value
                    })

            except Exception as e:
                # Skip problematic rows
                continue

        print(f"資産データ抽出完了: {len(holdings)}件")
        return holdings, exchange_rates

    def parse_file(self, file_content: bytes, filename: str) -> Dict:
        """
        Parse CSV file and determine type

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            Dict with 'type' and 'data' keys
        """
        # Detect encoding
        encoding = self.detect_encoding(file_content)

        # Read CSV
        try:
            df = pd.read_csv(
                io.BytesIO(file_content),
                encoding=encoding,
                header=None,  # No header initially
                skip_blank_lines=False,  # Keep blank lines for structure detection
                on_bad_lines='skip',  # Skip malformed lines
                engine='python'  # Use python engine for more flexibility
            )
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")

        # Determine file type by inspecting content
        df_str = df.astype(str).to_string()

        if '資産合計' in df_str or ('種別' in df_str and '時価評価額' in df_str):
            # Asset Balance File
            holdings, exchange_rates = self.parse_asset_balance(file_content, encoding)
            return {
                'type': 'balance',
                'data': holdings,
                'exchange_rates': exchange_rates,
                'filename': filename
            }

        # Decode via csv reader to preserve transaction formatting (esp. INVST points)
        rows = self._read_rows(file_content, encoding)
        tx_type, header_idx = self._detect_transaction_type(rows)

        if tx_type == 'US':
            transactions = self._parse_us_transactions(rows, header_idx)
        elif tx_type == 'JP':
            transactions = self._parse_jp_transactions(rows, header_idx)
        elif tx_type == 'INVST':
            transactions = self._parse_invst_transactions(rows, header_idx)
        else:
            return {
                'type': 'unknown',
                'data': [],
                'filename': filename
            }

        return {
            'type': 'transactions',
            'data': transactions,
            'filename': filename
        }

    def _parse_amount_and_points(self, raw_value) -> Tuple[float, float]:
        """
        Split combined amount/points fields like '5,000(493)' into cash amount and points used.
        """
        if raw_value is None:
            return 0.0, 0.0

        raw_str = str(raw_value)
        amount = parse_currency(raw_str)

        points = 0.0
        match = re.search(r'[（(]([0-9,.,]+)[)）]', raw_str)
        if match:
            points = parse_currency(match.group(1))

        return amount, points

    def _read_rows(self, file_content: bytes, encoding: str) -> List[List[str]]:
        """
        Read CSV content into a list of rows using Python's csv module to keep raw formatting.
        """
        text = file_content.decode(encoding, errors='replace')
        reader = csv.reader(io.StringIO(text))
        return [row for row in reader if row]

    def _detect_transaction_type(self, rows: List[List[str]]) -> Tuple[Optional[str], int]:
        """
        Inspect header rows to decide which transaction parser to use.
        Returns (tx_type, header_index) where tx_type is one of US/JP/INVST or None.
        """
        for idx, row in enumerate(rows[:10]):
            header = ''.join(row)
            has_date = any('約定日' in cell for cell in row)

            if has_date and ('ティッカー' in header):
                return 'US', idx
            if has_date and ('銘柄コード' in header):
                return 'JP', idx
            if has_date and ('ファンド名' in header and '受渡金額/(ポイント利用)[円]' in header):
                return 'INVST', idx
        return None, -1

    def _parse_us_transactions(self, rows: List[List[str]], header_idx: int) -> List[Dict]:
        headers = rows[header_idx]
        data_rows = rows[header_idx + 1:]
        transactions = []

        def get_value(row, column_name):
            try:
                col_idx = headers.index(column_name)
                return row[col_idx] if col_idx < len(row) else ''
            except ValueError:
                return ''

        for row in data_rows:
            if not any(cell.strip() for cell in row):
                continue

            tx = {}
            tx['date'] = pd.to_datetime(get_value(row, '約定日'), errors='coerce')
            tx['symbol'] = str(get_value(row, 'ティッカー') or '')
            tx['name'] = str(get_value(row, '銘柄名') or tx['symbol'])
            tx['type'] = str(get_value(row, '売買区分') or '')
            tx['qty'] = parse_currency(str(get_value(row, '数量［株］') or 0))

            amount_jpy_raw = get_value(row, '受渡金額［円］')
            if amount_jpy_raw not in ['-', '', None]:
                tx['amount_jpy'] = parse_currency(str(amount_jpy_raw))
            else:
                usd = parse_currency(str(get_value(row, '受渡金額［USドル］') or get_value(row, '約定代金［USドル］') or 0))
                rate = parse_currency(str(get_value(row, '為替レート') or 0))
                tx['amount_jpy'] = abs(usd * rate)

            tx['market'] = 'US'
            self._finalize_transaction(tx)
            if tx:
                transactions.append(tx)

        print(f"取引データ抽出(US): {len(transactions)}件")
        return transactions

    def _parse_jp_transactions(self, rows: List[List[str]], header_idx: int) -> List[Dict]:
        headers = rows[header_idx]
        data_rows = rows[header_idx + 1:]
        transactions = []

        def get_value(row, column_name):
            try:
                col_idx = headers.index(column_name)
                return row[col_idx] if col_idx < len(row) else ''
            except ValueError:
                return ''

        for row in data_rows:
            if not any(cell.strip() for cell in row):
                continue

            tx = {}
            tx['date'] = pd.to_datetime(get_value(row, '約定日'), errors='coerce')
            tx['symbol'] = str(get_value(row, '銘柄コード') or '')
            tx['name'] = str(get_value(row, '銘柄名') or '')
            tx['type'] = str(get_value(row, '売買区分') or '')
            tx['qty'] = parse_currency(str(get_value(row, '数量［株］') or 0))
            tx['amount_jpy'] = parse_currency(str(get_value(row, '受渡金額［円］') or 0))
            tx['market'] = 'JP'

            self._finalize_transaction(tx)
            if tx:
                transactions.append(tx)

        print(f"取引データ抽出(JP): {len(transactions)}件")
        return transactions

    def _parse_invst_transactions(self, rows: List[List[str]], header_idx: int) -> List[Dict]:
        headers = rows[header_idx]
        data_rows = rows[header_idx + 1:]
        transactions = []

        def get_value(row, column_name):
            try:
                col_idx = headers.index(column_name)
                return row[col_idx] if col_idx < len(row) else ''
            except ValueError:
                return ''

        # Check if quantity uses "口" units to normalize
        qty_header = next((h for h in headers if '数量' in h and '口' in h), None)
        normalize_kuchi = qty_header is not None

        for row in data_rows:
            if not any(cell.strip() for cell in row):
                continue

            tx = {}
            tx['date'] = pd.to_datetime(get_value(row, '約定日'), errors='coerce')

            raw_name = str(get_value(row, 'ファンド名') or '')
            mapped_name = self.apply_name_mapping(raw_name)
            tx['symbol'] = mapped_name
            tx['name'] = mapped_name
            tx['type'] = str(get_value(row, '取引') or get_value(row, '取引区分') or '')

            qty = parse_currency(str(get_value(row, '数量［口］') or 0))
            if normalize_kuchi:
                qty = qty / 10000  # Normalize to 万口 basis
            tx['qty'] = qty

            raw_amount = get_value(row, '受渡金額/(ポイント利用)[円]') or get_value(row, '受渡金額［円］')
            amount_jpy, points_used = self._parse_amount_and_points(raw_amount)
            tx['amount_jpy'] = amount_jpy
            tx['points_used'] = points_used
            tx['market'] = 'INVST'

            self._finalize_transaction(tx)
            if tx:
                transactions.append(tx)

        print(f"取引データ抽出(INVST): {len(transactions)}件")
        return transactions

    def _finalize_transaction(self, tx: Dict) -> None:
        """
        Normalize side/validation; mutates tx or clears it if invalid.
        """
        if pd.isna(tx.get('date')) or tx.get('amount_jpy', 0) <= 0:
            tx.clear()
            return

        tx_type = str(tx.get('type', '')).strip()
        if any(keyword in tx_type for keyword in ['買', '再投資', '積立']):
            tx['side'] = 'BUY'
        elif any(keyword in tx_type for keyword in ['売', '解約']):
            tx['side'] = 'SELL'
        else:
            tx['side'] = 'OTHER'

        tx['asset_class'] = None  # Classified later
