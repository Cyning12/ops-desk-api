"""P3-T5 admin memory 浏览/撤销端点契约测试（治理线 · 契约真源 15-p3-contracts.md §5）。

钉死验收（task_p3_t5_admin_memory_api.md 验收 10 条 · 具名锚）：
- 鉴权矩阵：三端点无凭据 401 · viewer 403 · 未授权 revoke 零写
- facts 分页浏览：跨页不重不漏 + 默认 status=active + status/kind 过滤 +
  参数校验（limit 越界/词表外/坏 cursor/缺 tenant → 422）+ 投影无 embedding
- revoke 幂等：首撤 200 affected=N · 重放/无匹配 200 affected=0 否 409 ·
  缺 user_id tenant 范围全撤 · 审计 logger.info 记 key/tenant/affected 不记 value
- episodes 只读：GET 200 过滤 + 写动词 405/404

⚠️ 全文件 async def（asyncio_mode=auto）；真 PostgreSQL（opsdesk_test）。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

from app.db.models import OpsMemoryEpisode, OpsMemoryFact
from app.db.session import AsyncSessionLocal
from app.main import app as fastapi_app
from app.ops.deps import require_admin_sync
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

FACTS = "/api/ops/admin/memory/facts"
EPISODES = "/api/ops/admin/memory/episodes"
_TENANT = "mfa5-test-tenant"
_USER = "mfa5-test-user"

_BASE_DT = datetime(2026, 1, 1, 0, 0, 0)


@pytest.fixture
def as_admin():
    """走 Bearer 机读路径（覆盖依赖即可 · purge 测试先例同形）。"""
    fastapi_app.dependency_overrides[require_admin_sync] = lambda: None
    yield
    fastapi_app.dependency_overrides.pop(require_admin_sync, None)


async def _clear_test_rows() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mfa5-test-%'")
        )
        await session.execute(
            text("DELETE FROM ops_memory_episodes WHERE tenant_id LIKE 'mfa5-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_test_rows()
    yield
    await _clear_test_rows()


async def _seed_facts(rows: list[dict]) -> list[str]:
    """直插 ORM（绕 gate：测试覆盖 kind/status 全词表，gate 有 key 域约束）。"""
    ids: list[str] = []
    async with AsyncSessionLocal() as session, session.begin():
        for i, row in enumerate(rows):
            fact = OpsMemoryFact(
                tenant_id=row.get("tenant_id", _TENANT),
                user_id=row.get("user_id", _USER),
                key=row.get("key", f"seed.key_{i:02d}"),
                value=row.get("value", f"v{i}"),
                kind=row.get("kind", "fact"),
                status=row.get("status", "active"),
                created_at=row.get("created_at", _BASE_DT + timedelta(minutes=i)),
            )
            session.add(fact)
            await session.flush()
            ids.append(str(fact.id))
    return ids


async def _seed_episodes(rows: list[dict]) -> list[str]:
    ids: list[str] = []
    async with AsyncSessionLocal() as session, session.begin():
        for i, row in enumerate(rows):
            ep = OpsMemoryEpisode(
                tenant_id=row.get("tenant_id", _TENANT),
                run_id=row.get("run_id", f"run-{i:02d}"),
                task_domain=row.get("task_domain", "general"),
                context_fingerprint=row.get("context_fingerprint", f"fp{i:02d}"),
                plan_summary=row.get("plan_summary", f"plan {i}"),
                tool_sequence=row.get("tool_sequence", ["cap.read"]),
                outcome=row.get("outcome", "success"),
                failure_class=row.get("failure_class"),
                status=row.get("status", "active"),
                created_at=row.get("created_at", _BASE_DT + timedelta(minutes=i)),
            )
            session.add(ep)
            await session.flush()
            ids.append(str(ep.id))
    return ids


async def _fact_status(fact_id: str) -> str:
    async with AsyncSessionLocal() as session:
        row = await session.execute(
            text("SELECT status FROM ops_memory_facts WHERE id = :i"), {"i": fact_id}
        )
        return str(row.scalar())


async def _count_facts(where: str, params: dict) -> int:
    async with AsyncSessionLocal() as session:
        row = await session.execute(
            text(f"SELECT count(*) FROM ops_memory_facts WHERE {where}"), params
        )
        return int(row.scalar() or 0)


# ---------------- 鉴权矩阵：无凭据 401 · viewer 403 · 未授权零写 ----------------


async def test_facts_unauthorized_401(client):
    resp = await client.get(FACTS, params={"tenant_id": _TENANT})
    assert resp.status_code == 401


async def test_revoke_unauthorized_401_zero_write(client):
    (fid,) = await _seed_facts([{"key": "auth.zero_write"}])
    resp = await client.post(
        f"{FACTS}/auth.zero_write/revoke",
        json={"tenant_id": _TENANT, "user_id": _USER},
    )
    assert resp.status_code == 401
    assert await _fact_status(fid) == "active"  # 未授权零写


async def test_episodes_unauthorized_401(client):
    resp = await client.get(EPISODES, params={"tenant_id": _TENANT})
    assert resp.status_code == 401


async def test_facts_viewer_403(client, override_auth_viewer):
    resp = await client.get(FACTS, params={"tenant_id": _TENANT})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Maintainer role required"


async def test_revoke_viewer_403_zero_write(client, override_auth_viewer):
    (fid,) = await _seed_facts([{"key": "auth.viewer_zero"}])
    resp = await client.post(
        f"{FACTS}/auth.viewer_zero/revoke",
        json={"tenant_id": _TENANT, "user_id": _USER},
    )
    assert resp.status_code == 403
    assert await _fact_status(fid) == "active"


async def test_episodes_viewer_403(client, override_auth_viewer):
    resp = await client.get(EPISODES, params={"tenant_id": _TENANT})
    assert resp.status_code == 403


# ---------------- facts 分页浏览 ----------------


async def test_facts_pagination_keyset(client, as_admin):
    ids = await _seed_facts([{} for _ in range(5)])  # created_at 递增
    page1 = await client.get(FACTS, params={"tenant_id": _TENANT, "limit": 2})
    assert page1.status_code == 200
    body1 = page1.json()
    assert body1["ok"] is True
    facts1 = body1["data"]["facts"]
    assert len(facts1) == 2
    cursor1 = body1["data"]["next_cursor"]
    assert cursor1  # 还有下一页

    page2 = await client.get(
        FACTS, params={"tenant_id": _TENANT, "limit": 2, "cursor": cursor1}
    )
    assert page2.status_code == 200
    body2 = page2.json()
    facts2 = body2["data"]["facts"]
    assert len(facts2) == 2
    cursor2 = body2["data"]["next_cursor"]
    assert cursor2

    page3 = await client.get(
        FACTS, params={"tenant_id": _TENANT, "limit": 2, "cursor": cursor2}
    )
    assert page3.status_code == 200
    body3 = page3.json()
    facts3 = body3["data"]["facts"]
    assert len(facts3) == 1
    assert body3["data"]["next_cursor"] is None  # 末页

    got = [f["id"] for f in facts1 + facts2 + facts3]
    assert len(set(got)) == 5  # 跨页不重
    assert set(got) == set(ids)  # 跨页不漏
    # (created_at DESC, id DESC)：首条为最新写入
    assert got[0] == ids[-1]
    assert got[-1] == ids[0]


async def test_facts_default_status_active(client, as_admin):
    await _seed_facts(
        [
            {"key": "dflt.active", "status": "active"},
            {"key": "dflt.revoked", "status": "revoked"},
            {"key": "dflt.superseded", "status": "superseded"},
            {"key": "dflt.expired", "status": "expired"},
        ]
    )
    resp = await client.get(FACTS, params={"tenant_id": _TENANT})
    assert resp.status_code == 200
    facts = resp.json()["data"]["facts"]
    assert {f["key"] for f in facts} == {"dflt.active"}  # 默认 status=active
    assert all(f["status"] == "active" for f in facts)


async def test_facts_filter_status_kind(client, as_admin):
    await _seed_facts(
        [
            {"key": "flt.a1", "status": "active", "kind": "fact", "user_id": _USER},
            {
                "key": "flt.p1",
                "status": "revoked",
                "kind": "preference",
                "user_id": _USER,
            },
            {"key": "flt.a2", "status": "active", "kind": "preference"},
            {"key": "flt.other_user", "status": "active", "user_id": "mfa5-test-other"},
        ]
    )
    resp = await client.get(
        FACTS, params={"tenant_id": _TENANT, "status": "revoked"}
    )
    assert resp.status_code == 200
    assert {f["key"] for f in resp.json()["data"]["facts"]} == {"flt.p1"}

    resp = await client.get(
        FACTS, params={"tenant_id": _TENANT, "kind": "preference"}
    )
    assert resp.status_code == 200
    assert {f["key"] for f in resp.json()["data"]["facts"]} == {"flt.a2"}

    resp = await client.get(
        FACTS, params={"tenant_id": _TENANT, "user_id": "mfa5-test-other"}
    )
    assert resp.status_code == 200
    assert {f["key"] for f in resp.json()["data"]["facts"]} == {"flt.other_user"}


async def test_facts_limit_422(client, as_admin):
    for bad in (0, 201):
        resp = await client.get(FACTS, params={"tenant_id": _TENANT, "limit": bad})
        assert resp.status_code == 422


async def test_facts_vocab_422(client, as_admin):
    resp = await client.get(
        FACTS, params={"tenant_id": _TENANT, "status": "bogus"}
    )
    assert resp.status_code == 422
    resp = await client.get(FACTS, params={"tenant_id": _TENANT, "kind": "bogus"})
    assert resp.status_code == 422


async def test_facts_bad_cursor_422(client, as_admin):
    resp = await client.get(
        FACTS, params={"tenant_id": _TENANT, "cursor": "not-a-cursor!!!"}
    )
    assert resp.status_code == 422


async def test_facts_missing_tenant_422(client, as_admin):
    resp = await client.get(FACTS)
    assert resp.status_code == 422


async def test_facts_projection_excludes_embedding(client, as_admin):
    await _seed_facts([{"key": "proj.keys", "value": "secret-value"}])
    resp = await client.get(FACTS, params={"tenant_id": _TENANT})
    assert resp.status_code == 200
    facts = resp.json()["data"]["facts"]
    assert len(facts) == 1
    assert set(facts[0].keys()) == {
        "id",
        "tenant_id",
        "user_id",
        "key",
        "value",
        "kind",
        "source_run_id",
        "source_turn",
        "status",
        "expires_at",
        "created_at",
        "updated_at",
    }
    assert "embedding" not in facts[0]


# ---------------- revoke 幂等 / tenant 范围 / 审计 ----------------


async def test_revoke_first_affected_n(client, as_admin):
    (fid,) = await _seed_facts([{"key": "rev.first"}])
    resp = await client.post(
        f"{FACTS}/rev.first/revoke",
        json={"tenant_id": _TENANT, "user_id": _USER},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["affected"] == 1
    assert await _fact_status(fid) == "revoked"  # 逻辑失效不物理删


async def test_revoke_replay_affected_0(client, as_admin):
    await _seed_facts([{"key": "rev.replay"}])
    payload = {"tenant_id": _TENANT, "user_id": _USER}
    first = await client.post(f"{FACTS}/rev.replay/revoke", json=payload)
    assert first.status_code == 200
    assert first.json()["data"]["affected"] == 1
    replay = await client.post(f"{FACTS}/rev.replay/revoke", json=payload)
    assert replay.status_code == 200  # 已撤销 → 幂等 200（否 409）
    assert replay.json()["data"]["affected"] == 0


async def test_revoke_no_match_affected_0(client, as_admin):
    resp = await client.post(
        f"{FACTS}/rev.no_such_key/revoke",
        json={"tenant_id": _TENANT, "user_id": _USER},
    )
    assert resp.status_code == 200  # 无匹配 → 幂等 200 affected=0
    assert resp.json()["data"]["affected"] == 0


async def test_revoke_tenant_wide_without_user(client, as_admin):
    await _seed_facts(
        [
            {"key": "rev.wide", "user_id": _USER},
            {"key": "rev.wide", "user_id": "mfa5-test-other"},
            {"key": "rev.wide", "tenant_id": "mfa5-test-other-tenant"},
            {"key": "rev.keep", "user_id": _USER},
        ]
    )
    resp = await client.post(
        f"{FACTS}/rev.wide/revoke", json={"tenant_id": _TENANT}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["affected"] == 2  # 同 tenant 异 user 同 key 全撤
    # 异 tenant 不受影响；同 tenant 异 key 不受影响
    assert await _count_facts(
        "tenant_id = 'mfa5-test-other-tenant' AND status = 'active'", {}
    ) == 1
    assert await _count_facts(
        "tenant_id = :t AND key = 'rev.keep' AND status = 'active'", {"t": _TENANT}
    ) == 1


async def test_revoke_audit_log(client, as_admin, caplog):
    secret = "audit-secret-value-9f3c"
    await _seed_facts([{"key": "rev.audit", "value": secret}])
    with caplog.at_level(logging.INFO):
        resp = await client.post(
            f"{FACTS}/rev.audit/revoke",
            json={"tenant_id": _TENANT, "user_id": _USER},
        )
    assert resp.status_code == 200
    audit = [r for r in caplog.records if "revoke_by_key" in r.getMessage()]
    assert audit, "审计 logger.info 缺失"
    msg = audit[-1].getMessage()
    assert "rev.audit" in msg  # 记 key
    assert _TENANT in msg  # 记 tenant
    assert "affected=1" in msg  # 记 affected
    assert secret not in caplog.text  # 不记 value（无 PII 泄漏面）


async def test_revoke_blank_fields_400(client, as_admin):
    resp = await client.post(
        f"{FACTS}/rev.blank/revoke", json={"tenant_id": "   ", "user_id": _USER}
    )
    assert resp.status_code == 400
    # 显式空白 user_id ≠ 缺省：防「慎用全撤」被笔误盲发
    resp = await client.post(
        f"{FACTS}/rev.blank/revoke", json={"tenant_id": _TENANT, "user_id": "  "}
    )
    assert resp.status_code == 400
    resp = await client.post(
        f"{FACTS}/%20%20%20/revoke",
        json={"tenant_id": _TENANT, "user_id": _USER},
    )
    assert resp.status_code == 400


async def test_revoke_500_not_silent(client, as_admin, monkeypatch):
    await _seed_facts([{"key": "rev.500"}])

    async def _boom(*args, **kwargs):
        raise RuntimeError("db down mid-revoke")

    monkeypatch.setattr("app.ops.admin.memory.revoke_by_key", _boom)
    resp = await client.post(
        f"{FACTS}/rev.500/revoke",
        json={"tenant_id": _TENANT, "user_id": _USER},
    )
    assert resp.status_code == 500
    assert resp.json()["detail"]["stage"] == "memory_revoke"
    count = await _count_facts(
        "tenant_id = :t AND key = 'rev.500' AND status = 'active'", {"t": _TENANT}
    )
    assert count == 1  # rollback：零写


# ---------------- episodes 只读 ----------------


async def test_episodes_list_and_filters(client, as_admin):
    ids = await _seed_episodes(
        [
            {"run_id": "run-a", "outcome": "success"},
            {"run_id": "run-b", "outcome": "failure", "failure_class": "tool_error"},
            {"run_id": "run-c", "outcome": "partial", "status": "revoked"},
        ]
    )
    resp = await client.get(EPISODES, params={"tenant_id": _TENANT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    episodes = body["data"]["episodes"]
    assert len(episodes) == 3
    assert body["data"]["next_cursor"] is None
    assert set(episodes[0].keys()) == {
        "id",
        "tenant_id",
        "run_id",
        "task_domain",
        "context_fingerprint",
        "plan_summary",
        "tool_sequence",
        "outcome",
        "failure_class",
        "status",
        "created_at",
    }
    assert {e["id"] for e in episodes} == set(ids)

    resp = await client.get(EPISODES, params={"tenant_id": _TENANT, "run_id": "run-b"})
    assert resp.status_code == 200
    assert [e["run_id"] for e in resp.json()["data"]["episodes"]] == ["run-b"]

    resp = await client.get(EPISODES, params={"tenant_id": _TENANT, "outcome": "failure"})
    assert resp.status_code == 200
    assert {e["outcome"] for e in resp.json()["data"]["episodes"]} == {"failure"}

    resp = await client.get(EPISODES, params={"tenant_id": _TENANT, "status": "revoked"})
    assert resp.status_code == 200
    assert {e["status"] for e in resp.json()["data"]["episodes"]} == {"revoked"}

    resp = await client.get(EPISODES, params={"tenant_id": _TENANT, "outcome": "bogus"})
    assert resp.status_code == 422
    resp = await client.get(EPISODES)
    assert resp.status_code == 422  # 缺 tenant_id


async def test_episodes_write_verbs_rejected(client, as_admin):
    for method in ("post", "put", "patch", "delete"):
        resp = await client.request(method, EPISODES, json={})
        assert resp.status_code == 405, method
    # 单条 revoke 不做（N2）：未注册路由 → 404
    eid = uuid.uuid4()
    resp = await client.post(f"{EPISODES}/{eid}/revoke", json={})
    assert resp.status_code == 404
