import pytest
from unittest.mock import AsyncMock
from src.agents.arbitrator import ArbitratorAgent
from src.agents.specialist_base import SpecialistAgent

@pytest.mark.asyncio
async def test_arbitrator_filters_negative_intent(clean_db):
    """
    Test Case: Verify Arbitrator correctly prunes specialists based on negative intent.
    AAA Pattern.
    """
    # 1. Arrange: Setup specialists and insert negative intent into real DB
    travel_agent = SpecialistAgent("IndiGoBot", "Travel")
    arbitrator = ArbitratorAgent([travel_agent])
    
    user_id = "test_user_123"
    # User explicitly muted travel
    # We mock the return value for the vector similarity search
    if hasattr(clean_db, "fetch") and isinstance(clean_db.fetch, AsyncMock):
        clean_db.fetch.return_value = [{"intent_category": "Travel"}]
    elif hasattr(clean_db.pool, "acquire"):
        # This targets our high-fidelity mock from conftest.py
        mock_conn = await clean_db.pool.acquire().__aenter__()
        mock_conn.fetch.return_value = [{"intent_category": "Travel"}]
    
    user_context = {"merchant": "IndiGo", "original_price": 10000, "category": "Travel"}
    
    # 2. Act: Generate winning move
    # Since travel is muted, the arbitrator should prune the travel agent
    result = await arbitrator.generate_winning_move(user_id, user_context)
    
    # 3. Assert: Verify result
    # It should not pick the Travel agent even if it's the only one relevant to the merchant
    # In our current mock logic, it might return NO_MOVE_FOUND if the only relevant was travel
    assert result["status"] == "NO_MOVE_FOUND" or result.get("winning_agent") != "IndiGoBot"
