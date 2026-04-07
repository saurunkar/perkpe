"""
Utility Specialist Agent.
Scans Gmail for recurring subscriptions, detects duplicates, and suggests bill-pay cashback.
"""
from typing import Dict, Any, List
from src.agents.specialist_base import SpecialistAgent
from src.mcp.gmail_parser import gmail_parser
from src.mcp.realtime_search import deal_search


KNOWN_DUPLICATE_SERVICES = [
    {"names": ["netflix", "prime video", "disney+", "hotstar"], "label": "Streaming"},
    {"names": ["spotify", "apple music", "youtube music", "gaana"], "label": "Music"},
    {"names": ["google one", "icloud", "dropbox", "onedrive"], "label": "Cloud Storage"},
]


class UtilitySpecialist(SpecialistAgent):
    def __init__(self):
        super().__init__(name="UtilitySpecialist", category="utility")

    async def calculate_bid(self, user_context: Dict[str, Any]) -> float:
        """
        Finds subscription savings and utility cashback ERV.
        1. Parses Gmail for active subscriptions
        2. Detects duplicate/overlapping services
        3. Finds bill payment cashback offers
        """
        # 1. Parse Gmail for subscriptions
        parsed_emails = await gmail_parser.parse_inbox()
        subscriptions = [e for e in parsed_emails if e.get("type") == "SUBSCRIPTION"]

        # 2. Detect duplicates/waste
        duplicate_savings = self._find_duplicate_waste(subscriptions)

        # 3. Bill-pay cashback
        card = user_context.get("card", "")
        query = f"{card} utility electricity bill payment cashback offer"
        bill_deals = await deal_search.search_deals(query, num_results=3)
        bill_erv = 0.0
        total_bills = user_context.get("monthly_bills", 3000)
        for deal in bill_deals:
            erv = await deal_search.calculate_erv(deal, original_price=total_bills)
            if erv > bill_erv:
                bill_erv = erv

        total_erv = duplicate_savings + bill_erv
        self._last_details = {
            "category": "utility",
            "active_subscriptions": len(subscriptions),
            "duplicate_savings": duplicate_savings,
            "bill_cashback_erv": bill_erv,
            "total_erv": total_erv,
            "subscriptions_found": [s.get("merchant", s.get("offer_detail", "Unknown")) for s in subscriptions[:5]]
        }
        return round(total_erv, 2)

    def _find_duplicate_waste(self, subscriptions: List[Dict]) -> float:
        """Identifies overlapping subscriptions and estimates monthly savings."""
        found_services = []
        for sub in subscriptions:
            merchant = (sub.get("merchant") or sub.get("offer_detail") or "").lower()
            for group in KNOWN_DUPLICATE_SERVICES:
                for name in group["names"]:
                    if name in merchant:
                        found_services.append((group["label"], name, sub.get("amount", 0) or 0))
                        break

        # Check for duplicates in same category
        savings = 0.0
        seen_labels = {}
        for label, name, amount in found_services:
            if label in seen_labels:
                # Duplicate found — suggest cancelling cheaper one
                savings += min(amount, seen_labels[label])
            seen_labels[label] = amount

        return round(savings, 2)

    def get_details(self) -> Dict[str, Any]:
        return getattr(self, "_last_details", {})
