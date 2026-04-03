"""
Diagnostic script to test DB connectivity and registration endpoint.
Run from the backend/ directory:  python test_register.py
"""

import asyncio
import sys


async def test_db_connection():
    """Test 1: Can we connect to PostgreSQL?"""
    print("=" * 60)
    print("TEST 1: Database Connectivity")
    print("=" * 60)
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"  DB URL: postgresql+asyncpg://{settings.POSTGRES_USER}:****@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
            row = result.scalar()
            print(f"  SELECT 1 returned: {row}")
            print("  ✅ Database connection: OK")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"  ❌ Database connection FAILED: {e}")
        return False


async def test_tables_exist():
    """Test 2: Do the required tables exist?"""
    print("\n" + "=" * 60)
    print("TEST 2: Tables Existence")
    print("=" * 60)
    try:
        from app.core.config import get_settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        settings = get_settings()
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result.fetchall()]
            print(f"  Found {len(tables)} tables: {', '.join(tables)}")

            required = {"users", "organizations", "teams", "projects", "tasks"}
            missing = required - set(tables)
            if missing:
                print(f"  ❌ Missing tables: {missing}")
                return False
            else:
                print("  ✅ All required tables exist")
                return True
        await engine.dispose()
    except Exception as e:
        print(f"  ❌ Error checking tables: {e}")
        return False


async def test_model_imports():
    """Test 3: Do all model imports resolve correctly?"""
    print("\n" + "=" * 60)
    print("TEST 3: Model Imports & Mapper Configuration")
    print("=" * 60)
    try:
        import app.models  # This triggers all model imports
        from app.models.user import User
        from app.models.organization import Organization
        from app.models.team import Team
        from app.models.project import Project, Task
        from app.models.tracking import TimeEntry, Screenshot, ActivityLog, AppUsage
        from app.models.attendance import Attendance, GpsLocation
        from app.models.invoice import Invoice
        print("  ✅ All model imports: OK")

        # Verify mapper is configured (triggers relationship resolution)
        from sqlalchemy import inspect
        mapper = inspect(User)
        rels = [r.key for r in mapper.relationships]
        print(f"  User relationships resolved: {rels}")
        print("  ✅ Mapper configuration: OK")
        return True
    except Exception as e:
        print(f"  ❌ Model import/mapper FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_password_hashing():
    """Test 4: Does bcrypt/passlib work?"""
    print("\n" + "=" * 60)
    print("TEST 4: Password Hashing (bcrypt + passlib)")
    print("=" * 60)
    try:
        from app.core.security import hash_password, verify_password
        hashed = hash_password("TestPassword123")
        print(f"  Hashed: {hashed[:40]}...")
        verified = verify_password("TestPassword123", hashed)
        print(f"  Verify correct password: {verified}")
        wrong = verify_password("WrongPassword", hashed)
        print(f"  Verify wrong password: {wrong}")
        if verified and not wrong:
            print("  ✅ Password hashing: OK")
            return True
        else:
            print("  ❌ Password hashing logic error")
            return False
    except Exception as e:
        print(f"  ❌ Password hashing FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_registration():
    """Test 5: Full registration flow (creates a real user in DB)."""
    print("\n" + "=" * 60)
    print("TEST 5: Registration Flow (end-to-end)")
    print("=" * 60)
    try:
        from app.core.database import async_session_factory
        from app.services.auth_service import register_user
        from app.schemas.auth import RegisterRequest
        from sqlalchemy import text

        # Clean up any previous test user
        async with async_session_factory() as session:
            await session.execute(
                text("DELETE FROM users WHERE email = 'test_diag@example.com'")
            )
            await session.execute(
                text("DELETE FROM organizations WHERE slug = 'test-diag-org'")
            )
            await session.commit()

        # Attempt registration
        data = RegisterRequest(
            email="test_diag@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
            organization_name="Test Diag Org",
        )

        async with async_session_factory() as session:
            try:
                result = await register_user(session, data)
                await session.commit()
                print(f"  Access token: {result.access_token[:30]}...")
                print(f"  Refresh token: {result.refresh_token[:30]}...")
                print(f"  Expires in: {result.expires_in}s")
                print("  ✅ Registration: OK")

                # Cleanup
                await session.execute(
                    text("DELETE FROM users WHERE email = 'test_diag@example.com'")
                )
                await session.execute(
                    text("DELETE FROM organizations WHERE slug LIKE 'test-diag-org%'")
                )
                await session.commit()
                print("  (Cleaned up test data)")
                return True
            except Exception as e:
                await session.rollback()
                raise e

    except Exception as e:
        print(f"  ❌ Registration FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n🔍 TrackForge Registration Diagnostic\n")

    results = {}
    results["db"] = await test_db_connection()
    if not results["db"]:
        print("\n⛔ Database connection failed — fix this first before other tests.")
        sys.exit(1)

    results["tables"] = await test_tables_exist()
    results["models"] = await test_model_imports()
    results["bcrypt"] = await test_password_hashing()

    if all([results["tables"], results["models"], results["bcrypt"]]):
        results["register"] = await test_registration()
    else:
        print("\n⛔ Skipping registration test — prerequisite tests failed.")
        results["register"] = False

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")

    if all(results.values()):
        print("\n🎉 All tests passed! Registration should work now.")
        print("   Restart your server: uvicorn app.main:app --reload")
    else:
        print("\n⚠️  Some tests failed — check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
