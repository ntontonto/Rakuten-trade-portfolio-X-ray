"""
Balance Data Merger Service

Merges asset balance data from CSV with existing holdings
Updates current prices and quantities

Ported from JavaScript (index.html lines 765-823)
"""
from typing import List, Dict
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Holding
from app.utils.currency import normalize_japanese_text


class BalanceMerger:
    """Merges balance CSV data with existing holdings"""

    def __init__(self, db: Session):
        self.db = db

    def merge_balance_data(
        self,
        portfolio_id: str,
        balance_data: List[Dict],
        exchange_rates: Dict[str, float]
    ) -> Dict[str, int]:
        """
        Merge balance data with existing holdings

        Args:
            portfolio_id: Portfolio UUID
            balance_data: List of balance items from CSV
            exchange_rates: Exchange rate dictionary (e.g., {"USD": 150.25})

        Returns:
            Dict with merge statistics
        """
        if not balance_data:
            return {
                'total_items': 0,
                'matched': 0,
                'unmatched': 0
            }

        # Fetch all holdings for this portfolio
        holdings = (
            self.db.query(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .all()
        )

        # Aggregate balance data by symbol/name
        # Multiple rows for same asset are summed
        balance_map = {}
        for item in balance_data:
            # Create key from code or name
            code = item.get('code')
            name = item.get('name')

            key = normalize_japanese_text(code) if code else normalize_japanese_text(name)
            if not key:
                key = normalize_japanese_text(name) if name else None

            if not key:
                continue

            if key not in balance_map:
                balance_map[key] = {
                    'value': Decimal('0'),
                    'qty': Decimal('0'),
                    'name': name,
                    'count': 0
                }

            balance_map[key]['value'] += Decimal(str(item.get('value', 0)))
            balance_map[key]['qty'] += Decimal(str(item.get('qty', 0)))
            balance_map[key]['count'] += 1

        # Match holdings with balance data
        match_count = 0
        unmatch_count = 0

        for holding in holdings:
            # Try matching by code first, then by name
            h_code = normalize_japanese_text(holding.symbol)
            h_name = normalize_japanese_text(holding.name)

            matched_item = None
            if h_code and h_code in balance_map:
                matched_item = balance_map[h_code]
            elif h_name and h_name in balance_map:
                matched_item = balance_map[h_name]

            if matched_item and matched_item['qty'] > 0:
                # Calculate implied price from aggregated data
                implied_price = matched_item['value'] / matched_item['qty']

                # Update holding
                holding.current_value = matched_item['value']
                holding.quantity = matched_item['qty']  # Overwrite qty to match balance reality
                holding.current_price = implied_price
                holding.is_price_auto_updated = True

                match_count += 1
                print(
                    f"[Balance Merge] {holding.name}: "
                    f"Price ¥{int(implied_price):,} "
                    f"(Value ¥{int(matched_item['value']):,} / Qty {matched_item['qty']} / "
                    f"{matched_item['count']} rows aggregated)"
                )
            else:
                unmatch_count += 1
                print(f"[Balance Merge] Unmatched: {holding.name}")

        # Commit changes
        self.db.commit()

        return {
            'total_items': len(balance_data),
            'matched': match_count,
            'unmatched': unmatch_count,
            'exchange_rates': exchange_rates
        }

    def apply_exchange_rate(self, portfolio_id: str, currency: str, rate: float):
        """
        Apply exchange rate to foreign currency holdings

        Args:
            portfolio_id: Portfolio UUID
            currency: Currency code (e.g., "USD")
            rate: Exchange rate to JPY
        """
        # This would be used if we need to convert USD prices to JPY
        # For now, we assume all prices are already in JPY from the CSV
        pass
