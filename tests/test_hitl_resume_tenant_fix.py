"""T-fix-1/T-fix-2 · HG-W-TENANT-DESIGN 裁决接线（api-w-hitl-tenant-fix · 30 棒）。

裁决值（PR #312 review 维护者签认 · auth311 · task 档钉死契约表）：

- **① A+B 组合**：单据 ``tenant_id`` 为唯一真源 —— resume 执行体驱动图前按
  单据快照 ``set_current_tenant`` 还原；手动入口 session 租户存在且 ≠ 单据
  tenant → 403（对齐 ``lg_rag/router.py:376-384`` 先例）；Bearer 机读 /
  auto-scan 无 session 上下文 → 纯 A（仅快照）；**fail-closed：单据 tenant
  为空 → 拒 resume**（历史 ``''`` 40 行同口径 · 不回填）。
- **② delegation 消费守卫扩列**：``_WRITE_CONSUMABLE_BLOCKED_BY`` 两类单据
  均查租户（T-fix-2 打戳后守卫查非空成立）。
- 回执/消费日志 tenant 取还原后的运行上下文 —— N-R2-1 现场
  （回执 ``d6bd262904544232`` 错标 ``ops-desk-pilot``）不复发为硬验收。
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

import app.ops.hitl.router as router_mod
from app.ops.hitl.persistence import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import STATUS_APPROVED, InMemoryHitlStore
from app.ops.tenant_context import (
    TENANT_A,
    TENANT_B,
    current_tenant,
    reset_current_tenant,
    set_current_tenant,
)
from tests.test_hitl_resume import _RUN, _approved_row, _client, _drain


@pytest.fixture(autouse=True)
def _isolate():
    """store 隔离 + ContextVar 净空（快照还原测试要求无 ambient tenant）。"""
    reset_hitl_store()
    token = set_current_tenant(None)
    yield
    reset_current_tenant(token)
    reset_hitl_store()
    router_mod._RESUME_IN_FLIGHT.clear()


def _decided(store: InMemoryHitlStore, **row_kw) -> dict:
    row = _approved_row(**row_kw)
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="验收"))
    return row


# ---------------------------------------------------------------------------
# T-fix-1 ① · 执行体快照还原（auto-scan 纯 A 形态同覆盖：同一执行体）
# ---------------------------------------------------------------------------


def test_execute_resume_restores_row_tenant_snapshot():
    """单据 tenant=B · 无 ambient 租户 ⇒ 恢复段 ContextVar = B（快照还原），
    消费环不再回落默认租户 A（N-R2-1 现场根治）。"""
    store = InMemoryHitlStore()
    created = _decided(store, tenant_id=TENANT_B)
    set_hitl_store(store)
    # 执行体消费 store 里已决行（端点同款取法），不用过期的 pre-decide 副本。
    row = asyncio.run(store.aget(created["id"]))

    seen: list = []

    async def _spy(**kwargs):
        from app.ops.tenant_context import current_tenant_or_default

        seen.append(current_tenant_or_default())
        return {"thread_id": kwargs["thread_id"], "state": {}, "answer": "", "query": ""}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_spy),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
    ):
        out = asyncio.run(router_mod._execute_decided_resume(row))

    assert seen == [TENANT_B], f"恢复段租户应为单据快照 {TENANT_B}，实际 {seen}"
    assert current_tenant() is None, "reset 未成对 —— ContextVar 泄漏到后续用例"
    assert out["req_status"] == STATUS_APPROVED


def test_execute_resume_empty_tenant_fail_closed():
    """裁决① fail-closed：单据 tenant 为空 → 拒 resume（历史 '' 40 行口径）。"""
    store = InMemoryHitlStore()
    row = _decided(store, tenant_id="")
    set_hitl_store(store)

    from app.ops.hitl.resume import ResumeError

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=AsyncMock()),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        pytest.raises(ResumeError) as exc_info,
    ):
        asyncio.run(router_mod._execute_decided_resume(row))

    assert exc_info.value.code == "tenant_missing"


# ---------------------------------------------------------------------------
# T-fix-1 ① · 手动入口 session 守卫（A+B 组合的 B 面）
# ---------------------------------------------------------------------------


def test_resume_endpoint_session_tenant_mismatch_403(monkeypatch):
    """session 租户 B ≠ 单据租户 A → 403（对齐 lg_rag/router.py:376-384 先例），
    后台执行零派发。"""
    store = InMemoryHitlStore()
    row = _decided(store, tenant_id=TENANT_A)

    executed: list = []

    async def _spy(**kwargs):
        executed.append(kwargs)
        return {"thread_id": kwargs["thread_id"], "state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_spy),
        _client(monkeypatch, store, tenant=TENANT_B) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 403, res.text
    assert "tenant" in res.json()["detail"]
    assert executed == [], "403 后不许再驱动恢复"


def test_resume_endpoint_session_tenant_match_accepted(monkeypatch):
    """session 租户 = 单据租户 → 200 受理（同租户正样本不误拒）。"""
    store = InMemoryHitlStore()
    row = _decided(store, tenant_id=TENANT_A)

    async def _spy(**kwargs):
        return {"thread_id": kwargs["thread_id"], "state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_spy),
        _client(monkeypatch, store, tenant=TENANT_A) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()

    assert res.status_code == 200, res.text
    assert res.json()["resume"]["status"] == "accepted"


def test_resume_endpoint_bearer_no_session_pure_snapshot(monkeypatch):
    """Bearer 机读（无 session 租户 → state 未设置）→ 不 403，纯快照受理。"""
    store = InMemoryHitlStore()
    row = _decided(store, tenant_id=TENANT_B)

    seen: list = []

    async def _spy(**kwargs):
        from app.ops.tenant_context import current_tenant_or_default

        if kwargs.get("preflight_only"):
            return {"preflight": True}
        seen.append(current_tenant_or_default())
        return {"thread_id": kwargs["thread_id"], "state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_spy),
        _client(monkeypatch, store) as client,  # 默认：不注入 ops_tenant_id
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()

    assert res.status_code == 200, res.text
    assert seen == [TENANT_B], "Bearer 形态也应按单据快照还原租户"


def test_resume_endpoint_empty_tenant_409(monkeypatch):
    """手动入口 fail-fast：单据 tenant 为空 → 请求内 409（不打后台）。"""
    store = InMemoryHitlStore()
    row = _decided(store, tenant_id="")

    executed: list = []

    async def _spy(**kwargs):
        executed.append(kwargs)
        return {"thread_id": kwargs["thread_id"], "state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_spy),
        _client(monkeypatch, store, tenant=TENANT_A) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 409, res.text
    assert "tenant" in res.json()["detail"]
    assert executed == []


# ---------------------------------------------------------------------------
# T-fix-2 · delegation 建单打戳（对齐 capability_write :1881-1925 先例形态）
# ---------------------------------------------------------------------------


def test_delegation_blocked_terminal_stamps_current_tenant():
    """delegation 签发拦截 terminal 补租户戳：当前租户 B → terminal tenant=B。"""
    from app.ops.lg_rag.multi.nodes import _delegation_blocked_terminal

    row = {"subtask_id": f"{_RUN}:9", "type": "tool", "tool": "testing.write.echo"}
    token = set_current_tenant(TENANT_B)
    try:
        blocked = _delegation_blocked_terminal(row, "委派签发需人工审批（测试）")
    finally:
        reset_current_tenant(token)

    assert blocked["blocked_by"] == "delegation_issue_hitl_required"
    assert blocked["hitl_required"] is True
    assert blocked["tenant_id"] == TENANT_B, "delegation 拦截未打租户戳（F3 真空）"


def test_delegation_blocked_terminal_default_tenant_a():
    """无请求上下文（CLI/扫描）→ 回落试点 A（对齐 capability_write 先例同口径）。"""
    from app.ops.lg_rag.multi.nodes import _delegation_blocked_terminal

    row = {"subtask_id": f"{_RUN}:10", "type": "tool", "tool": "testing.write.echo"}
    blocked = _delegation_blocked_terminal(row, "委派签发需人工审批（测试）")
    assert blocked["tenant_id"] == TENANT_A


# ---------------------------------------------------------------------------
# 守卫预登记（delegation 扩列负样本 · 详见 test_write_approval_gate W2 组增补）
# ---------------------------------------------------------------------------
# 说明：消费守卫扩列（_write_execution_approval 两类查租户）的负样本与
# 「空 tenant fail-closed」负样本落在 tests/test_write_approval_gate.py（复用
# write_env fixture），与本文件同源同裁决值。
