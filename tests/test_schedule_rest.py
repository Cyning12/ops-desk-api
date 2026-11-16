"""P3-T2 · REST schedule 面（/api/ops/schedules 四端点 · issue #23 · 契约 15 §1）。

- 未登录 401（CurrentUser 前置）。
- POST 201 + {"ok":true,"data":{"schedule":{...}}} 响应壳（15 §1.3）。
- 词表外 kind / interval<300 / 附加字段 → 422（detail 逐字词表 · §1.8）。
- GET list 谓词 tenant+user（§1.4）；GET/{id} 404 不泄露（§1.5）。
- PATCH 空体 422 · cancelled 终态 422 逐字（§1.6）。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.db.models import OpsUser
from app.main import app as fastapi_app
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 ops_schedules REST"
)


@pytest.fixture
async def schedule_auth():
    """建真用户（ops_schedules.user_id FK ops_users）并 override 鉴权（goals REST 体例）。"""
    from functools import wraps

    from app.db.session import AsyncSessionLocal
    from app.ops.deps import get_current_user as real_get_current_user

    async with AsyncSessionLocal() as db:
        user = OpsUser(username=f"sch-rest-{uuid.uuid4().hex[:8]}", role="viewer")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    @wraps(real_get_current_user)
    async def fake_get_current_user(*args, **kwargs):
        return user

    fastapi_app.dependency_overrides[real_get_current_user] = fake_get_current_user
    yield {"user": user}
    fastapi_app.dependency_overrides.clear()


def _create_body(**over):
    body = {
        "thread_id": f"th-{uuid.uuid4().hex[:8]}",
        "name": "每 10 分钟巡检",
        "instruction": "巡检同步状态",
        "schedule_kind": "interval",
        "interval_seconds": 600,
    }
    body.update(over)
    return body


class TestSchedulesAuth:
    async def test_post_requires_auth(self, client):
        r = await client.post("/api/ops/schedules", json=_create_body())
        assert r.status_code == 401

    async def test_list_requires_auth(self, client):
        r = await client.get("/api/ops/schedules")
        assert r.status_code == 401

    async def test_get_requires_auth(self, client):
        r = await client.get(f"/api/ops/schedules/{uuid.uuid4()}")
        assert r.status_code == 401

    async def test_patch_requires_auth(self, client):
        r = await client.patch(f"/api/ops/schedules/{uuid.uuid4()}", json={"status": "paused"})
        assert r.status_code == 401


@_DB_REQUIRED
class TestSchedulesRest:
    async def test_post_201_envelope_and_defaults(self, client, schedule_auth):
        """创建正路径：201 · ok/data 壳 · status=active · fire_count=0 · next_fire_at 即算。"""
        r = await client.post("/api/ops/schedules", json=_create_body())
        assert r.status_code == 201
        payload = r.json()
        assert payload["ok"] is True
        schedule = payload["data"]["schedule"]
        assert schedule["status"] == "active"
        assert schedule["fire_count"] == 0
        assert schedule["schedule_kind"] == "interval"
        assert schedule["interval_seconds"] == 600
        assert schedule["catchup_policy"] == "fire_once"
        assert schedule["timezone"] == "Asia/Shanghai"
        next_fire = datetime.fromisoformat(schedule["next_fire_at"])
        assert next_fire > datetime.now(UTC)
        assert schedule["humanized_display"] == "每 10 分钟"

    async def test_post_once_at(self, client, schedule_auth):
        run_at = (datetime.now(UTC) + timedelta(hours=5)).isoformat()
        r = await client.post(
            "/api/ops/schedules",
            json=_create_body(
                schedule_kind="once_at", interval_seconds=None, run_at=run_at
            ),
        )
        assert r.status_code == 201
        s = r.json()["data"]["schedule"]
        assert s["schedule_kind"] == "once_at"
        assert s["next_fire_at"] is not None
        assert s["humanized_display"].startswith("将于 ")

    async def test_post_unknown_kind_422_verbatim(self, client, schedule_auth):
        from app.ops.schedule.store import ERR_KIND

        r = await client.post("/api/ops/schedules", json=_create_body(schedule_kind="cron"))
        assert r.status_code == 422
        assert r.json()["detail"] == ERR_KIND

    async def test_post_interval_below_min_422_verbatim(self, client, schedule_auth):
        from app.ops.schedule.store import ERR_INTERVAL_MIN

        r = await client.post(
            "/api/ops/schedules", json=_create_body(interval_seconds=120)
        )
        assert r.status_code == 422
        assert r.json()["detail"] == ERR_INTERVAL_MIN

    async def test_post_extra_field_422(self, client, schedule_auth):
        """additionalProperties:false（15 §1.3）。"""
        r = await client.post(
            "/api/ops/schedules", json=_create_body(cron_expr="* * * * *")
        )
        assert r.status_code == 422

    async def test_list_predicate_thread_and_user(self, client, schedule_auth):
        """GET 列表：?thread_id= 过滤 + 同租户他用户不可见（15 §1.4 · §1.7-1）。"""
        thread = f"th-{uuid.uuid4().hex[:8]}"
        r1 = await client.post("/api/ops/schedules", json=_create_body(thread_id=thread))
        assert r1.status_code == 201
        other_thread = f"th-{uuid.uuid4().hex[:8]}"
        r2 = await client.post(
            "/api/ops/schedules", json=_create_body(thread_id=other_thread)
        )
        assert r2.status_code == 201

        rl = await client.get("/api/ops/schedules", params={"thread_id": thread})
        assert rl.status_code == 200
        assert rl.json()["ok"] is True
        schedules = rl.json()["data"]["schedules"]
        assert len(schedules) == 1
        assert schedules[0]["thread_id"] == thread

        # 他用户视角：列表空 · 详情 404（不泄露存在性）
        from functools import wraps

        from app.db.session import AsyncSessionLocal
        from app.ops.deps import get_current_user as real_get_current_user

        async with AsyncSessionLocal() as db:
            other = OpsUser(username=f"sch-other-{uuid.uuid4().hex[:8]}", role="viewer")
            db.add(other)
            await db.commit()
            await db.refresh(other)

        @wraps(real_get_current_user)
        async def fake_other(*args, **kwargs):
            return other

        fastapi_app.dependency_overrides[real_get_current_user] = fake_other
        try:
            rl2 = await client.get("/api/ops/schedules", params={"thread_id": thread})
            assert rl2.status_code == 200
            assert rl2.json()["data"]["schedules"] == []
            sid = schedules[0]["schedule_id"]
            rg = await client.get(f"/api/ops/schedules/{sid}")
            assert rg.status_code == 404
            rp = await client.patch(f"/api/ops/schedules/{sid}", json={"status": "paused"})
            assert rp.status_code == 404
        finally:
            fastapi_app.dependency_overrides.clear()

    async def test_get_detail_with_recent_fires(self, client, schedule_auth):
        """GET /{id}：schedule + recent_fires 字段集（15 §1.5）。"""
        r = await client.post("/api/ops/schedules", json=_create_body())
        sid = r.json()["data"]["schedule"]["schedule_id"]
        rg = await client.get(f"/api/ops/schedules/{sid}")
        assert rg.status_code == 200
        data = rg.json()["data"]
        assert data["schedule"]["schedule_id"] == sid
        assert data["recent_fires"] == []

    async def test_get_not_found_404(self, client, schedule_auth):
        rg = await client.get(f"/api/ops/schedules/{uuid.uuid4()}")
        assert rg.status_code == 404
        # 非法 uuid 同样 404（不泄露）
        rg2 = await client.get("/api/ops/schedules/not-a-uuid")
        assert rg2.status_code == 404

    async def test_patch_pause_resume_cancel(self, client, schedule_auth):
        """PATCH 状态机：active→paused→active→cancelled；cancelled 后再改 → 422 逐字。"""
        from app.ops.schedule.store import ERR_CANCELLED

        r = await client.post("/api/ops/schedules", json=_create_body())
        sid = r.json()["data"]["schedule"]["schedule_id"]
        rp = await client.patch(f"/api/ops/schedules/{sid}", json={"status": "paused"})
        assert rp.status_code == 200
        assert rp.json()["data"]["schedule"]["status"] == "paused"
        ra = await client.patch(f"/api/ops/schedules/{sid}", json={"status": "active"})
        assert ra.json()["data"]["schedule"]["status"] == "active"
        rc = await client.patch(f"/api/ops/schedules/{sid}", json={"status": "cancelled"})
        assert rc.json()["data"]["schedule"]["status"] == "cancelled"
        rx = await client.patch(f"/api/ops/schedules/{sid}", json={"status": "active"})
        assert rx.status_code == 422
        assert rx.json()["detail"] == ERR_CANCELLED

    async def test_patch_empty_body_422(self, client, schedule_auth):
        r = await client.post("/api/ops/schedules", json=_create_body())
        sid = r.json()["data"]["schedule"]["schedule_id"]
        rp = await client.patch(f"/api/ops/schedules/{sid}", json={})
        assert rp.status_code == 422

    async def test_patch_unknown_status_422_verbatim(self, client, schedule_auth):
        from app.ops.schedule.store import ERR_STATUS

        r = await client.post("/api/ops/schedules", json=_create_body())
        sid = r.json()["data"]["schedule"]["schedule_id"]
        rp = await client.patch(f"/api/ops/schedules/{sid}", json={"status": "archived"})
        assert rp.status_code == 422
        assert rp.json()["detail"] == ERR_STATUS

    async def test_patch_reschedule_recomputes(self, client, schedule_auth):
        """PATCH 改 interval → next_fire_at 重算且 > now（15 §1.6 · N5）。"""
        r = await client.post("/api/ops/schedules", json=_create_body())
        s = r.json()["data"]["schedule"]
        rp = await client.patch(
            f"/api/ops/schedules/{s['schedule_id']}", json={"interval_seconds": 3600}
        )
        assert rp.status_code == 200
        patched = rp.json()["data"]["schedule"]
        assert patched["interval_seconds"] == 3600
        new_next = datetime.fromisoformat(patched["next_fire_at"])
        assert new_next > datetime.now(UTC)
        assert patched["humanized_display"] == "每 1 小时"
