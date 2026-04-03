"""
Project and Task models for project management and time allocation.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6", nullable=False)  # hex color

    # Status: active, paused, completed, archived
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Budget
    budget_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # for invoicing
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Client info
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Organization
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    tasks = relationship("Task", back_populates="project", lazy="selectin")
    time_entries = relationship("TimeEntry", back_populates="project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status: todo, in_progress, review, done
    status: Mapped[str] = mapped_column(String(50), default="todo", nullable=False)

    # Priority: low, medium, high, urgent
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)

    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    assignee_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    project = relationship("Project", back_populates="tasks")
    time_entries = relationship("TimeEntry", back_populates="task", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Task {self.title} [{self.status}]>"
