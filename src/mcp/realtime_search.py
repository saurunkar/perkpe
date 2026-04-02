"""
MCP Tooling for real-time merchant deal fetching.
Simulates searching for deals on specific retailers to match with credit card offers.
"""
from typing import List, Dict, Any

class RealtimeDealSearch:
    def __init__(self):
        # We define common credit card offers the agent "knows" about
        self.card_offers = {
            "HDFC": {
                "Myntra": "10% Instant Discount on HDFC Bank Credit Cards",
                "Amazon": "5% Unlimited Cashback on HDFC Millennia",
                "Flipkart": "Flat $50 off on HDFC Cards"
            }
        }

    async def search_merchant_deals(self, merchant: str, search_query: str) -> List[Dict[str, Any]]:
        """
        Simulates fetching real-time deals for a merchant based on a query.
        """
        # Mocking the search results on Myntra
        if merchant.lower() == "myntra":
            return [
                {"product": "Nike Air Max", "price": 4999, "discount": "20% Off"},
                {"product": "Levis 501 Jeans", "price": 2999, "discount": "Flat 30% Off"},
                {"product": "Samsung Galaxy Watch", "price": 14999, "discount": "Bank Offer Available"}
            ]
        return []

    async def find_winning_match(self, user_card: str, merchant: str, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Matches merchant deals with known credit card offers.
        """
        offer = self.card_offers.get(user_card, {}).get(merchant)
        
        if not offer or not deals:
            return {"status": "NO_MATCH"}
            
        winning_deal = deals[0] # Simply picking the first deal for the match demo
        
        return {
            "status": "MATCH_FOUND",
            "card": user_card,
            "merchant": merchant,
            "card_offer": offer,
            "deal": winning_deal,
            "final_value": f"Savings of 10% on top of {winning_deal['discount']}"
        }

# Global instance for MCP Tooling
deal_search = RealtimeDealSearch()
