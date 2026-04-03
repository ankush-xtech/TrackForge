"""
Authentication API endpoints: register, login, refresh, password management, email verification.
"""

import logging
import traceback

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import (
    change_password,
    confirm_password_reset,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    request_password_reset,
    verify_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and create an organization."""
    try:
        return await register_user(db, data)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        logger.error(traceback.format_exc())
        raise


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and get access/refresh tokens."""
    return await login_user(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Get a new access token using a refresh token."""
    return await refresh_access_token(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return current_user


@router.post("/change-password", response_model=MessageResponse, status_code=200)
async def change_user_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change the authenticated user's password.

    Requires:
    - Valid access token
    - Current password for verification
    - New password meeting strength requirements
    """
    return await change_password(db, current_user, data)


@router.post("/forgot-password", response_model=MessageResponse, status_code=200)
async def forgot_password(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset token via email.

    Returns a reset token that can be used with /reset-password endpoint.
    In production, this token would be sent to the user's email.
    """
    token = await request_password_reset(db, data.email)
    # In production, send token via email
    # For now, return it for testing
    return {"message": f"Password reset token: {token}"}


@router.post("/reset-password", response_model=MessageResponse, status_code=200)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using a password reset token.

    Requires:
    - A valid reset token (from /forgot-password)
    - New password meeting strength requirements
    """
    return await confirm_password_reset(db, data.token, data.new_password)


@router.post("/verify-email/{token}", response_model=MessageResponse, status_code=200)
async def verify_email_endpoint(
    token: str = Path(..., description="Email verification token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a user's email address.

    Uses an email verification token (typically sent via email).
    """
    return await verify_email(db, token)


@router.post("/logout", response_model=MessageResponse, status_code=200)
async def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout the authenticated user.

    Optionally provide a refresh token to invalidate (for future token blacklisting).
    """
    return await logout_user(db, current_user, data.refresh_token)
