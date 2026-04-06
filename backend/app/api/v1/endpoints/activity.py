"""
Team Activity & Screenshot management API endpoints.
Provides manager team-level activity views and screenshot gallery.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_manager
from app.models.tracking import Screenshot, TimeEntry
from app.models.user import User

# Screenshot storage directory
SCREENSHOTS_DIR = Path("storage/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
from app.schemas.reports import (
    TeamMemberActivity,
    TeamActivityResponse,
    ScreenshotMeta,
    ScreenshotListResponse,
)

router = APIRouter(prefix="/activity", tags=["Activity & Screenshots"])


# ── Team Activity ──


@router.get("/team", response_model=TeamActivityResponse)
async def get_team_activity(
    current_user: User = Depends(get_current_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get real-time activity status of all team members in the organization.
    Manager+ only. Shows who is tracking, their hours today, and current task.
    """
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all users in the same organization
    users_result = await db.execute(
        select(User).where(
            User.organization_id == current_user.organization_id,
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
            # Add live elapsed to today total
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

    # Sort: currently tracking first, then by hours desc
    members.sort(key=lambda m: (-m.is_tracking, -m.today_seconds))

    return TeamActivityResponse(
        members=members,
        total_members=len(members),
        members_tracking=tracking_count,
    )


# ── Screenshots ──


@router.post("/screenshots/upload", status_code=201)
async def upload_screenshot(
    file: UploadFile = File(...),
    time_entry_id: str = Form(...),
    captured_at: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a screenshot captured by the browser Screen Capture API.
    Saves the file to local storage and creates a metadata record.
    """
    # Validate the time entry belongs to this user
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

    # Parse captured_at
    try:
        cap_time = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        cap_time = datetime.now(UTC)

    # Create screenshot record
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


@router.get("/screenshots", response_model=ScreenshotListResponse)
async def list_screenshots(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List screenshot metadata. Employees see own; managers see org.
    Screenshots are stored in MinIO — this returns metadata only.
    """
    query = select(Screenshot)

    # Access control
    if current_user.role == "employee":
        query = query.where(Screenshot.user_id == current_user.id)
    elif user_id:
        query = query.where(Screenshot.user_id == user_id)

    if date_from:
        query = query.where(Screenshot.captured_at >= date_from)
    if date_to:
        query = query.where(Screenshot.captured_at <= date_to)

    query = query.where(Screenshot.is_deleted == False)

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

    screenshots = [
        ScreenshotMeta(
            id=str(s.id),
            user_id=str(s.user_id),
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

    # Only owner or admin can delete
    if str(shot.user_id) != str(current_user.id) and current_user.role not in ("super_admin", "org_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this screenshot")

    shot.is_deleted = True
    await db.flush()
