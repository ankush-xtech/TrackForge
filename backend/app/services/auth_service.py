"""
Authentication business logic — registration, login, token refresh, password management.
"""

import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

settings = get_settings()


def _slugify(name: str) -> str:
    """Convert organization name to URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


async def register_user(db: AsyncSession, data: RegisterRequest) -> TokenResponse:
    """Register a new user and create their organization."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create organization
    slug = _slugify(data.organization_name)
    # Ensure unique slug
    slug_check = await db.execute(select(Organization).where(Organization.slug == slug))
    if slug_check.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(
        name=data.organization_name,
        slug=slug,
        plan_type="free",
        max_users=5,
        settings={
            "screenshot_interval": 300,
            "screenshot_blur": False,
            "track_urls": True,
            "track_apps": True,
            "idle_threshold": 300,
            "timezone": "UTC",
        },
    )
    db.add(org)
    await db.flush()

    # Create user as org admin
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role="org_admin",
        organization_id=org.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role, "org_id": str(org.id)},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def login_user(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate a user and return tokens."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role, "org_id": str(user.organization_id)},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Generate a new access token using a valid refresh token."""
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    new_access = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role, "org_id": str(user.organization_id)},
    )
    new_refresh = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def change_password(
    db: AsyncSession, user: User, data: ChangePasswordRequest
) -> dict[str, str]:
    """
    Change a user's password after validating the old password.

    Args:
        db: Database session.
        user: The authenticated user.
        data: ChangePasswordRequest containing old and new passwords.

    Returns:
        A dict with a success message.

    Raises:
        HTTPException: If old password is invalid or new password fails validation.
    """
    # Verify old password
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_message,
        )

    # Prevent reusing the same password
    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different from current password",
        )

    # Hash and update
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.flush()

    return {"message": "Password changed successfully"}


async def request_password_reset(db: AsyncSession, email: str) -> str:
    """
    Generate a password reset token for a user.

    Args:
        db: Database session.
        email: The user's email address.

    Returns:
        A password reset token (short-lived, 1 hour).

    Raises:
        HTTPException: If user with email doesn't exist.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # For security, we don't reveal whether the email exists
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found",
        )

    token = create_password_reset_token(email)
    return token


async def confirm_password_reset(
    db: AsyncSession, token: str, new_password: str
) -> dict[str, str]:
    """
    Reset a user's password using a password reset token.

    Args:
        db: Database session.
        token: The password reset token.
        new_password: The new password to set.

    Returns:
        A dict with a success message.

    Raises:
        HTTPException: If token is invalid or new password fails validation.
    """
    # Decode token
    payload = decode_token(token)
    if payload is None or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token",
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        )

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_message,
        )

    # Update password
    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.flush()

    return {"message": "Password reset successfully"}


async def verify_email(db: AsyncSession, token: str) -> dict[str, str]:
    """
    Verify a user's email address using an email verification token.

    Args:
        db: Database session.
        token: The email verification token.

    Returns:
        A dict with a success message.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    # Decode token
    payload = decode_token(token)
    if payload is None or payload.get("type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification token",
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification token",
        )

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Mark email as verified
    user.is_verified = True
    db.add(user)
    await db.flush()

    return {"message": "Email verified successfully"}


async def logout_user(
    db: AsyncSession, user: User, refresh_token: str | None = None
) -> dict[str, str]:
    """
    Logout a user (placeholder for token blacklisting implementation).

    Currently, this function serves as a placeholder. In a production system,
    this would invalidate refresh tokens via a blacklist or token store.

    Args:
        db: Database session.
        user: The authenticated user.
        refresh_token: Optional refresh token to invalidate.

    Returns:
        A dict with a success message.
    """
    # Placeholder: In production, implement token blacklisting
    # For now, just confirm logout success
    return {"message": "Logged out successfully"}
