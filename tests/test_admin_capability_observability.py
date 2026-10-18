"""观测端点的契约测试（管理员面）。

重点不是"端点能返回 200"，而是：

1. **鉴权真的生效**（未授权拿不到观测数据）
2. **`/runtime` 能把「持久化没配」这件事说出来** —— 这是当前唯一会静默失效的地方，
   观测端点如果连它都不说，那这个端点就没解决最要紧的问题
3. `/catalog` 能回答**"为什么他没看到"**（给出 hidden + reason）
4. `/idempotency?stuck_only=true` 真的只列卡住的行
"""

from __future__ import annotations

import pytest

from app.main import app as fastapi_app
from app.ops.capability import (
    GenericHttpAdapter,
    register,
    reset_idempotency_store,
    unregister,
)
from app.ops.capability.types import CapabilitySpec
from app.ops.deps import require_admin_sync
from tests.conftest import DB_AVAILABLE

BASE = "/api/ops/admin/capability"


@pytest.fixture
def as_admin():
    """走 Bearer 机读路径（覆盖依赖即可，不必真配 token）。"""
    fastapi_app.dependency_overrides[require_admin_sync] = lambda: None
    yield
    fastapi_app.dependency_overrides.pop(require_admin_sync, None)


@pytest.fixture(autouse=True)
def _clean():
    reset_idempotency_store()
    yield
    reset_idempotency_store()


# ---------------- 鉴权 ----------------


async def test_runtime_requires_admin_auth(client):
    """**观测端点不能裸奔**：未授权一律拒。"""
    resp = await client.get(f"{BASE}/runtime")
    assert resp.status_code in (401, 403)


async def test_catalog_requires_admin_auth(client):
    resp = await client.get(f"{BASE}/catalog")
    assert resp.status_code in (401, 403)


# ---------------- /runtime ----------------


async def test_runtime_reports_persistence_and_capabilities(client, as_admin):
    resp = await client.get(f"{BASE}/runtime")
    assert resp.status_code == 200
    body = resp.json()

    persistence = body["persistence"]
    assert persistence["mode"] in {"db", "memory", "null"}
    assert persistence["env_var"] == "OPS_CAPABILITY_PERSISTENCE"
    assert isinstance(persistence["production_safe"], bool)

    caps = body["capabilities"]
    assert caps["total"] >= 5  # builtin 五枚
    assert caps["enabled"] >= 5
    assert "local_fn" in caps["by_kind"]
    assert isinstance(caps["write_capabilities"], list)


async def test_runtime_makes_disabled_persistence_visible(client, as_admin):
    """★ 没配持久化时`/runtime`必须明确说出来——不能让人靠翻环境变量发现。

    这是「唯一会静默失效的地方」：不配 = 没有防重，但一切照常运行、不报错。
    """
    resp = await client.get(f"{BASE}/runtime")
    body = resp.json()
    assert body["persistence"]["mode"] == "null"  # 测试环境默认
    assert body["persistence"]["production_safe"] is False
    assert body["persistence"]["idempotency"]["enabled"] is False
    assert body["health"]["level"] == "warn"
    assert "不可上生产" in body["health"]["message"]
    assert "第二张单据" in body["health"]["impact"]


async def test_runtime_health_ok_when_db_configured(client, as_admin, monkeypatch):
    if not DB_AVAILABLE:
        pytest.skip("需要 PostgreSQL")
    from app.ops.capability import (
        DbIdempotencyStore,
        DbReceiptSink,
        set_idempotency_store,
        set_receipt_sink,
    )

    set_idempotency_store(DbIdempotencyStore(lease_seconds=120))
    set_receipt_sink(DbReceiptSink())
    try:
        body = (await client.get(f"{BASE}/runtime")).json()
        assert body["persistence"]["mode"] == "db"
        assert body["persistence"]["production_safe"] is True
        assert body["health"]["level"] == "ok"
    finally:
        reset_idempotency_store()


