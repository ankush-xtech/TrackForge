"""
FastAPI dependency injection functions.
Uses the RoleService as the single source of truth for all permission checks.

Open/Closed Principle: To add a new permission level, add to roles.py — not here.
Dependency Inversion: Endpoints depend on abstractions (role_required), not concrete checks.
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.roles import role_service
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


def role_required(minimum_role: str) -> Callable:
    """
    Factory that creates a FastAPI dependency requiring a minimum role level.

    Usage in endpoints:
        current_user: User = Depends(role_required("manager"))
        current_user: User = Depends(role_required("org_admin"))
    """

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if not role_service.is_at_least(current_user.role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. {minimum_role} access or higher required.",
            )
        return current_user

    return _check


# ── Convenience aliases (backward-compatible) ──

async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has admin privileges (org_admin or super_admin)."""
    if not role_service.is_at_least(current_user.role, "org_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required.",
        )
    return current_user


async def get_current_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has at least manager privileges."""
    if not role_service.is_at_least(current_user.role, "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Manager access required.",
        )
    return current_user


async def get_current_active_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active and has verified their email."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )
    return current_user
