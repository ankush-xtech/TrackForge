"""
Authentication and security utilities.
JWT token creation/verification and password hashing.
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Validate password strength requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Returns:
        A tuple of (is_valid, error_message). If valid, error_message is None.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    return True, None


def create_access_token(subject: str | int, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a JWT access token."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    """Create a JWT refresh token with longer expiry."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """
    Create a short-lived password reset token (1 hour expiry).

    Args:
        email: The user's email address to encode in the token.

    Returns:
        A JWT token with 1-hour expiry.
    """
    expire = datetime.now(UTC) + timedelta(hours=1)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "password_reset",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token (24 hour expiry).

    Args:
        email: The user's email address to encode in the token.

    Returns:
        A JWT token with 24-hour expiry.
    """
    expire = datetime.now(UTC) + timedelta(hours=24)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "email_verification",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
