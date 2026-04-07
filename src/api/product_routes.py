"""
Product Deal Search API Routes.
Handles product purchase optimization using saved credit cards.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["product"])


class ProductSearchRequest(BaseModel):
    product: str


@router.post("/search")
async def search_product_deals(request: ProductSearchRequest):
    """
    Finds the best credit card deal for a given product.
    - Fetches product price from web
    - Compares cashback/discount for each saved card
    - Returns ranked comparison + best deal
    """
    from src.data.local_db import get_cards
    from src.mcp.product_search import compare_product_deals

    if not request.product or len(request.product.strip()) < 3:
        return {"error": "Please enter a valid product name."}

    # Get saved cards
    cards = await get_cards()
    if not cards:
        from src.mcp.card_detector import get_demo_cards
        cards = get_demo_cards()

    # Run comparison
    result = await compare_product_deals(request.product.strip(), cards)

    # Save to history
    try:
        from src.data.local_db import save_search_result
        await save_search_result(request.product, result.get("deals", []))
    except Exception:
        pass

    return result


@router.get("/history")
async def get_search_history():
    """Returns the last 10 product searches."""
    import aiosqlite
    import json
    from src.data.local_db import DB_PATH
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT product, results_json, searched_at FROM product_searches ORDER BY searched_at DESC LIMIT 10"
            )
            rows = await cursor.fetchall()
            return {
                "history": [
                    {
                        "product": r["product"],
                        "searched_at": r["searched_at"],
                        "deal_count": len(json.loads(r["results_json"] or "[]"))
                    }
                    for r in rows
                ]
            }
    except Exception as e:
        return {"history": [], "error": str(e)}
