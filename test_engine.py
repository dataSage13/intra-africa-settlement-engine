import pytest
from router import process_settlement_request
from database import get_db_connection

def test_successful_settlement():
    """Verify that a standard trade request clears when liquidity is safe."""
    # NGN to ZAR should pass easily with low amounts
    result = process_settlement_request("NGN", "ZAR", 1000)
    assert result["status"] == "SETTLED"
    assert "routing_path" in result
    assert result["final_payout_amount"] > 0

def test_liquidity_shortfall_failure():
    """Verify that the engine actively blocks transactions that exceed central bank pools."""
    # An incredibly massive amount of NGN to GHS should trigger our safety block
    result = process_settlement_request("NGN", "GHS", 999_999_999)
    assert result["status"] == "FAILED_LIQUIDITY"
    assert "reason" in result
    assert "Liquidity shortfall" in result["reason"]

def test_invalid_currency_route():
    """Verify that the engine safely handles currencies that don't exist in our matrix."""
    # 'XYZ' is an invalid currency code and should return no route
    result = process_settlement_request("NGN", "XYZ", 500)
    assert result["status"] == "FAILED_NO_ROUTE"
