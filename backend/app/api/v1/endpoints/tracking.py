"""
Time tracking API endpoints — used by the desktop agent and web dashboard.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.tracking import ActivityLog, AppUsage, TimeEntry
from app.models.user import User
from app.schemas.tracking import (
    ActivityLogCreate,
    ActivityLogResponse,
    AgentSyncPayload,
    AppUsageCreate,
    AppUsageResponse,
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntryListItem,
    TimeEntryStop,
    TimeEntryUpdate,
    TrackingSummary,
)


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

router = APIRouter(prefix="/tracking", tags=["Time Tracking"])


# ── Time Entries ──


@router.post("/time-entries", response_model=TimeEntryResponse, status_code=201)
async def start_time_entry(
    data: TimeEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new time tracking session."""
    # Check if there's already an active (running) entry
    active = await db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.end_time.is_(None),
        )
    )
    if active.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="You already have an active time entry. Stop it first.",
        )

    entry = TimeEntry(
        user_id=current_user.id,
        project_id=data.project_id,
        task_id=data.task_id,
        start_time=data.start_time or datetime.now(UTC),
        description=data.description,
        is_manual=data.is_manual,
    )
    db.add(entry)
    await db.flush()
    return entry


@router.patch("/time-entries/{entry_id}/stop", response_model=TimeEntryResponse)
async def stop_time_entry(
    entry_id: uuid.UUID,
    data: TimeEntryStop,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop a running time entry."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    if entry.end_time is not None:
        raise HTTPException(status_code=400, detail="Time entry is already stopped")

    end = data.end_time or datetime.now(UTC)
    entry.end_time = end
    entry.duration_seconds = int((end - entry.start_time).total_seconds())
    await db.flush()
    return entry


@router.post("/time-entries/stop-active", status_code=200)
async def stop_active_entry(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stop whatever entry is currently running for this user.
    Designed for browser beforeunload / sendBeacon — works as a POST
    so navigator.sendBeacon can call it when the tab or browser closes.
    """
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.end_time.is_(None),
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return {"stopped": False, "detail": "No active entry"}

    end = datetime.now(UTC)
    entry.end_time = end
    entry.duration_seconds = int((end - entry.start_time).total_seconds())
    await db.flush()
    return {"stopped": True, "entry_id": str(entry.id)}


@router.patch("/time-entries/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    entry_id: uuid.UUID,
    data: TimeEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a time entry (description, project, task)."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    # Recalculate duration if times changed
    if entry.end_time and entry.start_time:
        entry.duration_seconds = int(
            (entry.end_time - entry.start_time).total_seconds()
        )

    await db.flush()
    return entry


@router.delete("/time-entries/{entry_id}", status_code=204)
async def delete_time_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a time entry."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    await db.delete(entry)
    await db.flush()


@router.get("/time-entries", response_model=list[TimeEntryListItem])
async def list_time_entries(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    project_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List time entries with filters.
    - employee: own entries only
    - manager: own + employees they created
    - org_admin / super_admin: all in the org
    """
    # Use shared visibility scoping
    visible_ids = _visible_user_ids_query(current_user)
    query = select(TimeEntry).where(TimeEntry.user_id.in_(visible_ids))

    # Optional filter by specific user (must still be within visible set)
    if user_id:
        query = query.where(TimeEntry.user_id == user_id)

    # Date & project filters
    if date_from:
        query = query.where(TimeEntry.start_time >= date_from)
    if date_to:
        query = query.where(TimeEntry.start_time <= date_to)
    if project_id:
        query = query.where(TimeEntry.project_id == project_id)

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(TimeEntry.start_time.desc()).offset(offset).limit(per_page)
    )
    entries = result.scalars().all()

    # Batch-load user names for all entries
    entry_user_ids = list({e.user_id for e in entries})
    user_map: dict[str, User] = {}
    if entry_user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(entry_user_ids))
        )
        for u in users_result.scalars().all():
            user_map[str(u.id)] = u

    # Build enriched response with user names
    return [
        TimeEntryListItem(
            id=e.id,
            user_id=e.user_id,
            user_name=f"{user_map[str(e.user_id)].first_name} {user_map[str(e.user_id)].last_name}"
            if str(e.user_id) in user_map
            else None,
            user_email=user_map[str(e.user_id)].email
            if str(e.user_id) in user_map
            else None,
            project_id=e.project_id,
            task_id=e.task_id,
            start_time=e.start_time,
            end_time=e.end_time,
            duration_seconds=e.duration_seconds,
            activity_percent=e.activity_percent,
            mouse_events=e.mouse_events,
            keyboard_events=e.keyboard_events,
            is_manual=e.is_manual,
            description=e.description,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/time-entries/active", response_model=TimeEntryResponse | None)
async def get_active_entry(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the currently running time entry (if any)."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.end_time.is_(None),
        )
    )
    return result.scalar_one_or_none()


# ── Summary / Stats ──


@router.get("/summary", response_model=TrackingSummary)
async def get_tracking_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get time tracking summary (today, this week, this month)."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    base_q = select(
        func.coalesce(func.sum(TimeEntry.duration_seconds), 0)
    ).where(TimeEntry.user_id == current_user.id)

    today_result = await db.execute(
        base_q.where(TimeEntry.start_time >= today_start)
    )
    today_seconds = today_result.scalar() or 0

    week_result = await db.execute(
        base_q.where(TimeEntry.start_time >= week_start)
    )
    week_seconds = week_result.scalar() or 0

    month_result = await db.execute(
        base_q.where(TimeEntry.start_time >= month_start)
    )
    month_seconds = month_result.scalar() or 0

    # Count entries today
    entries_count_result = await db.execute(
        select(func.count(TimeEntry.id)).where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.start_time >= today_start,
        )
    )
    entries_today = entries_count_result.scalar() or 0

    # Average activity percent (from completed entries today)
    activity_result = await db.execute(
        select(func.coalesce(func.avg(TimeEntry.activity_percent), 0.0)).where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.start_time >= today_start,
            TimeEntry.end_time.isnot(None),
        )
    )
    avg_activity = round(float(activity_result.scalar() or 0), 1)

    # Check for currently running entry
    active_result = await db.execute(
        select(TimeEntry.id, TimeEntry.start_time).where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.end_time.is_(None),
        )
    )
    active_row = active_result.first()
    is_tracking = active_row is not None

    # If currently tracking, add elapsed time to today's total
    if is_tracking:
        active_elapsed = int((now - active_row.start_time).total_seconds())
        today_seconds += active_elapsed

    return TrackingSummary(
        today_seconds=today_seconds,
        week_seconds=week_seconds,
        month_seconds=month_seconds,
        entries_today=entries_today,
        avg_activity_percent=avg_activity,
        is_tracking=is_tracking,
        active_entry_id=str(active_row.id) if active_row else None,
    )


