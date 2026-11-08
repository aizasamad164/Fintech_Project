"""
FR-1.1: accounts. Sign-up, sign-in, email confirmation, password reset and
Google sign-in all happen in the browser through Supabase Auth; the frontend
then sends its access token to this API (see app/api/deps.py).

  GET /api/auth/mode   'supabase' (real accounts) or 'demo' (no Supabase configured)
  GET /api/auth/me     who the token belongs to
"""
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, auth_mode, get_current_user

router = APIRouter()


@router.get("/mode")
async def mode():
    return {"mode": auth_mode()}


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "demo": user.demo}
