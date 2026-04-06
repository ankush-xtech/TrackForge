"""
Pydantic schemas for reports and analytics.
"""

from datetime import datetime

from pydantic import BaseModel


# ── Daily Breakdown ──
class DailyBreakdownItem(BaseModel):
    date: str
    total_seconds: int
    entries: int
    avg_activity_percent: float


class DailyBreakdown(BaseModel):
    days: list[DailyBreakdownItem]
    total_seconds: int
    total_entries: int


# ── Weekly Report ──
class WeeklyReport(BaseModel):
    this_week_seconds: int
    this_week_entries: int
    this_week_avg_activity: float
    last_week_seconds: int
    last_week_entries: int
    last_week_avg_activity: float
    change_percent: float


# ── Productivity Trend ──
class ProductivityTrendItem(BaseModel):
    date: str
    avg_activity_percent: float
    total_seconds: int


class ProductivityTrend(BaseModel):
    days: list[ProductivityTrendItem]
    period_days: int


# ── App Usage Summary ──
class AppUsageSummaryItem(BaseModel):
    app_name: str
    category: str
    total_seconds: int
    session_count: int


class AppUsageSummary(BaseModel):
    apps: list[AppUsageSummaryItem]
    period_start: datetime
    period_end: datetime


# ── Team Activity (for manager view) ──
class TeamMemberActivity(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    role: str
    is_tracking: bool
    today_seconds: int
    active_entry_description: str | None = None
    active_entry_start_time: datetime | None = None
    avg_activity_percent: float = 0.0


class TeamActivityResponse(BaseModel):
    members: list[TeamMemberActivity]
    total_members: int
    members_tracking: int


# ── Screenshot Metadata ──
class ScreenshotMeta(BaseModel):
    id: str
    user_id: str
    time_entry_id: str
    file_path: str
    thumbnail_path: str | None
    activity_percent: float
    captured_at: datetime
    is_blurred: bool
    active_app: str | None
    active_window_title: str | None
    active_url: str | None


class ScreenshotListResponse(BaseModel):
    screenshots: list[ScreenshotMeta]
    total: int
    page: int
    per_page: int
