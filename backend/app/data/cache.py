"""
FR-2.4: In-memory cache to stay within external API rate limits (e.g. 60 req/min).
NFR-3.2: If live feeds fail, callers should fall back to the last cached value here
(or to the Supabase market_data_cache table for cold-start / multi-instance cases).
"""
from cachetools import TTLCache
from app.config import settings

# One shared cache instance for the process.
market_data_cache = TTLCache(
    maxsize=1000,
    ttl=settings.market_data_cache_ttl_seconds,
)


def get_cached(key: str):
    return market_data_cache.get(key)


def set_cached(key: str, value) -> None:
    market_data_cache[key] = value
