"""
Organization (tenant) model for multi-tenancy support.
"""

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Plan & limits
    plan_type: Mapped[str] = mapped_column(
        String(50), default="free", nullable=False
    )  # free, starter, professional, enterprise
    max_users: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Organization settings stored as JSON
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    # Example settings: {
    #   "screenshot_interval": 300,
    #   "screenshot_blur": false,
    #   "track_urls": true,
    #   "track_apps": true,
    #   "idle_threshold": 300,
    #   "work_schedule": {"start": "09:00", "end": "18:00"},
    #   "timezone": "UTC"
    # }

    # Billing info
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    users = relationship("User", back_populates="organization", lazy="selectin")
    projects = relationship("Project", back_populates="organization", lazy="selectin")
    teams = relationship("Team", back_populates="organization", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.slug})>"
