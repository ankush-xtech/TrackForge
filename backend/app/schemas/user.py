"""
Pydantic schemas for User CRUD operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    timezone: str = "UTC"
    job_title: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: str = "employee"
    team_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    timezone: str | None = None
    job_title: str | None = None
    avatar_url: str | None = None
    role: str | None = None
    team_id: uuid.UUID | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: str | None
    organization_id: uuid.UUID | None
    team_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
