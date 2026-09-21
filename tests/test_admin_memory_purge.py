"""POST /admin/memory/purge 契约测试（AdminSyncAuth 对齐 · 默认干跑 · expected_count 双闸门）。

钉死验收（task D2 · SPEC §6-D2）：
- 未授权 → 401/403 且表行零变化
- 默认干跑：缺省 dry_run → 200 + 计数报告 + 表行零变化 + 响应 echo dry_run
- 双闸门三态：dry_run=false 缺 expected_count → 400 零删除；
  计数不等 → 409 零删除；计数等 → 200 且 deleted==expected_count
- tenant/user 空白 strip 后空 → 400（service.py :110-115 strip 先例对齐）
- 500 不静默：异常 rollback + HTTPException 500（admin/sync.py :35-45 先例）

⚠️ 全文件 async def（asyncio_mode=auto）；真 PostgreSQL（opsdesk_test）。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.main import app as fastapi_app
from app.ops.deps import require_admin_sync
from app.ops.memory.gate import FactCandidate
from app.ops.memory.service import write_fact
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

BASE = "/api/ops/admin/memory/purge"
_TENANT = "mfpa-test-tenant"


@pytest.fixture
def as_admin():
    """走 Bearer 机读路径（覆盖依赖即可，不必真配 token · capability 观测测先例同形）。"""
    fastapi_app.dependency_overrides[require_admin_sync] = lambda: None
    yield
    fastapi_app.dependency_overrides.pop(require_admin_sync, None)


async def _clear_test_rows() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mfpa-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_test_rows()
    yield
    await _clear_test_rows()


async def _seed(user: str, n: int = 2) -> list[str]:
    ids = []
    for i in range(n):
        fact = await write_fact(
            FactCandidate(
                tenant_id=_TENANT,
                user_id=user,
                key=f"project.item_{i:02d}",
                value=f"v{i}",
            )
        )
        ids.append(str(fact.id))
    return ids


async def _count(user: str) -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT count(*) FROM ops_memory_facts "
                "WHERE tenant_id = :t AND user_id = :u"
            ),
            {"t": _TENANT, "u": user},
        )
        return int(rows.scalar() or 0)


# ---------------- 鉴权：未授权 401/403 且零删除 ----------------


async def test_unauthorized_rejected_and_zero_delete(client):
    user = "u-noauth-" + uuid.uuid4().hex[:8]
    await _seed(user, 2)
    resp = await client.post(
        BASE,
        json={"tenant_id": _TENANT, "user_id": user, "dry_run": False, "expected_count": 2},
    )
    assert resp.status_code in (401, 403)
    assert await _count(user) == 2  # 表行零变化


# ---------------- 默认干跑：200 + echo dry_run + 表行零变化 ----------------


async def test_default_dry_run_echo_and_zero_write(client, as_admin):
    user = "u-dry-" + uuid.uuid4().hex[:8]
    await _seed(user, 2)
    resp = await client.post(BASE, json={"tenant_id": _TENANT, "user_id": user})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True  # 响应 echo dry_run 标志
    assert body["scanned"] == 2
    assert body["deleted"] == 0
    assert body["by_status"] == {"active": 2}
    assert await _count(user) == 2  # 干跑零写


async def test_explicit_dry_run_true_same_as_default(client, as_admin):
    user = "u-dry2-" + uuid.uuid4().hex[:8]
    await _seed(user, 1)
    resp = await client.post(
        BASE, json={"tenant_id": _TENANT, "user_id": user, "dry_run": True}
    )
    assert resp.status_code == 200
    assert resp.json()["dry_run"] is True
    assert await _count(user) == 1


# ---------------- 双闸门三态：400 / 409 / 200 ----------------


async def test_real_purge_missing_expected_count_400(client, as_admin):
    user = "u-400-" + uuid.uuid4().hex[:8]
    await _seed(user, 2)
    resp = await client.post(
        BASE, json={"tenant_id": _TENANT, "user_id": user, "dry_run": False}
    )
    assert resp.status_code == 400
    assert await _count(user) == 2  # 零删除


async def test_real_purge_count_mismatch_409_zero_delete(client, as_admin):
    user = "u-409-" + uuid.uuid4().hex[:8]
    await _seed(user, 2)
    resp = await client.post(
        BASE,
        json={"tenant_id": _TENANT, "user_id": user, "dry_run": False, "expected_count": 99},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["current_count"] == 2
    assert await _count(user) == 2  # 计数不等 → 零删除


async def test_real_purge_count_match_200_deleted_eq_expected(client, as_admin):
    user = "u-200-" + uuid.uuid4().hex[:8]
    await _seed(user, 3)
    dry = await client.post(BASE, json={"tenant_id": _TENANT, "user_id": user})
    assert dry.status_code == 200
    expected = dry.json()["scanned"]
    assert expected == 3

    resp = await client.post(
        BASE,
        json={
            "tenant_id": _TENANT,
            "user_id": user,
            "dry_run": False,
            "expected_count": expected,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is False
    assert body["deleted"] == expected == 3  # deleted==expected_count
    assert await _count(user) == 0  # 表行零残留

    # 幂等重放：同 expected_count 再发 → 计数漂移（3→0）→ 409 零删除
    replay = await client.post(
        BASE,
        json={
            "tenant_id": _TENANT,
            "user_id": user,
            "dry_run": False,
            "expected_count": expected,
        },
    )
    assert replay.status_code == 409


# ---------------- 空白 tenant/user → 400（strip 先例对齐） ----------------


async def test_blank_tenant_or_user_400(client, as_admin):
    resp_t = await client.post(BASE, json={"tenant_id": "   ", "user_id": "u-x"})
    assert resp_t.status_code == 400
    resp_u = await client.post(BASE, json={"tenant_id": _TENANT, "user_id": "  "})
    assert resp_u.status_code == 400


async def test_tenant_user_whitespace_stripped_before_purge(client, as_admin):
    user = "u-strip-" + uuid.uuid4().hex[:8]
    await _seed(user, 1)
    resp = await client.post(
        BASE,
        json={
            "tenant_id": f"  {_TENANT}  ",
            "user_id": f" {user} ",
            "dry_run": False,
            "expected_count": 1,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1
    assert await _count(user) == 0


# ---------------- 500 不静默：异常 rollback + HTTPException 500 ----------------


async def test_purge_internal_error_500_not_silent(client, as_admin, monkeypatch):
    user = "u-500-" + uuid.uuid4().hex[:8]
    await _seed(user, 2)

    async def _boom(*args, **kwargs):
        raise RuntimeError("db down mid-purge")

    monkeypatch.setattr("app.ops.admin.memory.purge_by_user", _boom)
    resp = await client.post(
        BASE,
        json={"tenant_id": _TENANT, "user_id": user, "dry_run": False, "expected_count": 2},
    )
    assert resp.status_code == 500
    assert resp.json()["detail"]["stage"] == "memory_purge"
    assert await _count(user) == 2  # rollback：零删除
