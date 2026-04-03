"""
User management API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the organization (admin only)."""
    offset = (page - 1) * per_page

    # Only show users from same org
    query = select(User).where(
        User.organization_id == current_user.organization_id,
        User.deleted_at.is_(None),
    )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    return UserListResponse(users=users, total=total, page=page, per_page=per_page)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Invite/create a new user in the organization (admin only)."""
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        timezone=data.timezone,
        job_title=data.job_title,
        organization_id=current_user.organization_id,
        team_id=data.team_id,
    )
    db.add(user)
    await db.flush()
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user's profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile. Users can update themselves; admins can update anyone."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only admins can update other users
    is_self = current_user.id == user_id
    is_admin = current_user.role in ("super_admin", "org_admin")
    if not is_self and not is_admin:
        raise HTTPException(status_code=403, detail="Cannot update other users")

    # Only admins can change roles
    if data.role and not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can change roles")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    return user


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete (deactivate) a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = False
    user.soft_delete()
    await db.flush()
