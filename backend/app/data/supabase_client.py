"""
Shared Supabase client for server-side (service-role) database access.

NFR-2.1: the service-role key must NEVER be used from the frontend — it
bypasses RLS. It is only ever loaded here, from backend env vars, and only
this backend process talks to Postgres with it. All writes to ohlcv_daily,
technical_features, ml_signals and allocation_* go through this client.

Schema note: market tables are keyed by `stock_id` (uuid from public.stocks),
not by ticker. Use get_stock_id() to translate.
"""
import asyncio
from functools import lru_cache

from supabase import create_client, Client

from app.config import settings

# Supabase returns at most 1000 rows per request by default, so anything we
# read in bulk has to be paged, and writes are sent in chunks of this size.
CHUNK_SIZE = 1000


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """
    Returns a cached, process-wide Supabase client authenticated with the
    service-role key. Cached with lru_cache so we only construct it once.
    """
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# ---------------------------------------------------------------------------
# ticker -> stock_id
# ---------------------------------------------------------------------------
# Only successful lookups are cached, so a stock you add to public.stocks
# later is picked up without restarting the server.
_stock_id_cache: dict[str, str] = {}


def _lookup_stock_id(ticker: str) -> str | None:
    resp = (
        get_supabase()
        .table("stocks")
        .select("id")
        .eq("ticker", ticker)
        .limit(1)
        .execute()
    )
    return resp.data[0]["id"] if resp.data else None


async def get_stock_id(ticker: str) -> str | None:
    """
    Returns the uuid in public.stocks for `ticker`, or None if the ticker has
    not been added to the stocks table yet.
    """
    ticker = ticker.upper().strip()
    if ticker in _stock_id_cache:
        return _stock_id_cache[ticker]

    stock_id = await asyncio.to_thread(_lookup_stock_id, ticker)
    if stock_id is not None:
        _stock_id_cache[ticker] = stock_id
    return stock_id


# ---------------------------------------------------------------------------
# chunked upsert
# ---------------------------------------------------------------------------
def upsert_in_chunks(
    table: str,
    records: list[dict],
    on_conflict: str = "stock_id,trade_date",
) -> int:
    """
    Upserts `records` into `table` in chunks and returns how many rows were sent.
    Blocking — call it through asyncio.to_thread() from async code.

    `on_conflict` MUST name the table's unique columns. Without it, PostgREST
    conflicts on the primary key (the auto-generated `id`), which never
    matches, so re-running an ingest would fail on the unique constraint or
    create duplicates instead of updating.
    """
    client = get_supabase()
    for i in range(0, len(records), CHUNK_SIZE):
        client.table(table).upsert(
            records[i : i + CHUNK_SIZE], on_conflict=on_conflict
        ).execute()
    return len(records)
