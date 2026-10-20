"""
FR-3.1 (persistence half): save detected patterns to public.chart_patterns.

chart_patterns has no unique constraint, so a plain insert would pile up
duplicates every time a ticker is re-analysed. Instead the rows for
(stock, trade_date) are replaced: history across different dates is kept,
re-running on the same day is idempotent.
"""
import asyncio
import logging

from app.data.supabase_client import get_stock_id, get_supabase

logger = logging.getLogger(__name__)


def _replace_rows(stock_id: str, trade_date: str, rows: list[dict]) -> None:
    table = get_supabase().table("chart_patterns")
    table.delete().eq("stock_id", stock_id).eq("trade_date", trade_date).execute()
    if rows:
        table.insert(rows).execute()


async def save_patterns(ticker: str, records: list[dict]) -> int:
    """
    Replaces the stored patterns for `ticker` on the records' trade_date and
    returns how many rows were written. Raises ValueError if the ticker is
    not in public.stocks; database errors propagate to the caller.
    """
    if not records:
        return 0

    stock_id = await get_stock_id(ticker)
    if stock_id is None:
        raise ValueError(f"{ticker} is not in public.stocks; add it there first")

    trade_date = records[0]["trade_date"]
    rows = [{"stock_id": stock_id, **record} for record in records]
    await asyncio.to_thread(_replace_rows, stock_id, trade_date, rows)
    return len(rows)
