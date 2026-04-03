"""
Team/Department model for organizing employees within an organization.
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Team(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Organization
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Manager of this team (use_alter=True breaks circular FK with users)
    manager_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", use_alter=True, name="fk_teams_manager_id"),
        nullable=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    manager = relationship("User", foreign_keys=[manager_id], lazy="joined")
    members = relationship("User", back_populates="team", foreign_keys="User.team_id")

    def __repr__(self) -> str:
        return f"<Team {self.name}>"
