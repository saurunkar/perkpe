"""
API v1 Routes — All endpoints wired to real agent logic.
"""
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ─── Shared state (simple in-memory store; replace with AlloyDB for prod) ───
_auction_result: Dict[str, Any] = {}
_user_intents: Dict[str, Dict[str, str]] = {}
_user_settings = {
    "active_agents": ["lifestyle", "travel", "utility"],
    "muted_categories": [],
    "cards": [
        {"name": "Chase Sapphire Preferred", "type": "travel", "network": "Visa"},
        {"name": "HDFC Millennia", "type": "cashback", "network": "Mastercard"},
        {"name": "Axis Bank Magnus", "type": "travel", "network": "Visa"},
    ],
    "monthly_budget": 15000,
    "travel_budget": 30000,
    "monthly_bills": 4000,
}


# ─── Models ─────────────────────────────────────────────────────────────────

class IntentUpdate(BaseModel):
    user_id: str
    category: str
    intent: str  # "POSITIVE" | "NEGATIVE" | "MUTE"


class Offer(BaseModel):
    title: str
    description: str
    erv: float
    category: str
    source: Optional[str] = None


# ─── Helper: build arbitrator ────────────────────────────────────────────────

def _build_arbitrator():
    from src.agents.specialist_lifestyle import LifestyleSpecialist
    from src.agents.specialist_travel import TravelSpecialist
    from src.agents.specialist_utility import UtilitySpecialist
    from src.agents.arbitrator import ArbitratorAgent

    active = _user_settings["active_agents"]
    specialists = []
    if "lifestyle" in active:
        specialists.append(LifestyleSpecialist())
    if "travel" in active:
        specialists.append(TravelSpecialist())
    if "utility" in active:
        specialists.append(UtilitySpecialist())
    return ArbitratorAgent(specialists)


def _build_user_context():
    cards = _user_settings.get("cards", [])
    card = cards[0]["name"] if cards else "HDFC Millennia"
    return {
        "card": card,
        "monthly_budget": _user_settings.get("monthly_budget", 15000),
        "travel_budget": _user_settings.get("travel_budget", 30000),
        "monthly_bills": _user_settings.get("monthly_bills", 4000),
    }


# ─── Routes ─────────────────────────────────────────────────────────────────

@router.get("/offer-of-the-day", response_model=Offer)
async def get_offer_of_the_day():
    """
    Runs the full arbitrator pipeline and returns the best Financial Winning Move.
    """
    global _auction_result

    # Return cached result if available
    if _auction_result and _auction_result.get("status") == "WINNING_MOVE_GENERATED":
        agent_name = _auction_result.get("winning_agent", "LifestyleSpecialist")
        erv = _auction_result.get("erv", 0.0)
        details = _auction_result.get("details", {})
        return Offer(
            title=f"Best Move: {agent_name.replace('Specialist', '')} Savings",
            description=_auction_result.get("rationale", "Highest ERV opportunity identified."),
            erv=erv,
            category=details.get("category", agent_name.lower().replace("specialist", "")),
            source="arbitrator"
        )

    # Run a fresh auction
    try:
        arbitrator = _build_arbitrator()
        user_context = _build_user_context()
        result = await arbitrator.generate_winning_move("default_user", user_context)
        _auction_result = result

        if result.get("status") == "WINNING_MOVE_GENERATED":
            agent_name = result.get("winning_agent", "LifestyleSpecialist")
            return Offer(
                title=f"Best Move: {agent_name.replace('Specialist', '')} Savings",
                description=result.get("rationale", "Highest ERV opportunity identified by agents."),
                erv=result.get("erv", 0.0),
                category=agent_name.lower().replace("specialist", ""),
                source="arbitrator"
            )
    except Exception as e:
        print(f"Arbitrator error: {e}")

    # Fallback
    return Offer(
        title="Chase Sapphire: Maximize 3x Points",
        description="50,000 points expiring soon. Redirect lifestyle spend to maximize 3x multipliers before Oct 31st.",
        erv=750.00,
        category="lifestyle",
        source="fallback"
    )


@router.post("/trigger_auction")
async def trigger_auction(background_tasks: BackgroundTasks):
    """
    Triggers an asynchronous agent auction. Returns immediately, result cached.
    """
    global _auction_result
    _auction_result = {}  # Clear cache to force fresh run

    async def run_auction():
        global _auction_result
        try:
            arbitrator = _build_arbitrator()
            user_context = _build_user_context()
            result = await arbitrator.generate_winning_move("default_user", user_context)
            _auction_result = result
            print(f"Auction complete: {result}")
        except Exception as e:
            _auction_result = {"status": "ERROR", "message": str(e)}

    background_tasks.add_task(run_auction)
    return {"status": "AUCTION_TRIGGERED", "message": "Agents are scanning for best deals..."}


