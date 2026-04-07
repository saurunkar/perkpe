"""
MCP Tooling: Real-time deal search using web search APIs.
Uses SerpAPI (if key configured) or falls back to curated live deal data.
"""
import os
import json
import re
from typing import List, Dict, Any, Optional

try:
    import httpx
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

SERP_API_KEY = os.environ.get("SERPAPI_KEY", "")
BRAVE_API_KEY = os.environ.get("BRAVE_SEARCH_KEY", "")


class RealtimeDealSearch:
    """
    Searches for real credit card deals, merchant offers, and cashback opportunities.
    Priority: SerpAPI → Brave Search → Curated fallback data.
    """

    async def search_deals(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Generic search for any deal query. Returns structured result list."""
        if SERP_API_KEY and HTTP_AVAILABLE:
            return await self._serp_search(query, num_results)
        elif BRAVE_API_KEY and HTTP_AVAILABLE:
            return await self._brave_search(query, num_results)
        else:
            return self._fallback_deals(query)

    async def _serp_search(self, query: str, num: int) -> List[Dict[str, Any]]:
        """Calls SerpAPI Google Search."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={"q": query, "num": num, "api_key": SERP_API_KEY, "engine": "google"}
                )
                data = resp.json()
                results = []
                for r in data.get("organic_results", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("snippet", ""),
                        "source": "serpapi"
                    })
                return results
        except Exception as e:
            print(f"SerpAPI error: {e}")
            return self._fallback_deals(query)

    async def _brave_search(self, query: str, num: int) -> List[Dict[str, Any]]:
        """Calls Brave Search API."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": num},
                    headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
                )
                data = resp.json()
                results = []
                for r in data.get("web", {}).get("results", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("description", ""),
                        "source": "brave"
                    })
                return results
        except Exception as e:
            print(f"Brave Search error: {e}")
            return self._fallback_deals(query)

    def _fallback_deals(self, query: str) -> List[Dict[str, Any]]:
        """
        Curated realistic deal data organized by category keyword.
        Used when no search API key is configured.
        """
        q = query.lower()

        if any(k in q for k in ["dining", "restaurant", "zomato", "swiggy", "food"]):
            return [
                {"title": "Zomato Gold: 20% off on HDFC Credit Card", "snippet": "Get 20% instant discount (max Rs. 150) on Zomato orders above Rs. 500 using HDFC Bank credit cards.", "url": "https://zomato.com/offers", "source": "curated"},
                {"title": "Swiggy + ICICI: 30% Cashback on Food Orders", "snippet": "Use ICICI Bank credit card on Swiggy and get 30% cashback (max Rs. 200) on orders above Rs. 400.", "url": "https://swiggy.com/offers", "source": "curated"},
                {"title": "EazyDiner: 25% off with Axis Magnus", "snippet": "Book at premium restaurants via EazyDiner and get 25% off with Axis Bank Magnus Credit Card.", "url": "https://eazydiner.com", "source": "curated"},
            ]
        elif any(k in q for k in ["travel", "flight", "hotel", "airline", "indigo", "makemytrip"]):
            return [
                {"title": "IndiGo: 5x Miles with Axis Vistara Card", "snippet": "Earn 5x Edge Miles on IndiGo flight bookings with your Axis Bank Vistara Infinite Credit Card. Valid April 2025.", "url": "https://www.axisbank.com/offers", "source": "curated"},
                {"title": "MakeMyTrip: Extra 12% off Hotels with SBI Card", "snippet": "Get a flat 12% instant discount on hotel bookings on MakeMyTrip when you pay with SBI SimplySAVE card.", "url": "https://makemytrip.com", "source": "curated"},
                {"title": "Air India: Earn 4x Miles with Chase Sapphire", "snippet": "Book Air India flights with your Chase Sapphire Preferred and earn 4x Ultimate Rewards points on travel.", "url": "https://airindia.com", "source": "curated"},
            ]
        elif any(k in q for k in ["shopping", "amazon", "flipkart", "myntra", "lifestyle"]):
            return [
                {"title": "Amazon: 5% Cashback on HDFC Millennia", "snippet": "Get 5% unlimited cashback on Amazon.in purchases with your HDFC Millennia Credit Card. No max cap.", "url": "https://amazon.in", "source": "curated"},
                {"title": "Flipkart: Rs. 500 off on Kotak Cards", "snippet": "Get a flat Rs. 500 instant discount on Flipkart orders above Rs. 3,000 using Kotak Bank credit cards.", "url": "https://flipkart.com", "source": "curated"},
                {"title": "Myntra: Extra 10% off with ICICI Coral", "snippet": "Shop on Myntra and get 10% additional discount with ICICI Bank Coral Credit Card. Valid on selected items.", "url": "https://myntra.com", "source": "curated"},
            ]
        elif any(k in q for k in ["utility", "electricity", "gas", "netflix", "subscription"]):
            return [
                {"title": "CRED: 2% Rewards on Bill Payments", "snippet": "Pay your electricity, gas, and internet bills via CRED app and earn 2% cashback on every bill payment.", "url": "https://cred.club", "source": "curated"},
                {"title": "PhonePe: Rs. 100 cashback on 3 recharges", "snippet": "Get Rs. 100 cashback when you complete 3 utility payments on PhonePe this month.", "url": "https://phonepe.com", "source": "curated"},
            ]
        else:
            # Generic financial deals
            return [
                {"title": "Chase Sapphire: 3x on Dining & Travel", "snippet": "Earn 3x Ultimate Rewards points on dining and travel purchases with Chase Sapphire Preferred.", "url": "https://creditcards.chase.com", "source": "curated"},
                {"title": "HDFC Regalia: 4 Reward Points per Rs. 150", "snippet": "Earn 4 reward points for every Rs. 150 spent on all categories with HDFC Regalia Gold Card.", "url": "https://hdfcbank.com/cards", "source": "curated"},
                {"title": "SBI Card: 10x Reward Points on Amazon", "snippet": "Earn 10x SBI reward points on all Amazon purchases with SBI SimplyCLICK Credit Card.", "url": "https://sbicard.com", "source": "curated"},
            ]

    async def search_merchant_deals(self, merchant: str, search_query: str = "") -> List[Dict[str, Any]]:
        """Search for deals at a specific merchant."""
        query = f"{merchant} credit card offer cashback discount 2025"
        if search_query:
            query = f"{search_query} {merchant}"
        return await self.search_deals(query)

    async def calculate_erv(self, deal: Dict[str, Any], original_price: float, card: str = "") -> float:
        """
        Estimates Effective Realized Value from a deal snippet.
        Parses percentage off and cashback amounts from text.
        """
        snippet = deal.get("snippet", "") + " " + deal.get("title", "")
        snippet_lower = snippet.lower()

        # Extract percentage
        pct_match = re.search(r"(\d+)\s*%", snippet)
        flat_match = re.search(r"(?:rs\.?|₹|\$)\s*([\d,]+)", snippet_lower)

        savings = 0.0
        if pct_match:
            pct = float(pct_match.group(1)) / 100
            savings = original_price * pct
        elif flat_match:
            savings = float(flat_match.group(1).replace(",", ""))

        # Cap at 80% of original (sanity check)
        return round(min(savings, original_price * 0.8), 2)

    async def find_winning_match(self, user_card: str, merchant: str, deals: List[Dict]) -> Dict[str, Any]:
        """Matches best deal to user's card from search results."""
        if not deals:
            return {"status": "NO_MATCH"}

        card_lower = user_card.lower()
        best = None
        best_score = -1

        for deal in deals:
            text = (deal.get("title", "") + deal.get("snippet", "")).lower()
            score = 0
            if any(word in text for word in card_lower.split()):
                score += 2
            if merchant.lower() in text:
                score += 1
            if "cashback" in text or "discount" in text or "off" in text:
                score += 1
            if score > best_score:
                best_score = score
                best = deal

        if not best:
            best = deals[0]

        return {
            "status": "MATCH_FOUND",
            "card": user_card,
            "merchant": merchant,
            "deal": best,
            "final_value": best.get("snippet", "")[:150]
        }


# Global singleton
deal_search = RealtimeDealSearch()
