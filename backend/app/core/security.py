"""
NFR-2.3: Passwords salted and hashed using bcrypt before storage.
(Note: if using Supabase Auth directly, it handles this already — this
module is for any additional app-level credential handling.)
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