# ── Agent Sync (bulk data upload from desktop agent) ──


@router.post("/sync", status_code=202)
async def sync_agent_data(
    payload: AgentSyncPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk sync tracked data from the desktop agent."""
    # Process activity logs
    for log_data in payload.activity_logs:
        log = ActivityLog(
            user_id=current_user.id,
            time_entry_id=log_data.time_entry_id,
            interval_start=log_data.interval_start,
            interval_end=log_data.interval_end,
            mouse_events=log_data.mouse_events,
            keyboard_events=log_data.keyboard_events,
            mouse_distance_px=log_data.mouse_distance_px,
            scroll_events=log_data.scroll_events,
            click_events=log_data.click_events,
            activity_percent=log_data.activity_percent,
        )
        db.add(log)

    # Process app usage
    for usage_data in payload.app_usage:
        usage = AppUsage(
            user_id=current_user.id,
            time_entry_id=usage_data.time_entry_id,
            app_name=usage_data.app_name,
            window_title=usage_data.window_title,
            url=usage_data.url,
            duration_seconds=usage_data.duration_seconds,
            category=usage_data.category,
            started_at=usage_data.started_at,
            ended_at=usage_data.ended_at,
        )
        db.add(usage)

    await db.flush()
    return {
        "status": "accepted",
        "activity_logs": len(payload.activity_logs),
        "app_usage": len(payload.app_usage),
    }
