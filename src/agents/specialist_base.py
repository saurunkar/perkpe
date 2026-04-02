import json
import os
from typing import Dict, Any
from src.agents.arbitrator import AgentProtocol

class SpecialistAgent(AgentProtocol):
    def __init__(self, name: str, category: str):
        super().__init__(name, category)
        
    async def calculate_bid(self, user_context: Dict[str, Any]) -> float:
        """
        Calculates the Effective Realized Value (ERV).
        Formula: (Original Price * Base Discount) + (Remaining Price * Card Offer)
        """
        merchant = user_context.get("merchant")
        card = user_context.get("card")
        original_price = user_context.get("original_price", 0)
        base_discount = user_context.get("base_discount", 0)
        card_offer = user_context.get("card_offer", 0) # Percentage e.g., 0.10 for 10%
        
        # 1. Direct Merchant Savings
        merchant_savings = original_price * base_discount
        
        # 2. Additional Card Savings on the discounted price
        remaining_price = original_price - merchant_savings
        card_savings = remaining_price * card_offer
        
        # Total ERV
        erv = merchant_savings + card_savings
        return round(float(erv), 2)
