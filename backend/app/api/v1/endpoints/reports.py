"""
Reports & Analytics API endpoints.
Provides daily/weekly breakdowns, productivity trends, and app usage analytics.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_manager
from app.models.tracking import ActivityLog, AppUsage, TimeEntry
from app.models.user import User
from app.schemas.reports import (
    DailyBreakdown,
    DailyBreakdownItem,
    WeeklyReport,
    ProductivityTrend,
    ProductivityTrendItem,
    AppUsageSummary,
    AppUsageSummaryItem,
)

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/daily-breakdown", response_model=DailyBreakdown)
async def get_daily_breakdown(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get day-by-day breakdown of hours tracked over a date range."""
    now = datetime.now(UTC)
    if not date_from:
        date_from = now - timedelta(days=6)
    if not date_to:
        date_to = now

    # Access control
    target_user_id = current_user.id
    if user_id and current_user.role in ("super_admin", "org_admin", "manager"):
        target_user_id = user_id

    result = await db.execute(
        select(
            cast(TimeEntry.start_time, Date).label("day"),
            func.coalesce(func.sum(TimeEntry.duration_seconds), 0).label("total_seconds"),
            func.count(TimeEntry.id).label("entries"),
            func.coalesce(func.avg(TimeEntry.activity_percent), 0.0).label("avg_activity"),
        )
        .where(
            TimeEntry.user_id == target_user_id,
            TimeEntry.start_time >= date_from,
            TimeEntry.start_time <= date_to,
            TimeEntry.end_time.isnot(None),
        )
        .group_by(cast(TimeEntry.start_time, Date))
        .order_by(cast(TimeEntry.start_time, Date))
    )
    rows = result.all()

    days = []
    total_seconds = 0
    total_entries = 0
    for row in rows:
        secs = int(row.total_seconds)
        total_seconds += secs
        total_entries += row.entries
        days.append(DailyBreakdownItem(
            date=str(row.day),
            total_seconds=secs,
            entries=row.entries,
            avg_activity_percent=round(float(row.avg_activity), 1),
        ))

    return DailyBreakdown(
        days=days,
        total_seconds=total_seconds,
        total_entries=total_entries,
    )


@router.get("/weekly", response_model=WeeklyReport)
async def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a summary report for the current week vs last week."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_week_start = today_start - timedelta(days=today_start.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start

    base_q = select(
        func.coalesce(func.sum(TimeEntry.duration_seconds), 0),
        func.count(TimeEntry.id),
        func.coalesce(func.avg(TimeEntry.activity_percent), 0.0),
    ).where(
        TimeEntry.user_id == current_user.id,
        TimeEntry.end_time.isnot(None),
    )

    this_week = await db.execute(
        base_q.where(TimeEntry.start_time >= this_week_start)
    )
    tw = this_week.first()

    last_week = await db.execute(
        base_q.where(
            TimeEntry.start_time >= last_week_start,
            TimeEntry.start_time < last_week_end,
        )
    )
    lw = last_week.first()

    tw_secs = int(tw[0]) if tw else 0
    lw_secs = int(lw[0]) if lw else 0

    change_percent = 0.0
    if lw_secs > 0:
        change_percent = round(((tw_secs - lw_secs) / lw_secs) * 100, 1)

    return WeeklyReport(
        this_week_seconds=tw_secs,
        this_week_entries=int(tw[1]) if tw else 0,
        this_week_avg_activity=round(float(tw[2]), 1) if tw else 0.0,
        last_week_seconds=lw_secs,
        last_week_entries=int(lw[1]) if lw else 0,
        last_week_avg_activity=round(float(lw[2]), 1) if lw else 0.0,
        change_percent=change_percent,
    )


@router.get("/productivity-trend", response_model=ProductivityTrend)
async def get_productivity_trend(
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily productivity (activity %) trend over the past N days."""
    now = datetime.now(UTC)
    start = now - timedelta(days=days)

    result = await db.execute(
        select(
            cast(TimeEntry.start_time, Date).label("day"),
            func.coalesce(func.avg(TimeEntry.activity_percent), 0.0).label("avg_activity"),
            func.coalesce(func.sum(TimeEntry.duration_seconds), 0).label("total_seconds"),
        )
        .where(
            TimeEntry.user_id == current_user.id,
            TimeEntry.start_time >= start,
            TimeEntry.end_time.isnot(None),
        )
        .group_by(cast(TimeEntry.start_time, Date))
        .order_by(cast(TimeEntry.start_time, Date))
    )
    rows = result.all()

    items = [
        ProductivityTrendItem(
            date=str(row.day),
            avg_activity_percent=round(float(row.avg_activity), 1),
            total_seconds=int(row.total_seconds),
        )
        for row in rows
    ]

    return ProductivityTrend(days=items, period_days=days)


@router.get("/app-usage", response_model=AppUsageSummary)
async def get_app_usage_summary(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated app/website usage summary."""
    now = datetime.now(UTC)
    if not date_from:
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if not date_to:
        date_to = now

    result = await db.execute(
        select(
            AppUsage.app_name,
            AppUsage.category,
            func.sum(AppUsage.duration_seconds).label("total_seconds"),
            func.count(AppUsage.id).label("session_count"),
        )
        .where(
            AppUsage.user_id == current_user.id,
            AppUsage.started_at >= date_from,
            AppUsage.started_at <= date_to,
        )
        .group_by(AppUsage.app_name, AppUsage.category)
        .order_by(func.sum(AppUsage.duration_seconds).desc())
        .limit(20)
    )
    rows = result.all()

    apps = [
        AppUsageSummaryItem(
            app_name=row.app_name,
            category=row.category,
            total_seconds=int(row.total_seconds),
            session_count=row.session_count,
        )
        for row in rows
    ]

    return AppUsageSummary(apps=apps, period_start=date_from, period_end=date_to)
