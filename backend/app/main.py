"""
FastAPI application entry point.
"""

import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
import app.models  # noqa: F401 — register all models with SQLAlchemy mapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Employee Activity Tracking API — WebWork Clone",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ── DEBUG: Catch ALL unhandled exceptions and return details in response ──
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    """Return full traceback in response during development."""
    tb = traceback.format_exc()
    print(f"\n{'='*60}\nUNHANDLED EXCEPTION on {request.method} {request.url.path}\n{'='*60}")
    print(tb)
    print(f"{'='*60}\n")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": tb,
        },
    )


# CORS only — removed custom middleware temporarily for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/debug/db")
async def debug_db():
    """Debug endpoint to check DB connectivity and tables."""
    from sqlalchemy import text
    from app.core.database import async_session_factory
    try:
        async with async_session_factory() as session:
            # Check which database we're connected to
            db_result = await session.execute(text("SELECT current_database()"))
            db_name = db_result.scalar()

            # Check tables
            tables_result = await session.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in tables_result.fetchall()]

            return {
                "database": db_name,
                "database_url_db": settings.POSTGRES_DB,
                "tables_count": len(tables),
                "tables": tables,
                "has_users": "users" in tables,
            }
    except Exception as e:
        return {"error": str(e)}
