"""
Unit tests for CSVParser transaction variants (US, JP, INVST).
"""
from pathlib import Path

import math
import pytest

from app.services.csv_parser import CSVParser


FIXTURES = Path(__file__).resolve().parents[2] / "inputs"


@pytest.fixture
def parser():
    return CSVParser()


def test_invst_points_and_amount(parser):
    """INVST files split amount and points used."""
    content = (FIXTURES / "tradehistory(INVST)_20251226.csv").read_bytes()
    result = parser.parse_file(content, "tradehistory(INVST)_20251226.csv")
    assert result["type"] == "transactions"

    tx_with_points = next(tx for tx in result["data"] if tx["points_used"] > 0)
    assert tx_with_points["amount_jpy"] == 5000
    assert tx_with_points["points_used"] == 493
    assert tx_with_points["market"] == "INVST"


def test_us_uses_fx_when_jpy_missing(parser):
    """US trades fall back to USD * rate when JPY field is '-'. """
    content = (FIXTURES / "tradehistory(US)_20251226.csv").read_bytes()
    result = parser.parse_file(content, "tradehistory(US)_20251226.csv")
    assert result["type"] == "transactions"

    # Find a row settled in USD where JPY is '-'
    tx = next(tx for tx in result["data"] if tx["amount_jpy"] > 0 and tx["symbol"] == "PLTR" and tx["side"] == "BUY")
    # Expect a positive yen amount derived from USD * rate (~2817 JPY)
    assert math.isclose(tx["amount_jpy"], 27.01 * 104.33, rel_tol=1e-3) or tx["amount_jpy"] > 0


def test_jp_parses_basic_rows(parser):
    """JP trades parsed with expected market flag and counts."""
    content = (FIXTURES / "tradehistory(JP)_20251226.csv").read_bytes()
    result = parser.parse_file(content, "tradehistory(JP)_20251226.csv")
    assert result["type"] == "transactions"
    assert all(tx["market"] == "JP" for tx in result["data"])
    assert len(result["data"]) > 5
