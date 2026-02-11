"""Security utilities for the application."""

from passlib.context import CryptContext
from typing import Optional

# Password hashing context (for future authentication features)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def mask_api_key(api_key: str) -> str:
    """Mask API key for logging purposes."""
    if not api_key or len(api_key) < 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"
