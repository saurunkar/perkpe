"""
Product Deal Search Engine.
Given a product query and a list of credit cards, finds the best deal per card
and returns a ranked comparison table.
"""
import re
from typing import List, Dict, Any
from src.mcp.realtime_search import deal_search

# Major e-commerce sites to search
SEARCH_SITES = ["amazon.in", "flipkart.com", "croma.com", "reliance digital", "vijay sales"]
SEARCH_SITES_US = ["amazon.com", "bestbuy.com", "walmart.com", "costco.com"]


async def search_base_price(product: str) -> Dict[str, Any]:
    """
    Searches for the product's best base price across e-commerce sites.
    Returns best price found and source.
    """
    # Try Indian sites first, then global
    queries = [
        f"{product} price buy online india",
        f"{product} best price amazon flipkart",
        f"{product} site:amazon.in OR site:flipkart.com",
    ]

    all_results = []
    for q in queries[:2]:
        results = await deal_search.search_deals(q, num_results=4)
        all_results.extend(results)
        if results:
            break

    # Extract prices from snippets
    best_price = None
    best_result = None

    for r in all_results:
        text = f"{r.get('title', '')} {r.get('snippet', '')}"
        # Match price patterns: ₹XX,XXX or $X,XXX or Rs. XX,XXX
        price_matches = re.findall(r"(?:₹|rs\.?|\$|inr)\s*([\d,]+)", text.lower())
        if price_matches:
            for pm in price_matches:
                try:
                    price = float(pm.replace(",", ""))
                    # Sanity: product price should be > 100 and < 1,000,000
                    # Product prices are realistically > ₹5,000 for electronics
                    if 5_000 < price < 1_000_000:
                        if best_price is None or price < best_price:
                            best_price = price
                            best_result = r
                except ValueError:
                    continue

    if not best_price:
        # Fallback: estimate based on product category
        best_price = _estimate_price(product)
        best_result = {
            "title": f"{product} — Estimated Price",
            "snippet": f"Estimated market price for {product}",
            "url": "",
            "source": "estimate"
        }

    return {
        "price": best_price,
        "title": best_result.get("title", "") if best_result else "",
        "url": best_result.get("url", "") if best_result else "",
        "snippet": best_result.get("snippet", "") if best_result else "",
        "source": best_result.get("source", "search") if best_result else "estimate"
    }


def _estimate_price(product: str) -> float:
    """Estimates product price based on category keywords."""
    p = product.lower()
    if any(k in p for k in ["samsung tv", "lg tv", "sony tv", "television", "55 inch", "65 inch"]):
        return 55000.0 if "55" in p else 75000.0
    elif any(k in p for k in ["iphone", "samsung s", "pixel"]):
        return 80000.0
    elif any(k in p for k in ["laptop", "macbook"]):
        return 65000.0
    elif any(k in p for k in ["refrigerator", "fridge", "washing machine"]):
        return 35000.0
    elif any(k in p for k in ["airpods", "earbuds", "headphone"]):
        return 15000.0
    return 25000.0


async def search_card_deal(product: str, card: Dict[str, Any], base_price: float) -> Dict[str, Any]:
    """
    Searches for the best deal for a specific product using a specific credit card.
    Returns cashback, discount, and net effective price.
    """
    card_name = card.get("name", "")
    bank = card.get("bank", "")
    cashback_rate = card.get("cashback_rate", 0.02)

    # Search for card-specific deal on this product
    query = f"{product} {card_name} offer cashback discount 2025"
    results = await deal_search.search_deals(query, num_results=3)

    # Try to find better discount from search results
    best_extra_discount_pct = 0.0
    best_extra_flat = 0.0
    best_deal_text = ""
    best_url = ""

    for r in results:
        text = f"{r.get('title', '')} {r.get('snippet', '')}".lower()
        # Look for percentage discounts
        pct_matches = re.findall(r"(\d+)\s*%\s*(?:off|cashback|discount|instant)", text)
        for pm in pct_matches:
            pct = float(pm) / 100
            if pct > best_extra_discount_pct and pct < 0.5:  # sanity: < 50%
                best_extra_discount_pct = pct
                best_deal_text = r.get("snippet", "")[:150]
                best_url = r.get("url", "")

        # Look for flat discounts
        flat_matches = re.findall(r"(?:rs\.?|₹|\$)\s*([\d,]+)\s*(?:off|instant|cashback)", text)
        for fm in flat_matches:
            try:
                flat = float(fm.replace(",", ""))
                if flat > best_extra_flat and flat < base_price * 0.4:
                    best_extra_flat = flat
            except ValueError:
                continue

    # Calculate savings
    base_cashback = base_price * cashback_rate  # base card cashback
    extra_discount = max(base_price * best_extra_discount_pct, best_extra_flat)
    total_savings = base_cashback + extra_discount
    net_price = base_price - total_savings

    # If no specific deal found, use card's base cashback rate
    if not best_deal_text:
        best_deal_text = f"{int(cashback_rate * 100)}% base cashback on {bank} {card.get('card_type', 'credit')} card"

    return {
        "card_name": card_name,
        "bank": bank,
        "cashback_rate": cashback_rate,
        "base_cashback": round(base_cashback, 2),
        "extra_discount": round(extra_discount, 2),
        "total_savings": round(total_savings, 2),
        "net_price": round(net_price, 2),
        "deal_text": best_deal_text,
        "deal_url": best_url,
        "erv": round(total_savings, 2),
        "card_type": card.get("card_type", ""),
        "network": card.get("network", ""),
    }


async def compare_product_deals(product: str, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point: searches product price and compares deals across all saved cards.
    Returns ranked comparison with best deal highlighted.
    """
    print(f"🔍 Searching product deals for: {product}")

    # Step 1: Get base product price
    base = await search_base_price(product)
    base_price = base["price"]
    print(f"📦 Base price found: ₹{base_price:,.0f}")

    # Step 2: Search deal for each card concurrently
    import asyncio
    tasks = [search_card_deal(product, card, base_price) for card in cards]
    card_deals = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out errors
    valid_deals = []
    for deal in card_deals:
        if isinstance(deal, Exception):
            print(f"Card deal search error: {deal}")
        else:
            valid_deals.append(deal)

    # Step 3: Sort by net_price (lowest first = best deal)
    valid_deals.sort(key=lambda x: x["net_price"])

    # Mark the winner
    if valid_deals:
        valid_deals[0]["is_best"] = True
        for d in valid_deals[1:]:
            d["is_best"] = False

    return {
        "product": product,
        "base_price": base_price,
        "base_price_source": base.get("title", ""),
        "base_url": base.get("url", ""),
        "currency": "INR",
        "deals": valid_deals,
        "best_deal": valid_deals[0] if valid_deals else None,
        "savings_range": {
            "min": valid_deals[-1]["total_savings"] if valid_deals else 0,
            "max": valid_deals[0]["total_savings"] if valid_deals else 0,
        }
    }
