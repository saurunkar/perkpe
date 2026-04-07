"""
Travel Specialist Agent.
Searches for flights, hotels, and lounge access deals. Calculates ERV from reward points and cashback.
"""
from typing import Dict, Any
from src.agents.specialist_base import SpecialistAgent
from src.mcp.realtime_search import deal_search


class TravelSpecialist(SpecialistAgent):
    def __init__(self):
        super().__init__(name="TravelSpecialist", category="travel")

    async def calculate_bid(self, user_context: Dict[str, Any]) -> float:
        """
        Calculates ERV for travel-related card offers: airline miles, hotel cashback, lounge access.
        """
        card = user_context.get("card", "")
        budget = user_context.get("travel_budget", 20000)
        best_erv = 0.0

        query = f"{card} travel flight hotel cashback offer miles 2025"
        deals = await deal_search.search_deals(query, num_results=5)

        for deal in deals:
            erv = await deal_search.calculate_erv(deal, original_price=budget)
            if erv > best_erv:
                best_erv = erv

        # Lounge access value (if card supports it)
        lounge_value = 0.0
        if any(kw in card.lower() for kw in ["sapphire", "regalia", "vistara", "magnus", "infinite"]):
            lounge_value = 800  # ~Rs. 800 per lounge visit equivalent

        total_erv = best_erv + lounge_value
        self._last_details = {
            "category": "travel",
            "cashback_erv": best_erv,
            "lounge_value": lounge_value,
            "total_erv": total_erv
        }
        return round(total_erv, 2)

    def get_details(self) -> Dict[str, Any]:
        return getattr(self, "_last_details", {})
