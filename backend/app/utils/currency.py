"""
Currency and Number Parsing Utilities

Handles Japanese number formats and currency parsing
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


def parse_currency(value: str) -> float:
    """
    Parse currency values from Japanese CSV format

    Handles:
    - Comma separators: "1,000,000" -> 1000000
    - Parentheses with points: "5,000(493)" -> 5000
    - Negative values: "-1,000" -> -1000
    - Empty/None values -> 0

    Args:
        value: String value from CSV

    Returns:
        Float value

    Examples:
        >>> parse_currency("1,000,000")
        1000000.0
        >>> parse_currency("5,000(493)")
        5000.0
        >>> parse_currency("-1,234.56")
        -1234.56
    """
    if not value or value == '-' or value == '':
        return 0.0

    # Convert to string if not already
    value_str = str(value)

    # Remove parentheses and content (Points notation: "5,000(493)" -> "5,000")
    value_str = re.split(r'[(\(]', value_str)[0]
    value_str = re.split(r'[（]', value_str)[0]

    # Remove all non-numeric characters except minus and decimal point
    cleaned = re.sub(r'[^-0-9.]', '', value_str)

    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def clean_number(value: str) -> float:
    """Alias for parse_currency for backward compatibility"""
    return parse_currency(value)


def normalize_japanese_text(text: str) -> str:
    """
    Normalize Japanese text for matching

    Converts:
    - Full-width alphanumeric to half-width
    - Removes whitespace
    - Converts to lowercase

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ''

    # Convert full-width alphanumeric to half-width
    # Full-width A-Z (Ａ-Ｚ): 0xFF21-0xFF3A -> 0x0041-0x005A (subtract 0xFEE0)
    # Full-width a-z (ａ-ｚ): 0xFF41-0xFF5A -> 0x0061-0x007A (subtract 0xFEE0)
    # Full-width 0-9 (０-９): 0xFF10-0xFF19 -> 0x0030-0x0039 (subtract 0xFEE0)
    normalized = ''
    for char in text:
        code = ord(char)
        if 0xFF10 <= code <= 0xFF19:  # Full-width digits
            normalized += chr(code - 0xFEE0)
        elif 0xFF21 <= code <= 0xFF3A:  # Full-width uppercase
            normalized += chr(code - 0xFEE0)
        elif 0xFF41 <= code <= 0xFF5A:  # Full-width lowercase
            normalized += chr(code - 0xFEE0)
        else:
            normalized += char

    # Remove whitespace and convert to lowercase
    return normalized.replace(' ', '').replace('\u3000', '').lower()


def format_currency_jpy(amount: float, include_symbol: bool = True) -> str:
    """
    Format amount as Japanese Yen currency

    Args:
        amount: Numeric amount
        include_symbol: Whether to include ¥ symbol

    Returns:
        Formatted string

    Examples:
        >>> format_currency_jpy(1234567)
        '¥1,234,567'
        >>> format_currency_jpy(1234567, False)
        '1,234,567'
    """
    formatted = f"{int(amount):,}"
    return f"¥{formatted}" if include_symbol else formatted
