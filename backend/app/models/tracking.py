"""
Core tracking models: TimeEntry, Screenshot, ActivityLog, AppUsage.
These are the heart of the employee monitoring system.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class TimeEntry(Base, UUIDMixin, TimestampMixin):
    """A continuous block of tracked work time."""
    __tablename__ = "time_entries"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    task_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Activity metrics (aggregated from activity_logs)
    activity_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mouse_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keyboard_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Manual entry vs tracked by agent
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")
    task = relationship("Task", back_populates="time_entries")
    screenshots = relationship("Screenshot", back_populates="time_entry", lazy="selectin")
    activity_logs = relationship("ActivityLog", back_populates="time_entry", lazy="selectin")
    app_usage = relationship("AppUsage", back_populates="time_entry", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TimeEntry {self.user_id} {self.start_time}>"


class Screenshot(Base, UUIDMixin, TimestampMixin):
    """Periodic screenshot captured by the desktop agent."""
    __tablename__ = "screenshots"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    time_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("time_entries.id"), nullable=False, index=True
    )

    # Storage paths (MinIO/S3 keys)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Metadata
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activity_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Privacy
    is_blurred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Active window info at capture time
    active_app: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active_window_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    user = relationship("User", back_populates="screenshots")
    time_entry = relationship("TimeEntry", back_populates="screenshots")

    def __repr__(self) -> str:
        return f"<Screenshot {self.user_id} at {self.captured_at}>"


class ActivityLog(Base, UUIDMixin, TimestampMixin):
    """Periodic activity sample (mouse/keyboard counts per interval)."""
    __tablename__ = "activity_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    time_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("time_entries.id"), nullable=False, index=True
    )

    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    mouse_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keyboard_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mouse_distance_px: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scroll_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    click_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Calculated activity percentage (0-100)
    activity_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    time_entry = relationship("TimeEntry", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog {self.activity_percent}% at {self.interval_start}>"


class AppUsage(Base, UUIDMixin, TimestampMixin):
    """Tracks which applications and websites the employee used."""
    __tablename__ = "app_usage"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    time_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("time_entries.id"), nullable=False, index=True
    )

    app_name: Mapped[str] = mapped_column(String(255), nullable=False)
    window_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # for browsers
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Category: productive, unproductive, neutral, uncategorized
    category: Mapped[str] = mapped_column(String(50), default="uncategorized", nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    time_entry = relationship("TimeEntry", back_populates="app_usage")

    def __repr__(self) -> str:
        return f"<AppUsage {self.app_name} ({self.duration_seconds}s)>"
