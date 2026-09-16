"""
Shared Supabase client for server-side (service-role) database access.

NFR-2.1: the service-role key must NEVER be used from the frontend — it
bypasses RLS. It is only ever loaded here, from backend env vars, and only
this backend process talks to Postgres with it. All writes to market_cache,
technical_features, scores, and allocations go through this client.
"""
from functools import lru_cache

from supabase import create_client, Client

from app.config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """
    Returns a cached, process-wide Supabase client authenticated with the
    service-role key. Cached with lru_cache so we only construct it once.
    """
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
