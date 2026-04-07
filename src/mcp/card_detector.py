"""
Credit Card Detector — extracts credit card identities from Gmail emails
and enriches them with web-searched benefits data.
"""
import re
from typing import List, Dict, Any
from src.mcp.realtime_search import deal_search

# ── Known card patterns ───────────────────────────────────────────────────
# (pattern, card_name, bank, network, card_type, estimated_cashback_rate)
KNOWN_CARDS = [
    # Chase
    (r"chase sapphire (preferred|reserve|plus)?", "Chase Sapphire Preferred", "Chase", "Visa", "travel", 0.03),
    (r"chase freedom (flex|unlimited)?", "Chase Freedom Unlimited", "Chase", "Visa", "cashback", 0.015),
    (r"chase amazon", "Chase Amazon Prime", "Chase", "Visa", "cashback", 0.05),
    # HDFC
    (r"hdfc (millennia|regalia|diners|moneyback|freedom|infinia|swiggy)", "HDFC Millennia", "HDFC Bank", "Mastercard", "cashback", 0.05),
    (r"hdfc bank", "HDFC Credit Card", "HDFC Bank", "Mastercard", "cashback", 0.02),
    # ICICI
    (r"icici (amazon|rubyx|coral|sapphiro|emerald|platinum)", "ICICI Coral", "ICICI Bank", "Visa", "cashback", 0.02),
    (r"icici bank", "ICICI Credit Card", "ICICI Bank", "Visa", "cashback", 0.015),
    # SBI
    (r"sbi (simplysave|simplyclick|elite|prime|cashback)", "SBI SimplyCLICK", "SBI Card", "Visa", "cashback", 0.025),
    (r"sbi card", "SBI Credit Card", "SBI Card", "Visa", "cashback", 0.015),
    # Axis
    (r"axis (magnus|vistara|ace|flipkart|buzz|myzone)", "Axis Bank Magnus", "Axis Bank", "Visa", "travel", 0.04),
    (r"axis bank", "Axis Bank Credit Card", "Axis Bank", "Visa", "cashback", 0.02),
    # Kotak
    (r"kotak (811|delight|league|myntra|royale)", "Kotak 811 Credit Card", "Kotak Bank", "Visa", "cashback", 0.02),
    # American Express
    (r"amex|american express", "American Express Gold", "Amex", "Amex", "rewards", 0.04),
    # Citi
    (r"citi (cashback|rewards|prestige|premier)", "Citi Cashback Card", "Citibank", "Mastercard", "cashback", 0.05),
    # IDFC
    (r"idfc (first|wow|millennia)", "IDFC FIRST Classic", "IDFC FIRST Bank", "Visa", "cashback", 0.025),
    # RBL
    (r"rbl (shoprite|play|popcorn|icon)", "RBL ShopRite", "RBL Bank", "Mastercard", "cashback", 0.02),
    # IndusInd
    (r"indusind (legend|iconia|nexxt|platinum)", "IndusInd Legend", "IndusInd Bank", "Visa", "travel", 0.03),
    # Yes Bank
    (r"yes (first|exclusive|prosperity)", "Yes Bank First Exclusive", "Yes Bank", "Mastercard", "rewards", 0.025),
    # Standard Chartered
    (r"standard chartered|sc (ultimate|manhattan|smart)", "SC Ultimate Credit Card", "Standard Chartered", "Visa", "cashback", 0.03),
    # Paytm / One Card
    (r"paytm (hdfc|sbi)?", "Paytm Credit Card", "Paytm", "Mastercard", "cashback", 0.02),
    (r"one card|onecard", "OneCard", "OneCard", "Mastercard", "cashback", 0.01),
]

# Senders that typically send credit card related emails
CARD_SENDER_PATTERNS = [
    r"@chase\.com", r"@hdfcbank\.com", r"@icicibank\.com", r"@sbicard\.com",
    r"@axisbank\.com", r"@kotakbank\.com", r"@amex\.com", r"@citibank\.com",
    r"@idfcfirstbank\.com", r"@rblbank\.com", r"@indusind\.com", r"@yesbank\.in",
    r"@sc\.com", r"@StandardChartered\.com",
]


