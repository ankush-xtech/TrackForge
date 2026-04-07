"""
User management API endpoints with role-hierarchy enforcement.

Liskov Substitution: All role checks delegate to RoleService — no ad-hoc string checks.
Single Responsibility: This file handles HTTP concerns; RoleService handles permission logic.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user, role_required
from app.core.roles import role_service
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import (
    InvitableRolesResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


# ─── List users ────────────────────────────────────────────────
@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(role_required("manager")),
    db: AsyncSession = Depends(get_db),
):
    """
    List users in the organization.
    - org_admin / super_admin: sees all users in the org
    - manager: sees only employees THEY created + themselves
    """
    offset = (page - 1) * per_page

    query = select(User).where(
        User.organization_id == current_user.organization_id,
        User.deleted_at.is_(None),
    )

    # Managers only see employees THEY created + themselves
    if current_user.role == "manager":
        query = query.where(
            (
                (User.role == "employee")
                & (User.created_by == current_user.id)
            )
            | (User.id == current_user.id)
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


# ─── Get invitable roles for current user ──────────────────────
@router.get("/invitable-roles", response_model=InvitableRolesResponse)
async def get_invitable_roles(
    current_user: User = Depends(role_required("manager")),
):
    """Return the list of roles the current user is allowed to assign when inviting."""
    roles = role_service.invitable_roles(current_user.role)
    return InvitableRolesResponse(roles=roles)


# ─── Create / Invite user ──────────────────────────────────────
@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(role_required("manager")),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite/create a new user in the organization.
    - org_admin can create managers and employees.
    - manager can create employees only.
    - Role hierarchy is enforced by RoleService.
    """
    # Enforce invite permission
    if not role_service.can_invite(current_user.role, data.role):
        allowed = role_service.invitable_roles(current_user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You cannot assign the '{data.role}' role. You can invite: {', '.join(allowed) or 'nobody'}.",
        )

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
        created_by=current_user.id,  # Track who invited this user
    )
    db.add(user)
    await db.flush()
    return user


# ─── Get single user ──────────────────────────────────────────
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


# ─── Update user ──────────────────────────────────────────────
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user's profile.
    - Users can update their own non-role fields.
    - Role changes require hierarchy permission via RoleService.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    is_self = str(current_user.id) == str(user_id)
    is_above = role_service.is_above(current_user.role, user.role)

    # Non-self edits require being above in the hierarchy
    if not is_self and not is_above:
        raise HTTPException(status_code=403, detail="Cannot update this user — insufficient role level")

    # Role changes need strict hierarchy validation
    if data.role is not None:
        if is_self:
            raise HTTPException(status_code=403, detail="You cannot change your own role")
        if not role_service.can_change_role(current_user.role, user.role, data.role):
            raise HTTPException(
                status_code=403,
                detail=f"You cannot change this user's role to '{data.role}'",
            )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    return user


# ─── Deactivate user ──────────────────────────────────────────
@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(role_required("manager")),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete (deactivate) a user.
    - You must be strictly above the target in the hierarchy.
    - Cannot deactivate yourself.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    if user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Must be above the target's role
    if not role_service.is_above(current_user.role, user.role):
        raise HTTPException(status_code=403, detail="Cannot deactivate a user of equal or higher role")

    user.is_active = False
    user.soft_delete()
    await db.flush()
