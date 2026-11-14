"""Integration tests for chat SSE router."""

from __future__ import annotations

import pytest

from app.db.models import OpsUser
from app.main import app as fastapi_app


@pytest.fixture
def override_auth(monkeypatch):
    """Override auth dependency with a test user."""
    from functools import wraps

    from app.ops.deps import get_current_user as real_get_current_user

    test_user = OpsUser(id="00000000-0000-0000-0000-000000000001", username="tester", role="viewer")

    @wraps(real_get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[real_get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


class TestChatStream:
    """POST /api/ops/chat/stream 已 410 下线（lg-rag T6 · 2026-08-31）。

    原 SSE 流式用例改写为 410 断言；迁移指针指向 POST /api/ops/lg-rag/stream。
    """

    async def test_stream_success(self, client, override_auth):
        """410 Gone + JSON 迁移指针 + Deprecation/Link 头（原 SSE 200 用例改写）。"""
        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 410
        assert response.headers["Deprecation"] == "true"
        assert response.headers["Link"] == '</api/ops/lg-rag/stream>; rel="successor-version"'
        detail = response.json()["detail"]
        assert detail["error"] == "chat_stream_deprecated"
        assert detail["migrate_to"] == "/api/ops/lg-rag/stream"
        assert detail["message"]

    async def test_stream_requires_auth(self, client):
        """鉴权前置：未登录仍 401（先于 410，匿名探针不见迁移指针）。"""
        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 401

    async def test_stream_invalid_session(self, client, override_auth):
        """端点整体下线：不再做 session 解析，未知 session_id 同样 410（原 404 用例改写）。"""
        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi", "session_id": "00000000-0000-0000-0000-000000000099"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 410

    async def test_stream_existing_session_ok(self, client, override_auth):
        """端点下线后携带有效 session_id 同样 410（原 200 用例改写）。

        原回归意图（保留说明，R1 非阻塞 4）：有效 session_id 不得 404——真实 DB
        鉴权加载的 OpsUser.id 为 uuid.UUID，session 归属比对曾恒 404。端点整体
        弃用后该回归对象不复存在，不再依赖真实 DB 复现。
        """
        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi", "session_id": "00000000-0000-0000-0000-000000000002"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 410


class TestListModels:
    """GET /api/ops/chat/models 已 410 下线（P0' T2b · 2026-11-14）。"""

    async def test_list_models_gone(self, client, override_auth):
        """410 Gone + detail{error, migrate_to 指向 lg-rag} + Deprecation 头。"""
        response = await client.get("/api/ops/chat/models")

        assert response.status_code == 410
        detail = response.json()["detail"]
        assert detail["error"] == "chat_models_deprecated"
        assert "lg-rag" in detail["migrate_to"]
        assert response.headers.get("Deprecation") == "true"

    async def test_list_models_requires_auth(self, client):
        """鉴权前置：未登录仍 401（先于 410）。"""
        response = await client.get("/api/ops/chat/models")

        assert response.status_code == 401


class TestLatestChatSession:
    """GET /api/ops/chat/sessions/latest 已 410 下线（P0' T2b · 2026-11-14）。"""

    async def test_sessions_latest_gone(self, client, override_auth):
        """410 Gone + detail{error, migrate_to=/api/ops/chat/threads} + Deprecation 头。"""
        response = await client.get("/api/ops/chat/sessions/latest")

        assert response.status_code == 410
        detail = response.json()["detail"]
        assert detail["error"] == "chat_sessions_deprecated"
        assert detail["migrate_to"] == "/api/ops/chat/threads"
        assert response.headers.get("Deprecation") == "true"

    async def test_sessions_latest_requires_auth(self, client):
        """鉴权前置：未登录仍 401（先于 410）。"""
        response = await client.get("/api/ops/chat/sessions/latest")

        assert response.status_code == 401
