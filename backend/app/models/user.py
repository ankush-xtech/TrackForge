"""
User model with role-based access control.
"""

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    # Auth fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Role: super_admin, org_admin, manager, employee
    role: Mapped[str] = mapped_column(String(50), default="employee", nullable=False)

    # Organization (tenant)
    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    # Team
    team_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )

    # Who invited/created this user (NULL for self-registered org creators)
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Notification preferences (stored as JSON in settings)
    notification_settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    time_entries = relationship("TimeEntry", back_populates="user", lazy="selectin")
    screenshots = relationship("Screenshot", back_populates="user", lazy="selectin")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
