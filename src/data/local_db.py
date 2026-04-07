"""
Local SQLite database for Sentinel Finance OS.
Stores credit cards discovered during setup and user preferences.
No AlloyDB required for dev/demo mode.
"""
import os
import json
import aiosqlite
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "../../sentinel_local.db")
DB_PATH = os.path.abspath(DB_PATH)

CREATE_CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS credit_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    bank TEXT,
    card_type TEXT,
    network TEXT,
    benefits_json TEXT,
    cashback_rate REAL DEFAULT 0.0,
    annual_fee REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

CREATE_SEARCHES_TABLE = """
CREATE TABLE IF NOT EXISTS product_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    results_json TEXT,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    """Creates DB tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_CARDS_TABLE)
        await db.execute(CREATE_SETTINGS_TABLE)
        await db.execute(CREATE_SEARCHES_TABLE)
        await db.commit()
    print(f"✅ Local DB initialized at {DB_PATH}")


async def is_setup_complete() -> bool:
    """Returns True if user has saved at least one credit card."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM credit_cards")
            row = await cursor.fetchone()
            return (row[0] if row else 0) > 0
    except Exception:
        return False


async def save_cards(cards: List[Dict[str, Any]]) -> int:
    """
    Saves a list of credit card dicts to the DB.
    Returns count of saved cards.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Clear existing cards first (fresh setup)
        await db.execute("DELETE FROM credit_cards")
        for card in cards:
            await db.execute(
                """
                INSERT INTO credit_cards (name, bank, card_type, network, benefits_json, cashback_rate, annual_fee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.get("name", "Unknown Card"),
                    card.get("bank", ""),
                    card.get("card_type", ""),
                    card.get("network", ""),
                    json.dumps(card.get("benefits", [])),
                    card.get("cashback_rate", 0.0),
                    card.get("annual_fee", 0.0),
                )
            )
        await db.commit()
    return len(cards)


async def get_cards() -> List[Dict[str, Any]]:
    """Returns all saved credit cards from the DB."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, name, bank, card_type, network, benefits_json, cashback_rate, annual_fee FROM credit_cards ORDER BY id"
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "bank": r["bank"],
                    "card_type": r["card_type"],
                    "network": r["network"],
                    "benefits": json.loads(r["benefits_json"] or "[]"),
                    "cashback_rate": r["cashback_rate"],
                    "annual_fee": r["annual_fee"],
                }
                for r in rows
            ]
    except Exception as e:
        print(f"get_cards error: {e}")
        return []


async def update_card_benefits(card_id: int, benefits: List[str], cashback_rate: float):
    """Updates a card's web-enriched benefits data."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE credit_cards SET benefits_json=?, cashback_rate=? WHERE id=?",
            (json.dumps(benefits), cashback_rate, card_id)
        )
        await db.commit()


async def save_setting(key: str, value: str):
    """Saves or updates a user setting."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()


async def get_setting(key: str, default: str = "") -> str:
    """Gets a user setting value."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT value FROM user_settings WHERE key=?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else default
    except Exception:
        return default


async def save_search_result(product: str, results: List[Dict]):
    """Caches a product search result."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO product_searches (product, results_json) VALUES (?, ?)",
            (product, json.dumps(results))
        )
        await db.commit()
