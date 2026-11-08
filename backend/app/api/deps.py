"""
Who is calling the API.

Two modes, chosen automatically from backend/.env:

  supabase  SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set.
            Every protected request must send `Authorization: Bearer <access token>`
            (the token the frontend gets from Supabase Auth after sign-in).
            We ask Supabase to verify it, so this works with any Supabase JWT
            signing setup, and cache the answer briefly.

  demo      Supabase is not configured (a teammate running locally without keys).
            The caller identifies itself with a random UUID (`user_id`), exactly as
            before. Nothing is secure in this mode; it only keeps the app usable.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import Header, HTTPException, Query, status

from app.data import portfolio_store

logger = logging.getLogger(__name__)

_TOKEN_TTL = 300  # seconds a verified token is trusted before asking Supabase again
_token_cache: Dict[str, Tuple[float, "CurrentUser"]] = {}


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: Optional[str] = None
    demo: bool = False


def auth_mode() -> str:
    """'supabase' when real accounts are available, otherwise 'demo'."""
    return "supabase" if portfolio_store.storage_mode() == "supabase" else "demo"


def _verify_with_supabase(token: str) -> Optional[CurrentUser]:
    """Returns the user the token belongs to, or None if Supabase rejects it."""
    from app.data.supabase_client import get_supabase
    try:
        res = get_supabase().auth.get_user(token)
    except Exception as exc:  # noqa: BLE001 - invalid/expired tokens raise
        logger.info("Token rejected by Supabase: %s", exc)
        return None
    user = getattr(res, "user", None)
    if not user or not getattr(user, "id", None):
        return None
    return CurrentUser(id=str(user.id), email=getattr(user, "email", None))


async def _user_from_token(token: str) -> Optional[CurrentUser]:
    key = hashlib.sha256(token.encode()).hexdigest()
    hit = _token_cache.get(key)
    if hit and time.time() - hit[0] < _TOKEN_TTL:
        return hit[1]
    user = await asyncio.to_thread(_verify_with_supabase, token)
    if user:
        _token_cache[key] = (time.time(), user)
    return user


def _bearer(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


def _demo_user(user_id: Optional[str]) -> Optional[CurrentUser]:
    if not user_id:
        return None
    try:
        return CurrentUser(id=str(uuid.UUID(user_id)), demo=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="user_id must be a UUID")


async def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    user_id: Optional[str] = Query(default=None, description="Demo mode only"),
) -> Optional[CurrentUser]:
    if auth_mode() == "supabase":
        token = _bearer(authorization)
        return await _user_from_token(token) if token else None
    return _demo_user(user_id)


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    user_id: Optional[str] = Query(default=None, description="Demo mode only"),
) -> CurrentUser:
    user = await get_optional_user(authorization, user_id)
    if user is None:
        detail = ("Sign in to continue." if auth_mode() == "supabase"
                  else "user_id is required (demo mode: Supabase is not configured).")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                            headers={"WWW-Authenticate": "Bearer"})
    return user
