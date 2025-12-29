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

    def parse_transaction_history(self, df: pd.DataFrame) -> List[Dict]:
        """
        Parse transaction history CSV

        Handles:
        - US stocks (ティッカー)
        - JP stocks (銘柄コード)
        - Investment trusts (ファンド名)

        Args:
            df: DataFrame from CSV

        Returns:
            List of transaction dicts
        """
        transactions = []

        # Detect header row
        header_row_idx = -1
        for idx in range(min(10, len(df))):
            row = df.iloc[idx]
            if '約定日' in row.values and ('銘柄名' in row.values or 'ティッカー' in row.values or 'ファンド名' in row.values):
                header_row_idx = idx
                break

        if header_row_idx == -1:
            return []  # Not a transaction history file

        # Set header
        headers = df.iloc[header_row_idx].tolist()
        data_df = df.iloc[header_row_idx + 1:].copy()
        data_df.columns = headers

        # Determine market type
        is_us = 'ティッカー' in headers
        is_invst = 'ファンド名' in headers
        is_jp = '銘柄コード' in headers and not is_us

        file_type = '米国株' if is_us else ('投資信託' if is_invst else '日本株')
        print(f"取引履歴ファイル検出: {file_type}")

        # Check if quantity column has [口] unit
        qty_header_with_unit = None
        for header in headers:
            if '数量' in str(header) and ('口' in str(header) or '［口］' in str(header)):
                qty_header_with_unit = header
                break
        is_unit_kuchi = qty_header_with_unit is not None

        # Process rows
        for _, row in data_df.iterrows():
            try:
                # Skip empty rows
                if row.isna().all():
                    continue

                tx = {}

                if is_us:
                    # US Stock Transaction
                    tx['date'] = pd.to_datetime(row.get('約定日'), errors='coerce')
                    tx['symbol'] = str(row.get('ティッカー', ''))
                    tx['name'] = str(row.get('銘柄名', tx['symbol']))
                    tx['type'] = str(row.get('売買区分', ''))
                    tx['qty'] = parse_currency(str(row.get('数量［株］', 0)))

                    # Amount in JPY
                    amount_jpy_raw = row.get('受渡金額［円］')
                    if pd.notna(amount_jpy_raw) and str(amount_jpy_raw) not in ['-', '']:
                        tx['amount_jpy'] = parse_currency(str(amount_jpy_raw))
                    else:
                        usd = parse_currency(str(row.get('受渡金額［USドル］', 0)))
                        rate = parse_currency(str(row.get('為替レート', 0)))
                        tx['amount_jpy'] = abs(usd * rate)

                    tx['market'] = 'US'

                elif is_invst:
                    # Investment Trust Transaction
                    tx['date'] = pd.to_datetime(row.get('約定日'), errors='coerce')

                    raw_name = str(row.get('ファンド名', ''))
                    mapped_name = self.apply_name_mapping(raw_name)

                    tx['symbol'] = mapped_name
                    tx['name'] = mapped_name
                    tx['type'] = str(row.get('取引', row.get('取引区分', '')))

                    qty = parse_currency(str(row.get('数量［口］', 0)))
                    if is_unit_kuchi:
                        qty = qty / 10000  # Normalize to 万口 basis

                    tx['qty'] = qty
                    tx['amount_jpy'] = parse_currency(str(row.get('受渡金額/(ポイント利用)[円]', row.get('受渡金額［円］', 0))))
                    tx['market'] = 'INVST'

                elif is_jp:
                    # Japanese Stock Transaction
                    tx['date'] = pd.to_datetime(row.get('約定日'), errors='coerce')
                    tx['symbol'] = str(row.get('銘柄コード', ''))
                    tx['name'] = str(row.get('銘柄名', ''))
                    tx['type'] = str(row.get('売買区分', ''))
                    tx['qty'] = parse_currency(str(row.get('数量［株］', 0)))
                    tx['amount_jpy'] = parse_currency(str(row.get('受渡金額［円］', 0)))
                    tx['market'] = 'JP'

                # Validate required fields
                if pd.isna(tx.get('date')) or tx.get('amount_jpy', 0) <= 0:
                    continue

                # Determine side (BUY/SELL)
                tx_type = str(tx.get('type', '')).strip()
                if any(keyword in tx_type for keyword in ['買', '再投資', '積立']):
                    tx['side'] = 'BUY'
                elif any(keyword in tx_type for keyword in ['売', '解約']):
                    tx['side'] = 'SELL'
                else:
                    tx['side'] = 'OTHER'

                # Add asset classification (will be done in another service)
                tx['asset_class'] = None  # To be classified later

                transactions.append(tx)

            except Exception as e:
                # Skip problematic rows
                continue

        print(f"取引データ抽出: {len(transactions)}件")
        return transactions

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

        elif '約定日' in df_str and any(keyword in df_str for keyword in ['銘柄名', 'ティッカー', 'ファンド名']):
            # Transaction History File
            transactions = self.parse_transaction_history(df)
            return {
                'type': 'transactions',
                'data': transactions,
                'filename': filename
            }

        else:
            # Unknown file type
            return {
                'type': 'unknown',
                'data': [],
                'filename': filename
            }
