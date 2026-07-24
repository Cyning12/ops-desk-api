"""Tests for auth endpoints and session dependencies."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.db.models import OpsInviteToken, OpsSession, OpsSessionChat, OpsUser
from app.db.session import AsyncSessionLocal, engine
from app.main import app as fastapi_app
from app.ops.security import generate_invite_token, hash_token


def _db_available() -> bool:
    """Check whether PostgreSQL is reachable for integration tests."""
    import asyncio

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
async def seeded_maintainer():
    """Create a maintainer user with an unused invite token and a plaintext token."""
    plaintext_invite = generate_invite_token()
    async with AsyncSessionLocal() as db:
        user = OpsUser(username="admin", role="maintainer")
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
            await cleanup_db.execute(delete(OpsSession).where(OpsSession.user_id == user.id))
            await cleanup_db.execute(
                delete(OpsInviteToken).where(OpsInviteToken.token == hash_token(plaintext_invite))
            )
            await cleanup_db.execute(delete(OpsSessionChat).where(OpsSessionChat.user_id == user.id))
            await cleanup_db.execute(delete(OpsUser).where(OpsUser.id == user.id))
            await cleanup_db.commit()


@pytest.fixture
def override_auth_maintainer():
    """Override auth dependency with a test maintainer."""
    from functools import wraps

    from app.ops.deps import get_current_user as real_get_current_user

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000001",
        username="admin",
        role="maintainer",
    )

    @wraps(real_get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[real_get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def override_auth_viewer():
    """Override auth dependency with a test viewer."""
    from functools import wraps

    from app.ops.deps import get_current_user as real_get_current_user

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000002",
        username="viewer",
        role="viewer",
    )

    @wraps(real_get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[real_get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_login_success(client: AsyncClient, seeded_maintainer) -> None:
    """Login returns user and sets ops_session cookie."""
    response = await client.post(
        "/api/ops/auth/login",
        json={
            "username": seeded_maintainer["user"].username,
            "invite_token": seeded_maintainer["plaintext_invite"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "maintainer"
    assert "ops_session" in response.cookies


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_login_invalid_username(client: AsyncClient, seeded_maintainer) -> None:
    """Wrong username returns 401."""
    response = await client.post(
        "/api/ops/auth/login",
        json={"username": "nobody", "invite_token": seeded_maintainer["plaintext_invite"]},
    )
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_login_invalid_token(client: AsyncClient, seeded_maintainer) -> None:
    """Wrong invite token returns 401."""
    response = await client.post(
        "/api/ops/auth/login",
        json={
            "username": seeded_maintainer["user"].username,
            "invite_token": generate_invite_token(),
        },
    )
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_login_expired_token(client: AsyncClient) -> None:
    """Expired invite token returns 401."""
    plaintext_invite = generate_invite_token()
    async with AsyncSessionLocal() as db:
        user = OpsUser(username="expired-user", role="maintainer")
        db.add(user)
        await db.flush()
        invite = OpsInviteToken(
            token=hash_token(plaintext_invite),
            role="maintainer",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(invite)
        await db.commit()

    response = await client.post(
        "/api/ops/auth/login",
        json={"username": "expired-user", "invite_token": plaintext_invite},
    )
    assert response.status_code == 401

    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsUser).where(OpsUser.username == "expired-user"))
        await db.execute(delete(OpsInviteToken).where(OpsInviteToken.token == hash_token(plaintext_invite)))
        await db.commit()


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_logout_clears_session(client: AsyncClient, seeded_maintainer) -> None:
    """Logout deletes DB session and clears cookie."""
    login_response = await client.post(
        "/api/ops/auth/login",
        json={
            "username": seeded_maintainer["user"].username,
            "invite_token": seeded_maintainer["plaintext_invite"],
        },
    )
    assert login_response.status_code == 200
    assert "ops_session" in login_response.cookies

    logout_response = await client.post("/api/ops/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.cookies.get("ops_session") is None

    me_response = await client.get("/api/ops/auth/me")
    assert me_response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_me_requires_auth(client: AsyncClient) -> None:
    """GET /me without cookie returns 401."""
    response = await client.get("/api/ops/auth/me")
    assert response.status_code == 401


async def test_admin_sync_requires_auth(client: AsyncClient) -> None:
    """POST /admin/sync without cookie returns 401."""
    response = await client.post(
        "/api/ops/admin/sync",
        json={"repo_full_name": "acme/demo", "sync_type": "issues", "data": {}},
    )
    assert response.status_code == 401


async def test_admin_sync_viewer_forbidden(
    client: AsyncClient, override_auth_viewer
) -> None:
    """POST /admin/sync as viewer returns 403."""
    response = await client.post(
        "/api/ops/admin/sync",
        json={"repo_full_name": "acme/demo", "sync_type": "issues", "data": {}},
    )
    assert response.status_code == 403


async def test_admin_sync_maintainer_allowed(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """POST /admin/sync as maintainer returns 202."""
    response = await client.post(
        "/api/ops/admin/sync",
        json={"repo_full_name": "acme/demo", "sync_type": "issues", "data": {}},
    )
    assert response.status_code == 202


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_latest_chat_session_creates_when_empty(
    client: AsyncClient, seeded_maintainer
) -> None:
    """GET /chat/sessions/latest creates a session when none exist."""
    login_response = await client.post(
        "/api/ops/auth/login",
        json={
            "username": seeded_maintainer["user"].username,
            "invite_token": seeded_maintainer["plaintext_invite"],
        },
    )
    assert login_response.status_code == 200

    response = await client.get("/api/ops/chat/sessions/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(seeded_maintainer["user"].id)
    assert data["title"] == "New Chat"

    # Second call returns the same session.
    response2 = await client.get("/api/ops/chat/sessions/latest")
    assert response2.status_code == 200
    assert response2.json()["id"] == data["id"]
