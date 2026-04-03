"""
Time tracking API endpoints — used by the desktop agent and web dashboard.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
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
    TimeEntryStop,
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
        start_time=data.start_time,
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

    entry.end_time = data.end_time
    entry.duration_seconds = int((data.end_time - entry.start_time).total_seconds())
    await db.flush()
    return entry


@router.get("/time-entries", response_model=list[TimeEntryResponse])
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
    """List time entries with filters. Employees see their own; managers see their team."""
    query = select(TimeEntry)

    # Access control
    if current_user.role == "employee":
        query = query.where(TimeEntry.user_id == current_user.id)
    elif user_id:
        query = query.where(TimeEntry.user_id == user_id)

    # Filters
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
    return result.scalars().all()


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
    return {"status": "accepted", "activity_logs": len(payload.activity_logs), "app_usage": len(payload.app_usage)}
