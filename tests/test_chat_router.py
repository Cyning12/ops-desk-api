"""Integration tests for chat SSE router."""
from __future__ import annotations

import json

import pytest

from app.db.models import OpsUser
from app.db.session import engine
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk
from app.main import app as fastapi_app


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


def _parse_sse(response_text: str) -> list[dict]:
    """Parse SSE response text into a list of event data dicts."""
    events = []
    for block in response_text.strip().split("\n\n"):
        if not block.strip():
            continue
        lines = block.splitlines()
        data_line = next((line for line in lines if line.startswith("data: ")), None)
        if data_line:
            events.append(json.loads(data_line[len("data: "):]))
    return events


class FakeProvider(BaseProviderImpl):
    def __init__(self, chunks: list[LlmChunk]) -> None:
        self._chunks = chunks

    async def complete_stream(self, messages, model=None):
        for chunk in self._chunks:
            yield chunk


@pytest.fixture
def override_auth(monkeypatch):
    """Override auth dependency with a test user."""
    from functools import wraps

    from app.ops.deps import get_current_user as real_get_current_user

    test_user = OpsUser(
        id="00000000-0000-0000-0000-000000000001", username="tester", role="viewer"
    )

    @wraps(real_get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[real_get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def fake_provider(monkeypatch):
    def _make(chunks: list[LlmChunk]):
        monkeypatch.setattr(
            "app.ops.chat.nodes.get_llm_provider",
            lambda: FakeProvider(chunks),
        )

    return _make


@pytest.fixture
def no_persist(monkeypatch):
    """Disable DB persistence for lightweight router tests."""
    async def fake_resolve(*args, **kwargs):
        return "00000000-0000-0000-0000-000000000002"

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.ops.chat.router._resolve_chat_session",
        fake_resolve,
    )
    monkeypatch.setattr(
        "app.ops.chat.router._create_run_record",
        _noop,
    )
    monkeypatch.setattr(
        "app.ops.chat.streaming.flush_run_events",
        _noop,
    )
    monkeypatch.setattr(
        "app.ops.chat.streaming.persist_run_events",
        _noop,
    )


class TestChatStream:
    @pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
    async def test_stream_success(self, client, override_auth, fake_provider, no_persist):
        fake_provider([LlmChunk(content="Hello"), LlmChunk(content="!")])

        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        events = _parse_sse(response.text)
        event_types = [e["event_type"] for e in events]
        assert event_types == ["run.start", "thinking", "thinking", "answer", "answer", "done"]

        answer_event = events[3]
        assert answer_event["agent_role"] == "answer"
        assert answer_event["payload"]["content"] == "Hello"

    async def test_stream_requires_auth(self, client, fake_provider, no_persist):
        fake_provider([LlmChunk(content="ok")])

        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 401

    @pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
    async def test_stream_invalid_session(self, client, override_auth, fake_provider):
        fake_provider([LlmChunk(content="ok")])
        response = await client.post(
            "/api/ops/chat/stream",
            json={"message": "hi", "session_id": "00000000-0000-0000-0000-000000000099"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 404

    @pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
    async def test_stream_existing_session_ok(self, client, fake_provider):
        """Regression: a valid session_id must not 404.

        Real DB auth loads ``OpsUser.id`` as ``uuid.UUID``; the session check
        compared ``str(session.user_id)`` against that UUID object and always
        404'd. This test overrides auth with a UUID-id user to reproduce it.
        """
        from functools import wraps

        from sqlalchemy import delete

        from app.db.models import OpsSessionChat
        from app.db.models import OpsUser as DbUser
        from app.db.session import AsyncSessionLocal
        from app.ops.deps import get_current_user

        fake_provider([LlmChunk(content="ok")])
        async with AsyncSessionLocal() as db:
            user = DbUser(username="uuid_regression_user", role="viewer")
            db.add(user)
            await db.flush()
            chat_session = OpsSessionChat(user_id=user.id, title="regression")
            db.add(chat_session)
            await db.commit()
            await db.refresh(user)
            await db.refresh(chat_session)
            uid, sid = user.id, chat_session.id

        # Fresh instance whose id is a uuid.UUID, mimicking real DB-loaded auth.
        auth_user = DbUser(id=uid, username="uuid_regression_user", role="viewer")

        @wraps(get_current_user)
        async def fake_get_current_user(*args, **kwargs):
            return auth_user

        fastapi_app.dependency_overrides[get_current_user] = fake_get_current_user
        try:
            response = await client.post(
                "/api/ops/chat/stream",
                json={"message": "hi", "session_id": str(sid)},
                headers={"Accept": "text/event-stream"},
            )
        finally:
            fastapi_app.dependency_overrides.clear()
            async with AsyncSessionLocal() as db:
                await db.execute(delete(OpsSessionChat).where(OpsSessionChat.id == sid))
                await db.execute(delete(DbUser).where(DbUser.id == uid))
                await db.commit()

        assert response.status_code == 200


class TestListModels:
    async def test_list_models(self, client):
        response = await client.get("/api/ops/chat/models")

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "siliconflow"
        assert data["default_model"] == "deepseek-ai/DeepSeek-V4-Flash"
        assert any(m["id"] == "deepseek-ai/DeepSeek-V4-Flash" for m in data["models"])