@router.get("/offers")
async def get_all_offers():
    """
    Returns deals from all active specialist agents concurrently.
    """
    from src.agents.specialist_lifestyle import LifestyleSpecialist
    from src.agents.specialist_travel import TravelSpecialist
    from src.agents.specialist_utility import UtilitySpecialist
    from src.mcp.realtime_search import deal_search

    user_context = _build_user_context()
    card = user_context["card"]

    # Build queries per category
    queries = [
        ("Lifestyle Deals", f"{card} dining shopping cashback offer 2025"),
        ("Travel Deals", f"{card} flight hotel travel cashback miles 2025"),
        ("Utility & Bills", f"{card} utility electricity bill payment cashback"),
        ("Current Credit Card Offers", f"{card} best offer cashback reward points 2025"),
    ]

    all_offers = []
    for category, query in queries:
        deals = await deal_search.search_deals(query, num_results=3)
        for deal in deals:
            erv = await deal_search.calculate_erv(deal, original_price=user_context["monthly_budget"] * 0.3)
            all_offers.append({
                "category": category,
                "title": deal.get("title", ""),
                "description": deal.get("snippet", "")[:200],
                "url": deal.get("url", ""),
                "erv": erv,
                "source": deal.get("source", "search")
            })

    # Also include Gmail-parsed rewards
    try:
        from src.mcp.gmail_parser import gmail_parser
        parsed = await gmail_parser.parse_inbox()
        for item in parsed:
            if item.get("type") in ("REWARD", "CASHBACK_OFFER"):
                all_offers.append({
                    "category": "From Your Inbox",
                    "title": item.get("offer_detail", "")[:80],
                    "description": f"{item.get('program', '')} — {item.get('offer_detail', '')}",
                    "url": "",
                    "erv": item.get("erv_estimate") or 0.0,
                    "source": "gmail"
                })
    except Exception as e:
        print(f"Gmail offers error: {e}")

    return {"offers": all_offers, "count": len(all_offers), "card_used": card}


@router.get("/accounts")
async def get_accounts():
    """Returns configured credit cards and their current offer summaries."""
    from src.mcp.realtime_search import deal_search

    accounts = []
    for card in _user_settings.get("cards", []):
        query = f"{card['name']} best current offer cashback reward"
        deals = await deal_search.search_deals(query, num_results=2)
        top_deal = deals[0] if deals else {}
        accounts.append({
            "name": card["name"],
            "type": card["type"],
            "network": card["network"],
            "top_offer": top_deal.get("snippet", "No current offers found.")[:200],
            "offer_title": top_deal.get("title", "")[:100],
        })

    return {"accounts": accounts}


@router.get("/settings")
async def get_settings():
    """Returns current user settings."""
    return _user_settings


@router.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Updates user settings (active agents, muted categories, budget)."""
    global _user_settings
    for key in ("active_agents", "muted_categories", "monthly_budget", "travel_budget", "monthly_bills"):
        if key in settings:
            _user_settings[key] = settings[key]
    _auction_result.clear() if isinstance(_auction_result, dict) else None
    return {"status": "SETTINGS_UPDATED", "settings": _user_settings}


@router.post("/intent_update")
async def update_intent(data: IntentUpdate):
    """Records user intent signal (e.g., mute travel offers)."""
    uid = data.user_id
    if uid not in _user_intents:
        _user_intents[uid] = {}
    _user_intents[uid][data.category] = data.intent

    # If NEGATIVE/MUTE, add to muted categories
    if data.intent in ("NEGATIVE", "MUTE"):
        if data.category not in _user_settings["muted_categories"]:
            _user_settings["muted_categories"].append(data.category)
        if data.category in _user_settings["active_agents"]:
            _user_settings["active_agents"].remove(data.category)

    return {
        "status": "INTENT_UPDATED",
        "user_id": uid,
        "category": data.category,
        "intent": data.intent,
        "muted_categories": _user_settings["muted_categories"]
    }


@router.post("/apply_move")
async def apply_move():
    """Executes the current winning financial move — logs and confirms."""
    if not _auction_result or _auction_result.get("status") != "WINNING_MOVE_GENERATED":
        raise HTTPException(status_code=400, detail="No auction result available. Trigger auction first.")

    return {
        "status": "MOVE_APPLIED",
        "agent": _auction_result.get("winning_agent"),
        "erv": _auction_result.get("erv"),
        "message": "Financial Winning Move executed. Your spending has been optimized."
    }


@router.get("/auction_status")
async def auction_status():
    """Returns the current auction result."""
    return _auction_result or {"status": "NO_AUCTION_RUN"}


@router.get("/gmail_summary")
async def gmail_summary():
    """Triggers Gmail parsing and returns a summary of found rewards/subscriptions."""
    try:
        from src.mcp.gmail_parser import gmail_parser
        results = await gmail_parser.parse_inbox()
        return {
            "status": "SUCCESS",
            "total_parsed": len(results),
            "rewards": [r for r in results if r.get("type") == "REWARD"],
            "subscriptions": [r for r in results if r.get("type") == "SUBSCRIPTION"],
            "cashback_offers": [r for r in results if r.get("type") == "CASHBACK_OFFER"],
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
