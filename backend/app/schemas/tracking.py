"""
Pydantic schemas for time tracking, screenshots, and activity data.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Time Entry ──
class TimeEntryCreate(BaseModel):
    project_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    start_time: datetime
    description: str | None = None
    is_manual: bool = False


class TimeEntryStop(BaseModel):
    end_time: datetime


class TimeEntryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None
    task_id: uuid.UUID | None
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int
    activity_percent: float
    mouse_events: int
    keyboard_events: int
    is_manual: bool
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Screenshot ──
class ScreenshotCreate(BaseModel):
    time_entry_id: uuid.UUID
    captured_at: datetime
    activity_percent: float = 0.0
    active_app: str | None = None
    active_window_title: str | None = None
    active_url: str | None = None
    is_blurred: bool = False


class ScreenshotResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    time_entry_id: uuid.UUID
    file_path: str
    thumbnail_path: str | None
    activity_percent: float
    captured_at: datetime
    is_blurred: bool
    active_app: str | None
    active_window_title: str | None

    model_config = {"from_attributes": True}


# ── Activity Log ──
class ActivityLogCreate(BaseModel):
    time_entry_id: uuid.UUID
    interval_start: datetime
    interval_end: datetime
    mouse_events: int = 0
    keyboard_events: int = 0
    mouse_distance_px: int = 0
    scroll_events: int = 0
    click_events: int = 0
    activity_percent: float = Field(ge=0.0, le=100.0)


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    time_entry_id: uuid.UUID
    interval_start: datetime
    interval_end: datetime
    mouse_events: int
    keyboard_events: int
    activity_percent: float

    model_config = {"from_attributes": True}


# ── App Usage ──
class AppUsageCreate(BaseModel):
    time_entry_id: uuid.UUID
    app_name: str
    window_title: str | None = None
    url: str | None = None
    duration_seconds: int = 0
    category: str = "uncategorized"
    started_at: datetime
    ended_at: datetime | None = None


class AppUsageResponse(BaseModel):
    id: uuid.UUID
    app_name: str
    window_title: str | None
    url: str | None
    duration_seconds: int
    category: str
    started_at: datetime

    model_config = {"from_attributes": True}


# ── Bulk Sync (for desktop agent to send batched data) ──
class AgentSyncPayload(BaseModel):
    """Bulk payload from the desktop agent containing all tracked data for a period."""
    activity_logs: list[ActivityLogCreate] = []
    app_usage: list[AppUsageCreate] = []
    # Screenshot binary data is sent separately via multipart upload
