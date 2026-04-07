"""
Central API v1 router — assembles all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.organizations import router as organization_router
from app.api.v1.endpoints.projects import router as project_router
from app.api.v1.endpoints.projects import task_router
from app.api.v1.endpoints.teams import router as team_router
from app.api.v1.endpoints.tracking import router as tracking_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.activity import router as activity_router
from app.api.v1.endpoints.users import router as user_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(organization_router)
api_router.include_router(team_router)
api_router.include_router(tracking_router)
api_router.include_router(reports_router)
api_router.include_router(activity_router)
api_router.include_router(project_router)
api_router.include_router(task_router)