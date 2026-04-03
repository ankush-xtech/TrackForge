"""
Invoice model for billing clients based on tracked hours.
"""

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Invoice generated from tracked project hours."""
    __tablename__ = "invoices"

    # Invoice number (auto-generated, e.g., INV-2024-001)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )

    # Client details (copied at creation for historical accuracy)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Financial
    total_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hourly_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Status: draft, sent, paid, overdue, cancelled
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    # Dates
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Period covered
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # PDF storage
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ({self.status})>"
