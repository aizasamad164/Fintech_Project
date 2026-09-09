"""
FR-1.1: User registration/authentication via email+password or OAuth (JWT-based).
Delegates actual auth to Supabase Auth; this router proxies/validates tokens.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    # TODO: call Supabase auth.sign_up
    raise NotImplementedError


@router.post("/login")
async def login():
    # TODO: call Supabase auth.sign_in_with_password
    raise NotImplementedError
