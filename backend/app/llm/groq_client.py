# backend/app/llm/groq_client.py
"""
Groq async client.

Reads GROQ_API_KEY through app.config.settings (which loads backend/.env), so
it works with plain `uvicorn app.main:app` and doesn't need the key exported
in the shell. Created lazily: a missing key no longer crashes the whole
server at import time; only chat/explanation calls fail, and those fall back.
"""
from __future__ import annotations

from typing import Optional

from groq import AsyncGroq

from app.config import settings

_client: Optional[AsyncGroq] = None


def get_groq_client() -> AsyncGroq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is missing from backend/.env")
        _client = AsyncGroq(api_key=settings.groq_api_key, timeout=30.0)
    return _client


def groq_available() -> bool:
    return bool(settings.groq_api_key)


class _LazyClient:
    """Keeps `from app.llm.groq_client import groq_client` working in agent.py."""

    def __getattr__(self, item):
        return getattr(get_groq_client(), item)


groq_client = _LazyClient()
