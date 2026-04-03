"""
Team management API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_manager, get_current_user
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamListResponse, TeamResponse, TeamUpdate

router = APIRouter(prefix="/teams", tags=["Teams"])


async def get_team_member_count(db: AsyncSession, team_id: uuid.UUID) -> int:
    """Helper to count members in a team."""
    result = await db.execute(
        select(func.count()).select_from(User).where(User.team_id == team_id)
    )
    return result.scalar() or 0


@router.post("", response_model=TeamResponse, status_code=201)
async def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new team (admin only)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with an organization",
        )

    # If manager_id is provided, validate it exists and belongs to the org
    if data.manager_id:
        manager_result = await db.execute(
            select(User).where(
                and_(
                    User.id == data.manager_id,
                    User.organization_id == current_user.organization_id,
                    User.deleted_at.is_(None),
                )
            )
        )
        manager = manager_result.scalar_one_or_none()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found in this organization",
            )

    team = Team(
        name=data.name,
        description=data.description,
        organization_id=current_user.organization_id,
        manager_id=data.manager_id,
    )
    db.add(team)
    await db.flush()

    return TeamResponse(
        **{**team.__dict__, "member_count": 0}
    )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all teams in the organization (any authenticated user)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with an organization",
        )

    offset = (page - 1) * per_page

    # Count total teams in org
    count_query = select(Team).where(Team.organization_id == current_user.organization_id)
    total_result = await db.execute(
        select(func.count()).select_from(count_query.subquery())
    )
    total = total_result.scalar() or 0

    # Get teams for this page
    result = await db.execute(
        count_query.order_by(Team.created_at.desc()).offset(offset).limit(per_page)
    )
    teams = result.scalars().all()

    # Enrich teams with member counts
    team_responses = []
    for team in teams:
        member_count = await get_team_member_count(db, team.id)
        team_responses.append(
            TeamResponse(**{**team.__dict__, "member_count": member_count})
        )

    return TeamListResponse(
        teams=team_responses,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team details with member count."""
    result = await db.execute(
        select(Team).where(
            and_(
                Team.id == team_id,
                Team.organization_id == current_user.organization_id,
            )
        )
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    member_count = await get_team_member_count(db, team_id)
    return TeamResponse(**{**team.__dict__, "member_count": member_count})


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    data: TeamUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update team (admin only)."""
    result = await db.execute(
        select(Team).where(
            and_(
                Team.id == team_id,
                Team.organization_id == current_user.organization_id,
            )
        )
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # If manager_id is being set/changed, validate it
    if data.manager_id is not None and data.manager_id != team.manager_id:
        manager_result = await db.execute(
            select(User).where(
                and_(
                    User.id == data.manager_id,
                    User.organization_id == current_user.organization_id,
                    User.deleted_at.is_(None),
                )
            )
        )
        manager = manager_result.scalar_one_or_none()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found in this organization",
            )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.flush()

    member_count = await get_team_member_count(db, team_id)
    return TeamResponse(**{**team.__dict__, "member_count": member_count})


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete team (admin only). Team must have no members."""
    result = await db.execute(
        select(Team).where(
            and_(
                Team.id == team_id,
                Team.organization_id == current_user.organization_id,
            )
        )
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # Check if team has members
    members_result = await db.execute(
        select(func.count()).select_from(User).where(User.team_id == team_id)
    )
    member_count = members_result.scalar() or 0

    if member_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete team with active members. Remove all members first.",
        )

    await db.delete(team)
    await db.flush()


@router.post("/{team_id}/members", status_code=201)
async def add_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_manager),
    db: AsyncSession = Depends(get_db),
):
    """Add a user to a team (admin/manager only)."""
    # Verify team exists and belongs to current user's org
    team_result = await db.execute(
        select(Team).where(
            and_(
                Team.id == team_id,
                Team.organization_id == current_user.organization_id,
            )
        )
    )
    team = team_result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # Verify user exists and belongs to same org
    user_result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.organization_id == current_user.organization_id,
                User.deleted_at.is_(None),
            )
        )
    )
    target_user = user_result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user is already in a team (assuming one team per user)
    if target_user.team_id and target_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already assigned to another team",
        )

    if target_user.team_id == team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team",
        )

    # Add user to team
    target_user.team_id = team_id
    await db.flush()

    return {"message": f"User added to team successfully"}


@router.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_manager),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from a team (admin/manager only)."""
    # Verify team exists and belongs to current user's org
    team_result = await db.execute(
        select(Team).where(
            and_(
                Team.id == team_id,
                Team.organization_id == current_user.organization_id,
            )
        )
    )
    team = team_result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # Verify user exists and is in this team
    user_result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.organization_id == current_user.organization_id,
                User.team_id == team_id,
                User.deleted_at.is_(None),
            )
        )
    )
    target_user = user_result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this team",
        )

    # Remove user from team
    target_user.team_id = None
    await db.flush()
