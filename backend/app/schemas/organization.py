"""
Pydantic schemas for Organization CRUD.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    website: str | None = None
    billing_email: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    website: str | None = None
    logo_url: str | None = None
    billing_email: str | None = None
    billing_address: str | None = None
    settings: dict | None = None


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_url: str | None
    website: str | None
    plan_type: str
    max_users: int
    is_active: bool
    settings: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
