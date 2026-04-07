"""
Setup Wizard API Routes.
Handles first-run onboarding: Gmail scan → card detection → approval → save → enrich.
"""
from fastapi import APIRouter, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter(tags=["setup"])

# Module-level state for enrichment progress
_enrich_status: Dict[str, Any] = {"status": "idle", "progress": 0, "total": 0}


class SaveCardsRequest(BaseModel):
    cards: List[Dict[str, Any]]


@router.get("/status")
async def setup_status():
    """Returns whether the user has completed the setup wizard."""
    from src.data.local_db import is_setup_complete
    complete = await is_setup_complete()
    return {"is_complete": complete}


@router.post("/scan_gmail")
async def scan_gmail_for_cards():
    """
    Scans Gmail inbox and detects credit cards from email content.
    Returns detected cards for user review.
    """
    from src.mcp.gmail_parser import gmail_parser
    from src.mcp.card_detector import detect_cards_from_emails, get_demo_cards

    try:
        # Fetch emails from Gmail (or demo mode)
        emails = await gmail_parser.fetch_emails(max_results=30)

        # Detect credit cards from emails
        detected_cards = await detect_cards_from_emails(emails)
        print(f"Detected {len(detected_cards)} cards from {len(emails)} emails")

        # If no cards detected (no Gmail or no card emails), use demo set
        if not detected_cards:
            demo_cards = get_demo_cards()
            return {
                "status": "DEMO_MODE",
                "message": "No cards detected automatically. Showing suggested cards — check the ones you have.",
                "cards": demo_cards,
                "emails_scanned": len(emails),
                "source": "demo"
            }

        return {
            "status": "SUCCESS",
            "message": f"Scanned {len(emails)} emails and detected {len(detected_cards)} credit cards.",
            "cards": detected_cards,
            "emails_scanned": len(emails),
            "source": "gmail"
        }
    except Exception as e:
        print(f"scan_gmail error: {e}")
        from src.mcp.card_detector import get_demo_cards
        return {
            "status": "DEMO_MODE",
            "message": "Gmail scan failed. Showing suggested cards.",
            "cards": get_demo_cards(),
            "emails_scanned": 0,
            "source": "demo"
        }


@router.post("/save_cards")
async def save_approved_cards(request: SaveCardsRequest, background_tasks: BackgroundTasks):
    """
    Saves user-approved credit cards to local DB and triggers background enrichment.
    """
    from src.data.local_db import save_cards

    if not request.cards:
        return {"status": "ERROR", "message": "No cards provided."}

    count = await save_cards(request.cards)

    # Trigger background enrichment
    background_tasks.add_task(_enrich_all_cards, request.cards)

    return {
        "status": "SAVED",
        "message": f"Saved {count} cards. Enriching with web offers in background...",
        "count": count
    }


async def _enrich_all_cards(cards: List[Dict[str, Any]]):
    """Background task: enriches each card with web-scraped benefits data."""
    global _enrich_status
    from src.data.local_db import get_cards, update_card_benefits
    from src.mcp.card_detector import enrich_card_with_web

    _enrich_status = {"status": "running", "progress": 0, "total": len(cards)}

    # Re-fetch from DB to get IDs
    db_cards = await get_cards()

    for i, card in enumerate(db_cards):
        try:
            enriched = await enrich_card_with_web(card)
            await update_card_benefits(
                card["id"],
                enriched.get("benefits", []),
                enriched.get("cashback_rate", card.get("cashback_rate", 0.02))
            )
            _enrich_status["progress"] = i + 1
            print(f"✅ Enriched: {card['name']}")
        except Exception as e:
            print(f"Enrichment failed for {card['name']}: {e}")

    _enrich_status["status"] = "complete"


@router.get("/enrich_status")
async def enrich_status():
    """Returns background enrichment progress."""
    return _enrich_status


@router.delete("/reset")
async def reset_setup():
    """Resets the setup (clears all saved cards). Useful for retesting."""
    import aiosqlite
    from src.data.local_db import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM credit_cards")
        await db.execute("DELETE FROM user_settings")
        await db.commit()
    return {"status": "RESET", "message": "Setup data cleared. Refresh to run wizard again."}
