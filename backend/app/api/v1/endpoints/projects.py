"""
Project and Task management API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_manager, get_current_user
from app.models.project import Project, Task
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_manager),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project (manager+ only)."""
    project = Project(
        **data.model_dump(),
        organization_id=current_user.organization_id,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    status: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects in the organization."""
    query = select(Project).where(
        Project.organization_id == current_user.organization_id,
        Project.deleted_at.is_(None),
    )
    if status:
        query = query.where(Project.status == status)

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(Project.created_at.desc()).offset(offset).limit(per_page)
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_manager),
    db: AsyncSession = Depends(get_db),
):
    """Update a project (manager+ only)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    return project


# ── Tasks ──

task_router = APIRouter(prefix="/tasks", tags=["Tasks"])


@task_router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task within a project."""
    task = Task(**data.model_dump())
    db.add(task)
    await db.flush()
    return task


@task_router.get("", response_model=list[TaskResponse])
async def list_tasks(
    project_id: uuid.UUID,
    status: str | None = None,
    assignee_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tasks for a project."""
    query = select(Task).where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)

    result = await db.execute(query.order_by(Task.sort_order, Task.created_at.desc()))
    return result.scalars().all()


@task_router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task (status, assignee, priority, etc.)."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.flush()
    return task
