# backend/app/api/routes/news.py
"""GET /api/news/{ticker}?limit=3 -> headlines shaped for the frontend NewsCard."""
import asyncio
import time
from typing import Dict, List, Tuple

from fastapi import APIRouter, Query

from app.data.news import get_ticker_news

router = APIRouter()

# News changes slowly relative to page loads; cache 15 minutes per ticker
_TTL = 15 * 60
_cache: Dict[Tuple[str, int], Tuple[float, List[dict]]] = {}


@router.get("/{ticker}")
async def ticker_news(ticker: str, limit: int = Query(3, ge=1, le=10)):
    key = (ticker.upper().strip(), limit)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]

    raw = await asyncio.to_thread(get_ticker_news, key[0], limit)
    items = [
        {
            "id": f"{key[0]}-{i}",
            "ticker": key[0],
            "headline": a.get("title", ""),
            "source": a.get("publisher") or "Market News",
            "url": a.get("link") or "#",
            "publishedAt": a.get("published"),
        }
        for i, a in enumerate(raw.get("articles", []))
        if a.get("title")
    ]
    _cache[key] = (time.time(), items)
    return items
