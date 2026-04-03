"""
Import all models so SQLAlchemy's mapper can resolve string-based relationships.
Without these imports, relationships like User.team → "Team" would fail
because the target model class was never registered with the mapper.
"""

from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.project import Project, Task  # noqa: F401
from app.models.tracking import ActivityLog, AppUsage, Screenshot, TimeEntry  # noqa: F401
from app.models.attendance import Attendance, GpsLocation  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
