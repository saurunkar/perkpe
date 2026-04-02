import pytest
import json
import os
from src.agents.specialist_base import SpecialistAgent

@pytest.mark.asyncio
async def test_erv_calculation_match_mathematical_formula():
    """
    Test Case: Verify that ERV calculation matches our designated formula.
    Arrange-Act-Assert Pattern.
    """
    # 1. Arrange: Load real merchant data from JSON
    data_path = os.path.join(os.path.dirname(__file__), "data/merchants.json")
    with open(data_path, "r") as f:
        merchants = json.load(f)
    
    myntra_data = next(m for m in merchants if m["merchant"] == "Myntra")
    
    agent = SpecialistAgent(name="MyntraBot", category=myntra_data["category"])
    
    user_context = {
        "merchant": "Myntra",
        "card": "HDFC",
        "original_price": 5000,
        "base_discount": myntra_data["base_discount"], # 0.20
        "card_offer": myntra_data["card_offers"]["HDFC"] # 0.10
    }
    
    # 2. Act: Calculate bid
    erv = await agent.calculate_bid(user_context)
    
    # 3. Assert: Verify the ERV manually
    # Expected: (5000 * 0.20) + ((5000 - 1000) * 0.10)
    # Expected: 1000 + (4000 * 0.10) = 1400
    assert erv == 1400.0
    print(f"ERV Calculation Verified: {erv}")
