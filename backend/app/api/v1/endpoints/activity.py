"""
Team Activity & Screenshot management API endpoints.
Provides manager team-level activity views, screenshot gallery, and image serving.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_manager
from app.models.tracking import Screenshot, TimeEntry
from app.models.user import User
from app.schemas.reports import (
    TeamMemberActivity,
    TeamActivityResponse,
    ScreenshotMeta,
    ScreenshotListResponse,
)

# Screenshot storage directory
SCREENSHOTS_DIR = Path("storage/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/activity", tags=["Activity & Screenshots"])


# ═══════════════════════════════════════════════════════════════
# HELPER: Build a subquery of user IDs this person is allowed to see
# ═══════════════════════════════════════════════════════════════

def _visible_user_ids_query(current_user: User):
    """
    Returns a select() of user IDs the current_user is allowed to view.
    - employee: only themselves
    - manager: themselves + employees they created
    - org_admin / super_admin: all users in the org
    """
    if current_user.role == "employee":
        return select(User.id).where(User.id == current_user.id)

    if current_user.role == "manager":
        return select(User.id).where(
            User.organization_id == current_user.organization_id,
            (
                (User.id == current_user.id)
                | (
                    (User.role == "employee")
                    & (User.created_by == current_user.id)
                )
            ),
        )

    # org_admin / super_admin — all in org
    return select(User.id).where(
        User.organization_id == current_user.organization_id,
    )


# ═══════════════════════════════════════════════════════════════
# TEAM ACTIVITY
# ═══════════════════════════════════════════════════════════════

@router.get("/team", response_model=TeamActivityResponse)
async def get_team_activity(
    current_user: User = Depends(get_current_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get real-time activity status of team members.
    - org_admin / super_admin: sees ALL users in the organization.
    - manager: sees only employees THEY created + themselves.
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Fetch visible users
    visible_ids = _visible_user_ids_query(current_user)
    users_result = await db.execute(
        select(User).where(
            User.id.in_(visible_ids),
            User.is_active == True,
        )
    )
    users = users_result.scalars().all()

    members = []
    tracking_count = 0

    for user in users:
        # Get today's total seconds
        today_q = await db.execute(
            select(
                func.coalesce(func.sum(TimeEntry.duration_seconds), 0),
                func.coalesce(func.avg(TimeEntry.activity_percent), 0.0),
            ).where(
                TimeEntry.user_id == user.id,
                TimeEntry.start_time >= today_start,
                TimeEntry.end_time.isnot(None),
            )
        )
        today_row = today_q.first()
        today_secs = int(today_row[0]) if today_row else 0
        avg_activity = round(float(today_row[1]), 1) if today_row else 0.0

        # Check for active entry
        active_result = await db.execute(
            select(TimeEntry).where(
                TimeEntry.user_id == user.id,
                TimeEntry.end_time.is_(None),
            )
        )
        active_entry = active_result.scalar_one_or_none()
        is_tracking = active_entry is not None

        if is_tracking:
            tracking_count += 1
            elapsed = int((now - active_entry.start_time).total_seconds())
            today_secs += elapsed

        members.append(TeamMemberActivity(
            user_id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            is_tracking=is_tracking,
            today_seconds=today_secs,
            active_entry_description=active_entry.description if active_entry else None,
            active_entry_start_time=active_entry.start_time if active_entry else None,
            avg_activity_percent=avg_activity,
        ))

    members.sort(key=lambda m: (-m.is_tracking, -m.today_seconds))

    return TeamActivityResponse(
        members=members,
        total_members=len(members),
        members_tracking=tracking_count,
    )


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT UPLOAD
# ═══════════════════════════════════════════════════════════════

@router.post("/screenshots/upload", status_code=201)
async def upload_screenshot(
    file: UploadFile = File(...),
    time_entry_id: str = Form(...),
    captured_at: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a screenshot captured by the browser Screen Capture API."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.id == uuid.UUID(time_entry_id),
            TimeEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    # Save file to disk
    user_dir = SCREENSHOTS_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    file_path = user_dir / filename

    contents = await file.read()
    file_path.write_bytes(contents)

    try:
        cap_time = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        cap_time = datetime.now(UTC)

    screenshot = Screenshot(
        user_id=current_user.id,
        time_entry_id=uuid.UUID(time_entry_id),
        file_path=str(file_path),
        thumbnail_path=None,
        file_size_bytes=len(contents),
        activity_percent=0.0,
        captured_at=cap_time,
        is_blurred=False,
        is_deleted=False,
    )
    db.add(screenshot)
    await db.flush()

    return {
        "id": str(screenshot.id),
        "file_path": str(file_path),
        "captured_at": cap_time.isoformat(),
        "file_size_bytes": len(contents),
    }


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT IMAGE SERVING  (NEW — this was missing)
# ═══════════════════════════════════════════════════════════════

@router.get("/screenshots/{screenshot_id}/image")
async def get_screenshot_image(
    screenshot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Serve the actual screenshot image file.
    Access control: you can only view images of users you're allowed to see.
    """
    result = await db.execute(
        select(Screenshot).where(
            Screenshot.id == screenshot_id,
            Screenshot.is_deleted == False,
        )
    )
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    # Check permission: is this screenshot's user in the caller's visible set?
    visible_ids = _visible_user_ids_query(current_user)
    perm_check = await db.execute(
        select(func.count()).where(
            User.id == shot.user_id,
            User.id.in_(visible_ids),
        )
    )
    if (perm_check.scalar() or 0) == 0:
        raise HTTPException(status_code=403, detail="You don't have access to this screenshot")

    # Serve the file
    file_path = Path(shot.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type="image/jpeg",
        filename=file_path.name,
    )


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT LIST
# ═══════════════════════════════════════════════════════════════