# ---------------- /catalog ----------------


async def test_catalog_lists_visible_and_explains_hidden(client, as_admin):
    """★ 这个端点的价值就是**能回答"为什么他没看到"**。

    注意标签：必须带 `oa` 才会豁免 `kinds` 裁剪，否则它**在到达可见性判定之前**
    就被形态裁剪掉了——那时 `visibility_hidden` 里不会有它，
    而 `visible_ids` 里也没有它，看起来像"凭空消失"。
    **裁剪顺序是 kinds → 可见性**，这条顺序本身也是要被观测到的事实。
    """
    spec = CapabilitySpec(
        capability_id="dept_only_cap",
        kind="http",
        description="只有财务部能看",
        args_schema={"type": "object", "properties": {}},
        tags=("oa",),  # 豁免 kinds 裁剪，才能走到可见性判定
        side_effect="read",
        when_to_use="单测",
        visibility={"departments": ["finance"]},
        http={},
    )
    register(spec, GenericHttpAdapter(spec))
    try:
        anon = (await client.get(f"{BASE}/catalog")).json()
        assert "dept_only_cap" not in anon["visible_ids"]
        hidden = {h["capability_id"]: h["reason"] for h in anon["visibility_hidden"]}
        assert hidden.get("dept_only_cap") == "department_mismatch"
        assert anon["principal"]["anonymous"] is True

        fin = (
            await client.get(f"{BASE}/catalog", params={"departments": "finance,hr"})
        ).json()
        assert "dept_only_cap" in fin["visible_ids"]
        assert fin["principal"]["departments"] == ["finance", "hr"]
    finally:
        unregister("dept_only_cap")


async def test_catalog_shows_kinds_crop_wins_over_visibility(client, as_admin):
    """无域标签的 http 能力被 **kinds 裁剪**掉，不是被可见性裁掉——两者要分得清。"""
    spec = CapabilitySpec(
        capability_id="untagged_http_cap",
        kind="http",
        description="没有 oa 标签的 http 能力",
        args_schema={"type": "object", "properties": {}},
        side_effect="read",
        when_to_use="单测",
        visibility={"departments": ["all"]},
        http={},
    )
    register(spec, GenericHttpAdapter(spec))
    try:
        body = (await client.get(f"{BASE}/catalog")).json()
        assert "untagged_http_cap" not in body["visible_ids"]
        # 不在 hidden 里 —— 它没走到可见性判定，是被形态裁剪掉的
        assert "untagged_http_cap" not in {
            h["capability_id"] for h in body["visibility_hidden"]
        }
    finally:
        unregister("untagged_http_cap")


async def test_catalog_reports_the_filter_in_effect(client, as_admin):
    """基线开着时，`deny_write` / `allow_tags_any` 要能看见——否则"为什么看不到"还是答不出。"""
    body = (await client.get(f"{BASE}/catalog", params={"baseline": "true"})).json()
    assert body["filter"]["baseline"] is True
    assert body["filter"]["deny_write"] is True
    assert body["filter"]["deny_high_risk"] is True
    assert body["filter"]["allow_tags_any"] == ["oa"]

    raw = (await client.get(f"{BASE}/catalog", params={"baseline": "false"})).json()
    assert raw["filter"]["kinds"] is None


async def test_catalog_denies_write_capabilities_in_baseline(client, as_admin):
    spec = CapabilitySpec(
        capability_id="oa.write.probe",
        kind="http",
        description="探针写能力",
        args_schema={"type": "object", "properties": {}},
        tags=("oa",),
        side_effect="write",
        when_to_use="单测",
        visibility={"departments": ["all"]},
        http={},
    )
    register(spec, GenericHttpAdapter(spec))
    try:
        body = (await client.get(f"{BASE}/catalog")).json()
        assert "oa.write.probe" not in body["visible_ids"]  # deny_write 生效
    finally:
        unregister("oa.write.probe")


