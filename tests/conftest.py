"""Pytest fixtures.

Database isolation: integration tests run against a dedicated ``opsdesk_test``
database so destructive fixtures (e.g. ``clean_sync_data``) can never wipe the
development database that holds real imported data. The test database is
created on demand and its schema is managed via ``Base.metadata.create_all``.
"""
from __future__ import annotations

import asyncio
import os
import random
from datetime import datetime, timedelta

_TEST_DB_URL = "postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test"


def _setup_test_database() -> bool:
    """Point DATABASE_URL at opsdesk_test if PostgreSQL is reachable.

    Must run before app modules are imported (the engine is created at import
    time). Returns whether PostgreSQL is available.
    """
    import asyncpg  # noqa: PLC0415

    from app.config import settings  # noqa: PLC0415

    async def _prepare() -> bool:
        admin_dsn = settings.database_url.replace("+asyncpg", "").rsplit("/", 1)[0] + "/postgres"
        try:
            conn = await asyncpg.connect(admin_dsn)
        except (OSError, asyncpg.PostgresError):
            return False
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = 'opsdesk_test'"
            )
            if not exists:
                await conn.execute("CREATE DATABASE opsdesk_test")
        finally:
            await conn.close()
        return True

    available = asyncio.run(_prepare())
    if available:
        os.environ["DATABASE_URL"] = _TEST_DB_URL
        # settings is already instantiated by the import above; mutate it so
        # the engine (created on app.db.session import) targets the test DB.
        settings.database_url = _TEST_DB_URL
    return available


DB_AVAILABLE = _setup_test_database()

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.models import OpsInviteToken, OpsRepo, OpsSession, OpsSessionChat, OpsUser  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.ops.deps import get_current_user  # noqa: E402
from app.ops.security import generate_invite_token, hash_token  # noqa: E402


def _random_username() -> str:
    """Return a unique username for this test run."""
    import uuid

    return f"tester-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP test client."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True, scope="session")
async def _create_test_schema():
    """Create all tables in the test database once per session."""
    if DB_AVAILABLE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    yield


@pytest.fixture(autouse=True)
async def _reset_engine():
    """Dispose the async engine before each test to avoid cross-event-loop connection reuse."""
    await engine.dispose()
    yield


@pytest.fixture
async def clean_sync_data():
    """Remove all synced repos and cascading children before a test.

    Safe to delete broadly: this only runs against the opsdesk_test database.
    """
    from sqlalchemy import delete

    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo))
        await db.commit()
    yield
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo))
        await db.commit()


@pytest.fixture
async def seeded_maintainer():
    """Create a maintainer user with an unused invite token and a plaintext token."""
    plaintext_invite = generate_invite_token()
    username = _random_username()
    async with AsyncSessionLocal() as db:
        user = OpsUser(username=username, role="maintainer")
        db.add(user)
        await db.flush()

        invite = OpsInviteToken(
            token=hash_token(plaintext_invite),
            role="maintainer",
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db.add(invite)
        await db.commit()

        yield {
            "user": user,
            "plaintext_invite": plaintext_invite,
        }

        # Cleanup
        async with AsyncSessionLocal() as cleanup_db:
            from sqlalchemy import delete

            await cleanup_db.execute(
                delete(OpsSession).where(OpsSession.user_id == user.id)
            )
            await cleanup_db.execute(
                delete(OpsInviteToken).where(
                    OpsInviteToken.token == hash_token(plaintext_invite)
                )
            )
            await cleanup_db.execute(
                delete(OpsSessionChat).where(OpsSessionChat.user_id == user.id)
            )
            await cleanup_db.execute(delete(OpsUser).where(OpsUser.id == user.id))
            await cleanup_db.commit()


@pytest.fixture
def override_auth_maintainer():
    """Override auth dependency with a test maintainer."""
    from functools import wraps

    from app.db.models import OpsUser

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000001",
        username="admin",
        role="maintainer",
    )

    @wraps(get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def override_auth_viewer():
    """Override auth dependency with a test viewer."""
    from functools import wraps

    from app.db.models import OpsUser

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000002",
        username="viewer",
        role="viewer",
    )

    @wraps(get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def sample_sync_payload():
    """Return a deterministic sample sync payload dict."""
    import uuid

    suffix = uuid.uuid4().hex[:8]
    github_repo_id = random.randint(1, 2_147_483_647)
    return {
        "repo": {
            "owner": "acme",
            "name": f"ios-smoke-{suffix}",
            "full_name": f"acme/ios-smoke-{suffix}",
            "github_repo_id": github_repo_id,
            "default_branch": "main",
        },
        "issues": [
            {
                "number": 1,
                "title": "登录页面闪退",
                "state": "open",
                "labels": ["bug", "ios"],
                "module_tag": "auth",
                "author": "dev-a",
                "html_url": "https://github.com/acme/ios-smoke/issues/1",
                "created_at": "2026-07-17T09:00:00Z",
                "updated_at": "2026-07-17T09:00:00Z",
            }
        ],
        "pull_requests": [
            {
                "number": 2,
                "title": "Fix login crash",
                "state": "open",
                "draft": False,
                "ci_status": "success",
                "author": "dev-b",
                "html_url": "https://github.com/acme/ios-smoke/pull/2",
                "created_at": "2026-07-17T09:30:00Z",
                "updated_at": "2026-07-17T09:30:00Z",
            }
        ],
        "sync_run": {
            "sync_type": "full",
            "status": "completed",
            "started_at": "2026-07-17T10:00:00Z",
            "finished_at": "2026-07-17T10:01:00Z",
            "summary": {"issues": 1, "pulls": 1},
        },
        "scan_snapshot": {
            "parsed_summary": {"modules": ["auth"]},
            "raw_markdown": "# Scan summary",
        },
        "graph_snapshot": {
            "payload": {"nodes": [], "edges": []},
            "module_matrix": {"auth": [1]},
        },
    }