@router.get("/screenshots", response_model=ScreenshotListResponse)
async def list_screenshots(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List screenshot metadata.
    - employee: own screenshots only
    - manager: own + employees they created
    - org_admin / super_admin: all in the org
    Supports up to 200 per page for full-day timeline views.
    """
    # Use the shared visibility helper
    visible_ids = _visible_user_ids_query(current_user)

    query = select(Screenshot).where(
        Screenshot.user_id.in_(visible_ids),
        Screenshot.is_deleted == False,
    )

    # Optional filter by specific user (must still be in visible set)
    if user_id:
        query = query.where(Screenshot.user_id == user_id)

    if date_from:
        query = query.where(Screenshot.captured_at >= date_from)
    if date_to:
        query = query.where(Screenshot.captured_at <= date_to)

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(Screenshot.captured_at.desc()).offset(offset).limit(per_page)
    )
    shots = result.scalars().all()

    # Batch-load user names for all screenshots in one query
    user_ids = list({s.user_id for s in shots})
    user_map: dict[str, User] = {}
    if user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        for u in users_result.scalars().all():
            user_map[str(u.id)] = u

    screenshots = [
        ScreenshotMeta(
            id=str(s.id),
            user_id=str(s.user_id),
            user_name=f"{user_map[str(s.user_id)].first_name} {user_map[str(s.user_id)].last_name}"
            if str(s.user_id) in user_map
            else None,
            user_email=user_map[str(s.user_id)].email
            if str(s.user_id) in user_map
            else None,
            time_entry_id=str(s.time_entry_id),
            file_path=s.file_path,
            thumbnail_path=s.thumbnail_path,
            activity_percent=s.activity_percent,
            captured_at=s.captured_at,
            is_blurred=s.is_blurred,
            active_app=s.active_app,
            active_window_title=s.active_window_title,
            active_url=s.active_url,
        )
        for s in shots
    ]

    return ScreenshotListResponse(
        screenshots=screenshots,
        total=total,
        page=page,
        per_page=per_page,
    )


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT DELETE
# ═══════════════════════════════════════════════════════════════

@router.delete("/screenshots/{screenshot_id}", status_code=204)
async def delete_screenshot(
    screenshot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a screenshot (mark as deleted)."""
    result = await db.execute(
        select(Screenshot).where(Screenshot.id == screenshot_id)
    )
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    # Check permission
    visible_ids = _visible_user_ids_query(current_user)
    perm_check = await db.execute(
        select(func.count()).where(
            User.id == shot.user_id,
            User.id.in_(visible_ids),
        )
    )
    if (perm_check.scalar() or 0) == 0:
        raise HTTPException(status_code=403, detail="Access denied")

    shot.is_deleted = True
    await db.flush()
