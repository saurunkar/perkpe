from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Offer(BaseModel):
    title: str
    description: str
    erv: float
    category: str

@router.get("/offer-of-the-day", response_model=Offer)
async def get_offer_of_the_day():
    """
    Returns a mock 'Financial Winning Move' for the dashboard.
    In a real system, this would be triggered at 7 AM by the Arbitrator.
    """
    return Offer(
        title="Chase Sapphire Rewards Optimization",
        description="50,000 points expiring soon. Redirect your lifestyle spend to maximize 3x multipliers before Oct 31st.",
        erv=750.00,
        category="Lifestyle"
    )

@router.post("/trigger_auction")
async def trigger_auction():
    """
    Invoked via Cloud Scheduler at 06:30 AM to start the arbitrator process.
    """
    return {"status": "AUCTION_TRIGGERED"}

@router.post("/intent_update")
async def update_intent(user_id: str, category: str, intent: str):
    """
    Handles user feedback (e.g., 'Mute Travel').
    """
    return {"status": "INTENT_UPDATED", "user_id": user_id, "category": category, "intent": intent}