# ---------------- /metrics ----------------


async def test_metrics_exposes_write_blocked_counter(client, as_admin):
    """★ 最该被盯的数字：**被 Policy 拦下的写有多少次**。

    只看 `ok` 是看不出这件事的——写闸把请求拦了，调用方只看到"失败"，
    没有指标就没人能回答"到底有多少写被拦下了"。
    """
    from app.ops.capability import GenericHttpAdapter as _A
    from app.ops.capability import metrics as cap_metrics

    cap_metrics.reset()
    spec = CapabilitySpec(
        capability_id="metrics.write.probe",
        kind="http",
        description="探针写能力",
        args_schema={"type": "object", "properties": {"subject": {"type": "string"}}},
        tags=("oa",),
        side_effect="write",
        hitl_required=True,
        when_to_use="单测",
        visibility={"departments": ["all"]},
        http={"idempotency_key": "t:{{subject}}"},
    )
    register(spec, _A(spec))
    try:
        from app.ops.capability import invoke

        invoke("metrics.write.probe", {"subject": "x"}, ctx={"tenant_id": "t1"})  # 无放行 → 拦
        invoke("metrics.write.probe", {"subject": "x"}, ctx={"tenant_id": "t1"})  # 再来一次

        body = (await client.get(f"{BASE}/metrics")).json()
        assert body["scope"] == "process_local"
        assert body["write"]["blocked"] >= 2
        assert body["by_outcome"]["policy_blocked"] >= 2
        assert body["by_capability"]["metrics.write.probe"]["policy_blocked"] >= 2
    finally:
        unregister("metrics.write.probe")
        cap_metrics.reset()


# ---------------- /receipts 与 /idempotency ----------------


async def test_receipts_endpoint(client, as_admin):
    resp = await client.get(f"{BASE}/receipts", params={"limit": 5})
    if not DB_AVAILABLE:
        assert resp.status_code == 503
        return
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == len(body["receipts"])
    assert "persistence" in body


async def test_idempotency_endpoint_exposes_stuck_rows(client, as_admin):
    """★ 租约巡检：只列**租约已过期的 in_flight**——那些是"发出去了但不知道结果"的写。"""
    if not DB_AVAILABLE:
        pytest.skip("需要 PostgreSQL")
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    tenant = "obs-test-tenant"
    key = "obs-stuck-key"
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_capability_idempotency WHERE tenant_id = :t"),
            {"t": tenant},
        )
        # 造一条**租约已过期**的 in_flight（模拟"进程崩在发出请求与落回执之间"）
        await session.execute(
            text(
                "INSERT INTO ops_capability_idempotency "
                "(id, tenant_id, idempotency_key, capability_id, status, "
                " lease_expires_at, attempts, created_at, updated_at) "
                "VALUES (CAST(:id AS uuid), :t, :k, 'oa.ticket.create', 'in_flight', "
                " now() - interval '10 minutes', 1, now(), now())"
            ),
            {"id": "00000000-0000-0000-0000-000000000001", "t": tenant, "k": key},
        )
    try:
        body = (
            await client.get(
                f"{BASE}/idempotency", params={"tenant_id": tenant, "stuck_only": "true"}
            )
        ).json()
        keys = [r["idempotency_key"] for r in body["rows"]]
        assert key in keys
        assert body["needs_reconcile"] == 1
        assert body["hint"] and "不要直接重试" in body["hint"]
        assert all(r["status"] == "in_flight" for r in body["rows"])

        # 不带 stuck_only 时也能看到（全量列出）
        allrows = (await client.get(f"{BASE}/idempotency", params={"tenant_id": tenant})).json()
        assert any(r["idempotency_key"] == key for r in allrows["rows"])
    finally:
        async with AsyncSessionLocal() as session, session.begin():
            await session.execute(
                text("DELETE FROM ops_capability_idempotency WHERE tenant_id = :t"),
                {"t": tenant},
            )
