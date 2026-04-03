"""
FastAPI dependency injection functions.
Reusable dependencies for authentication, authorization, and database access.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token."""
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has admin privileges."""
    if current_user.role not in ("super_admin", "org_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required.",
        )
    return current_user


async def get_current_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has at least manager privileges."""
    if current_user.role not in ("super_admin", "org_admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Manager access required.",
        )
    return current_user


async def get_current_active_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the current user is active and has verified their email/account.
    Useful for endpoints that require email verification.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )
    return current_user
