"""
Organization management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/me", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's organization details."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not associated with an organization",
        )

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.patch("/me", response_model=OrganizationResponse)
async def update_organization(
    data: OrganizationUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update organization settings (admin only)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not associated with an organization",
        )

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.flush()
    return org


@router.get("/me/stats")
async def get_organization_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization statistics (any authenticated user)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not associated with an organization",
        )

    org_id = current_user.organization_id

    # Count total users
    total_users_result = await db.execute(
        select(func.count()).select_from(User).where(
            and_(
                User.organization_id == org_id,
                User.deleted_at.is_(None),
            )
        )
    )
    total_users = total_users_result.scalar() or 0

    # Count active users
    active_users_result = await db.execute(
        select(func.count()).select_from(User).where(
            and_(
                User.organization_id == org_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
    )
    active_users = active_users_result.scalar() or 0

    # Note: We would count total projects and tracked hours here,
    # but we'll return 0 for now since TimeEntry and Project schemas may vary
    # This can be extended once those models are confirmed

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_projects": 0,
        "total_tracked_hours": 0,
    }
