"""P1-T2 · REST goal 面（GET/PATCH /api/ops/goals · issue #390 · 设计真源 07 §4/§5）。

- 未登录 401（CurrentUser 前置）。
- 词表外 status → 422（pydantic Literal 前置，不进 store）。
- 跨租户 goal_id → 404（防探测，非 403）。
- 非法流转 / 终态不可逆 → 409。
- 正路径：GET list（含终态）· PATCH 流转成功 200。
"""

from __future__ import annotations

import uuid

import pytest

from app.db.models import OpsUser
from app.main import app as fastapi_app
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 ops_goals")


@pytest.fixture
def override_auth(monkeypatch):
    """Override auth dependency with a test user（test_chat_router.py 体例）。"""
    from functools import wraps

    from app.ops.deps import get_current_user as real_get_current_user

    test_user = OpsUser(id="00000000-0000-0000-0000-000000000001", username="tester", role="viewer")

    @wraps(real_get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return test_user

    fastapi_app.dependency_overrides[real_get_current_user] = fake_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()


async def _mk_goal(*, tenant_id: str, thread_id: str, status: str = "active") -> str:
    from app.ops.goals.store import patch_goal_status, resolve_goal_for_thread

    g = await resolve_goal_for_thread(tenant_id=tenant_id, thread_id=thread_id, query="把同步修好")
    assert g is not None
    if status != "active":
        g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant_id, new_status=status)
    return g["goal_id"]


class TestGoalsAuth:
    async def test_list_requires_auth(self, client):
        response = await client.get("/api/ops/goals", params={"thread_id": "th-x"})
        assert response.status_code == 401

    async def test_patch_requires_auth(self, client):
        response = await client.patch(
            f"/api/ops/goals/{uuid.uuid4()}", json={"status": "paused"}
        )
        assert response.status_code == 401


@_DB_REQUIRED
class TestGoalsRest:
    async def test_list_empty_then_after_create(self, client, override_auth):
        """GET 正路径：空 → resolve 建行后可列（默认 session 租户 TENANT_A）。"""
        thread = f"th-{uuid.uuid4().hex[:8]}"
        r0 = await client.get("/api/ops/goals", params={"thread_id": thread})
        assert r0.status_code == 200
        assert r0.json() == {"goals": []}

        from app.ops.tenant_context import TENANT_A

        gid = await _mk_goal(tenant_id=TENANT_A, thread_id=thread)
        r1 = await client.get("/api/ops/goals", params={"thread_id": thread})
        assert r1.status_code == 200
        goals = r1.json()["goals"]
        assert len(goals) == 1
        assert goals[0]["goal_id"] == gid
        assert goals[0]["status"] == "active"
        assert goals[0]["objective"] == "把同步修好"

    async def test_patch_transition_ok(self, client, override_auth):
        """PATCH 正路径：active→paused→active（O-1 人工复活通道）。"""
        from app.ops.tenant_context import TENANT_A

        thread = f"th-{uuid.uuid4().hex[:8]}"
        gid = await _mk_goal(tenant_id=TENANT_A, thread_id=thread)
        r = await client.patch(f"/api/ops/goals/{gid}", json={"status": "paused"})
        assert r.status_code == 200
        assert r.json()["status"] == "paused"
        r2 = await client.patch(f"/api/ops/goals/{gid}", json={"status": "active"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "active"

    async def test_patch_unknown_status_422(self, client, override_auth):
        """词表外 status → pydantic Literal 前置 422（不进 store）。"""
        from app.ops.tenant_context import TENANT_A

        thread = f"th-{uuid.uuid4().hex[:8]}"
        gid = await _mk_goal(tenant_id=TENANT_A, thread_id=thread)
        r = await client.patch(f"/api/ops/goals/{gid}", json={"status": "archived"})
        assert r.status_code == 422

    async def test_patch_cross_tenant_404(self, client, override_auth):
        """跨租户 goal_id → 404（防探测）；同租户不存在 id 同样 404。"""
        from app.ops.tenant_context import TENANT_B

        thread = f"th-{uuid.uuid4().hex[:8]}"
        gid_b = await _mk_goal(tenant_id=TENANT_B, thread_id=thread)
        # 默认 session 租户 TENANT_A 不可见 TENANT_B 的 goal
        r = await client.patch(f"/api/ops/goals/{gid_b}", json={"status": "paused"})
        assert r.status_code == 404
        r2 = await client.patch(f"/api/ops/goals/{uuid.uuid4()}", json={"status": "paused"})
        assert r2.status_code == 404

    async def test_patch_illegal_transition_409(self, client, override_auth):
        """非法流转 409：终态不可逆（done→active 拒绝）。"""
        from app.ops.tenant_context import TENANT_A

        thread = f"th-{uuid.uuid4().hex[:8]}"
        gid = await _mk_goal(tenant_id=TENANT_A, thread_id=thread, status="done")
        r = await client.patch(f"/api/ops/goals/{gid}", json={"status": "active"})
        assert r.status_code == 409
        # list 含终态（前端展示轨迹）
        r2 = await client.get("/api/ops/goals", params={"thread_id": thread})
        assert r2.json()["goals"][0]["status"] == "done"
