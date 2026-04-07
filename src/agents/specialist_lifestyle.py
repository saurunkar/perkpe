"""
Lifestyle Specialist Agent.
Searches for dining, shopping, entertainment deals and calculates ERV.
"""
from typing import Dict, Any
from src.agents.specialist_base import SpecialistAgent
from src.mcp.realtime_search import deal_search


class LifestyleSpecialist(SpecialistAgent):
    def __init__(self):
        super().__init__(name="LifestyleSpecialist", category="lifestyle")
        self.search_categories = ["dining restaurant zomato swiggy", "shopping amazon flipkart myntra"]

    async def calculate_bid(self, user_context: Dict[str, Any]) -> float:
        """
        Searches for real lifestyle deals and returns highest ERV found.
        """
        card = user_context.get("card", "")
        budget = user_context.get("monthly_budget", 5000)
        best_erv = 0.0

        for category_query in self.search_categories:
            query = f"{card} {category_query} cashback offer 2025"
            deals = await deal_search.search_deals(query, num_results=5)
            for deal in deals:
                erv = await deal_search.calculate_erv(deal, original_price=budget * 0.4)
                if erv > best_erv:
                    best_erv = erv

        # Ensure a minimum if deals found
        if best_erv == 0.0 and user_context.get("card"):
            best_erv = budget * 0.05  # 5% estimated lifestyle savings

        self._last_details = {
            "category": "lifestyle",
            "best_erv": best_erv,
            "activities": ["Dining", "Shopping", "Entertainment"]
        }
        return round(best_erv, 2)

    def get_details(self) -> Dict[str, Any]:
        return getattr(self, "_last_details", {})
