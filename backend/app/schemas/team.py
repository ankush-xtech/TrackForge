"""
Pydantic schemas for Team CRUD operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    manager_id: uuid.UUID | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    manager_id: uuid.UUID | None = None


class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    organization_id: uuid.UUID
    manager_id: uuid.UUID | None
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class TeamListResponse(BaseModel):
    teams: list[TeamResponse]
    total: int
    page: int = 1
    per_page: int = 20
