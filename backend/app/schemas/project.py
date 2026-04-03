"""
Pydantic schemas for Project and Task CRUD.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Project ──
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    color: str = "#3B82F6"
    budget_hours: float | None = None
    hourly_rate: float | None = None
    currency: str = "USD"
    client_name: str | None = None
    client_email: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    status: str | None = None
    budget_hours: float | None = None
    hourly_rate: float | None = None
    client_name: str | None = None
    client_email: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    color: str
    status: str
    budget_hours: float | None
    hourly_rate: float | None
    currency: str
    client_name: str | None
    organization_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Task ──
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    priority: str = "medium"
    estimated_hours: float | None = None
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None
    project_id: uuid.UUID


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    estimated_hours: float | None = None
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None
    sort_order: int | None = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str
    estimated_hours: float | None
    due_date: datetime | None
    project_id: uuid.UUID
    assignee_id: uuid.UUID | None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