def _match_card(text: str) -> Dict[str, Any]:
    """Matches text against known card patterns. Returns card dict or None."""
    text_lower = text.lower()
    for pattern, name, bank, network, card_type, cashback in KNOWN_CARDS:
        if re.search(pattern, text_lower):
            return {
                "name": name,
                "bank": bank,
                "network": network,
                "card_type": card_type,
                "cashback_rate": cashback,
                "annual_fee": 0.0,
                "benefits": [],
                "source": "email_detected"
            }
    return None


async def detect_cards_from_emails(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scans parsed Gmail emails to find mentioned credit cards.
    Returns a deduplicated list of detected card dicts.
    """
    detected = {}

    for email in emails:
        combined = f"{email.get('subject', '')} {email.get('snippet', '')} {email.get('from', '')} {email.get('body', '')}"

        card = _match_card(combined)
        if card and card["name"] not in detected:
            detected[card["name"]] = card
            print(f"🃏 Detected card: {card['name']} from email '{email.get('subject', '')[:50]}'")

        # Also check sender domain
        sender = email.get("from", "")
        for sender_pattern in CARD_SENDER_PATTERNS:
            if re.search(sender_pattern, sender, re.IGNORECASE):
                # Try to extract card from subject
                subj_card = _match_card(email.get("subject", ""))
                if subj_card and subj_card["name"] not in detected:
                    detected[subj_card["name"]] = subj_card
                break

    return list(detected.values())


def get_demo_cards() -> List[Dict[str, Any]]:
    """Returns a realistic demo card set for when Gmail is not connected."""
    return [
        {
            "name": "Chase Sapphire Preferred",
            "bank": "Chase",
            "network": "Visa",
            "card_type": "travel",
            "cashback_rate": 0.03,
            "annual_fee": 95.0,
            "benefits": ["3x points on dining", "3x on travel", "60,000 bonus points"],
            "source": "demo"
        },
        {
            "name": "HDFC Millennia Credit Card",
            "bank": "HDFC Bank",
            "network": "Mastercard",
            "card_type": "cashback",
            "cashback_rate": 0.05,
            "annual_fee": 1000.0,
            "benefits": ["5% cashback on Amazon/Flipkart", "2.5% on all online spends"],
            "source": "demo"
        },
        {
            "name": "Axis Bank Magnus",
            "bank": "Axis Bank",
            "network": "Visa",
            "card_type": "travel",
            "cashback_rate": 0.035,
            "annual_fee": 12500.0,
            "benefits": ["Unlimited domestic lounge", "4x miles on travel", "Edge Miles"],
            "source": "demo"
        },
        {
            "name": "SBI SimplyCLICK",
            "bank": "SBI Card",
            "network": "Visa",
            "card_type": "cashback",
            "cashback_rate": 0.025,
            "annual_fee": 499.0,
            "benefits": ["10x reward points on Amazon", "5x on partner merchants"],
            "source": "demo"
        },
    ]


async def enrich_card_with_web(card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Searches the web for the card's current offers/benefits and enriches the card dict.
    """
    query = f"{card['name']} {card['bank']} credit card benefits offers cashback rewards 2025"
    results = await deal_search.search_deals(query, num_results=3)

    benefits = []
    for r in results:
        snippet = r.get("snippet", "")
        if snippet and len(snippet) > 20:
            # Extract bullet-point benefits from snippet
            benefits.append(snippet[:150])

    if not benefits:
        # Generate benefits from cashback rate
        rate = card.get("cashback_rate", 0.02)
        benefits = [
            f"{int(rate * 100)}% cashback on select categories",
            f"Earn reward points on every purchase",
            f"Welcome benefits on first transaction",
        ]

    card["benefits"] = benefits[:3]  # Keep top 3
    return card
