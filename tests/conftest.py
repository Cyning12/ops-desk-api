"""Pytest fixtures."""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models import OpsInviteToken, OpsRepo, OpsSession, OpsSessionChat, OpsUser
from app.db.session import AsyncSessionLocal, engine
from app.main import app as fastapi_app
from app.ops.deps import get_current_user
from app.ops.security import generate_invite_token, hash_token


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


def _db_available() -> bool:
    """Check whether PostgreSQL is reachable for integration tests."""

    async def _ping() -> bool:
        try:
            async with engine.connect():
                return True
        except Exception:
            return False
        finally:
            await engine.dispose()

    return asyncio.run(_ping())


DB_AVAILABLE = _db_available()


@pytest.fixture(autouse=True)
async def _reset_engine():
    """Dispose the async engine before each test to avoid cross-event-loop connection reuse."""
    await engine.dispose()
    yield


@pytest.fixture
async def clean_sync_data():
    """Remove all synced repos and cascading children before a test."""
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
