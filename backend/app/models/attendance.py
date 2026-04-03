"""
Attendance and GPS tracking models.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Attendance(Base, UUIDMixin, TimestampMixin):
    """Daily attendance record per employee."""
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_attendance_user_date"),
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    total_tracked_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_active_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_idle_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status: present, absent, late, half_day, leave, holiday
    status: Mapped[str] = mapped_column(String(50), default="present", nullable=False)

    # Overtime
    overtime_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Attendance {self.user_id} on {self.date} [{self.status}]>"


class GpsLocation(Base, UUIDMixin, TimestampMixin):
    """GPS location data captured during tracked time."""
    __tablename__ = "gps_locations"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    time_entry_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("time_entries.id"), nullable=True
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Reverse geocoded address (optional, populated async)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<GpsLocation ({self.latitude}, {self.longitude})>"
