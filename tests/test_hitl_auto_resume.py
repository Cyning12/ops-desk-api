"""HITL 批准后自动恢复（T2 · SPEC D5）验收断言：TB1–TB6 逐条断言化。

钉住的语义：

- **配置面（Q7）**：```OPS_HITL_AUTO_RESUME``` 缺省/非法=manual（零 diff）· auto；
  decide 载荷 ```resume_mode``` 白名单——未知值 **400**（R2-N1 · 非 Pydantic 422），
  缺键=inherit；```decision``` 非法仍 422（既有形态一行不动）。
- **触发器（R2-N2）**：decide 成功分支派发进程内 asyncio 任务，与手动 resume
  **同一条恢复路径**（```_execute_decided_resume``` 同源）；manual 形态零派发零扫描。
- **防重（FP-8 · R2-N3）**：Db 组真 PG 行锁（FOR UPDATE SKIP LOCKED）并发认领仅一成功；
  InMemory **无行锁语义**，只承载状态机幂等断言（禁假断言 · 实操-C）。
- **兜底（FP-9）**：补偿扫描补触发「approved 未过 TTL ∧ run 无终态 ∧ 无未决 pending」；
  不循环（FP-11）：auto 后仍拦 → 新 pending → 扫描跳过等人。
- **台账**：hitl_auto_resume_triggered / claimed / compensated（记动作不记内容）。

行锁断言仅 Db 组（真 PG fixture 承 test_hitl_resume.py 形态）；DB 不可用时跳过。
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.hitl import auto_resume
from app.ops.hitl.persistence import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import ResumeError
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    InMemoryHitlStore,
    NullHitlStore,
    new_request_id,
)
from tests.conftest import DB_AVAILABLE

_MAINTAINER_ID = "00000000-0000-0000-0000-000000000001"
_RUN = "runauto"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"
_TOOL = "mock_get_issue_status"


@pytest.fixture(autouse=True)
def _isolate():
    reset_hitl_store()
    yield
    reset_hitl_store()
    # 后台任务不跨用例泄漏（实操-D 对称面）：统一收尸
    for task in list(auto_resume._BACKGROUND_TASKS):
        task.cancel()


# ---------------------------------------------------------------------------
# 测试夹具：行构造 / owner 替身 / async 客户端 / 图替身（承 test_hitl_pending_decide）
# ---------------------------------------------------------------------------


def _row(**kw) -> dict:
    base = {
        "id": new_request_id(),
        "run_id": _RUN,
        "thread_id": "t-auto",
        "subtask_id": _T2,
        "unlock_subtask_id": _T1,
        "blocked_by": "prefix_touch_required",
        "reason": "需要重跑已执行步骤",
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    base.update(kw)
    return base


def _owner_map(mapping):
    async def _fake(run_id: str):
        return mapping.get(run_id)

    return _fake


def _bare_app(*, user_id: str = _MAINTAINER_ID):
    """裸 FastAPI app + hitl router（async 用例与同一事件循环，便于 drain 后台任务）。"""
    from functools import wraps

    from fastapi import FastAPI

    from app.db.models import OpsUser
    from app.ops.deps import get_current_user
    from app.ops.hitl.router import router

    user = OpsUser(id=user_id, username="admin", role="maintainer")

    @wraps(get_current_user)
    async def _fake(*args, **kwargs):
        return user

    app = FastAPI()
    app.include_router(router, prefix="/api/ops")
    app.dependency_overrides[get_current_user] = _fake
    return app


def _graph_factory(*, checkpointer):
    """最小 observe 图替身（承 test_hitl_resume.py harness · sid 保留形态）。"""
    from langgraph.graph import END, START, StateGraph

    from app.ops.lg_rag.multi.nodes import observe_node, route_after_react
    from app.ops.lg_rag.state import LgRagState

    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


def _hitl_state(**kw) -> dict:
    base = {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "thread_id": "t-auto",
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 1,
        "host_subtask_seq": 2,
        "react_round": 0,
        "inflight_subtask_ids": [],
        "subtasks": [
            {"id": _T1, "subtask_id": _T1, "alias": "t1", "type": "tool", "tool": _TOOL, "input": "x", "depends_on": []},
            {"id": _T2, "subtask_id": _T2, "alias": "t2", "type": "tool", "tool": _TOOL, "input": "x", "depends_on": [_T1]},
        ],
        "subtask_results": [
            {"subtask_id": _T1, "type": "tool", "output": {"assignee": "张三"}},
            {"subtask_id": _T2, "type": "tool", "error": "需要重跑已执行步骤", "blocked_by": "prefix_touch_required", "hitl_required": True},
        ],
        "plan_prefix_ids": [_T1],
    }
    base.update(kw)
    return base


async def _suspend(state: dict, saver: InMemorySaver, thread_id: str):
    graph = _graph_factory(checkpointer=saver)
    payload = None
    async for chunk in graph.astream(
        state, {"configurable": {"thread_id": thread_id}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            payload = intr.value
    return payload


def _resume_via(saver, calls: list | None = None):
    """真驱动器 + 注入内存 saver/图替身；calls 传入时记录每次调用。"""
    from app.ops.hitl.resume import resume_hitl_run as real

    async def _wrapped(**kw):
        if calls is not None:
            calls.append(kw)
        return await real(checkpointer=saver, graph_factory=_graph_factory, **kw)

    return _wrapped


async def _drain_background(timeout: float = 5.0) -> None:
    """等后台任务集合清空（auto 派发异步 · 同事件循环可 await）。"""
    deadline = time.monotonic() + timeout
    while auto_resume._BACKGROUND_TASKS and time.monotonic() < deadline:
        await asyncio.sleep(0.02)
    assert not auto_resume._BACKGROUND_TASKS, "后台任务未在限时内收尾"


# ---------------------------------------------------------------------------
# TB2⑤ · 配置面：env 解析 / 有效模式求解 / 扫描周期域
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,want",
    [
        (None, "manual"),  # 缺省
        ("", "manual"),
        ("manual", "manual"),
        ("auto", "auto"),
        (" AUTO ", "auto"),  # strip + 大小写
        ("banana", "manual"),  # 非法回退 manual（fail-closed）
        ("0", "manual"),
    ],
)
def test_env_auto_resume_parse(monkeypatch, raw, want):
    if raw is None:
        monkeypatch.delenv("OPS_HITL_AUTO_RESUME", raising=False)
    else:
        monkeypatch.setenv("OPS_HITL_AUTO_RESUME", raw)
    assert auto_resume.auto_resume_mode() == want


def test_env_invalid_logs_error(monkeypatch, caplog):
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "banana")
    with caplog.at_level(logging.ERROR, logger="app.ops.hitl.auto_resume"):
        assert auto_resume.auto_resume_mode() == "manual"
    assert any("OPS_HITL_AUTO_RESUME" in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize(
    "env,mode,want",
    [
        (None, "inherit", "manual"),  # inherit → 全局默认 manual
        ("auto", "inherit", "auto"),  # inherit → 全局 auto
        ("auto", "manual", "manual"),  # 单据覆盖压过全局
        (None, "immediate", "auto"),  # immediate 无视全局 manual
        ("auto", "immediate", "auto"),
        ("banana", "inherit", "manual"),  # 非法 env 回退后 inherit=manual
    ],
)
def test_resolve_resume_mode(monkeypatch, env, mode, want):
    if env is None:
        monkeypatch.delenv("OPS_HITL_AUTO_RESUME", raising=False)
    else:
        monkeypatch.setenv("OPS_HITL_AUTO_RESUME", env)
    assert auto_resume.resolve_resume_mode(mode) == want


def test_resolve_unknown_mode_fail_closed(monkeypatch):
    """绕过端点白名单直调求解：未知值同样 fail-closed 回 manual。"""
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "auto")
    assert auto_resume.resolve_resume_mode("bogus") == "manual"


@pytest.mark.parametrize(
    "raw,want",
    [(None, 60), ("", 60), ("5", 5), ("3600", 3600), ("4", 60), ("3601", 60), ("abc", 60)],
)
def test_scan_interval_parse(monkeypatch, raw, want):
    if raw is None:
        monkeypatch.delenv("OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS", raising=False)
    else:
        monkeypatch.setenv("OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS", raw)
    assert auto_resume.scan_interval_seconds() == want


# ---------------------------------------------------------------------------
# TB2④ · resume_mode 白名单：未知值 400（非 422 · R2-N1 / 实操-A）
# ---------------------------------------------------------------------------


async def test_decide_resume_mode_unknown_400_not_422():
    store = InMemoryHitlStore()
    row = _row()
    await store.acreate(row)
    set_hitl_store(store)
    owner = _owner_map({_RUN: _MAINTAINER_ID})
    from httpx import ASGITransport, AsyncClient

    with patch("app.ops.lg_rag.event_store.run_owner", new=owner):
        async with AsyncClient(
            transport=ASGITransport(app=_bare_app()), base_url="http://test"
        ) as client:
            bad = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide",
                json={"decision": "approved", "resume_mode": "bogus"},
            )
            assert bad.status_code == 400, bad.text  # SPEC FP-10：400 非 422
            # 对照钉：decision 非法仍是 Pydantic 422（既有形态一行不动）
            bad_decision = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide",
                json={"decision": "bogus", "resume_mode": "immediate"},
            )
            assert bad_decision.status_code == 422, bad_decision.text
    # 400 不落 decide：单据仍是 pending（白名单校验在 adecide 之前）
    assert (await store.aget(row["id"]))["status"] == STATUS_PENDING


# ---------------------------------------------------------------------------
# TB6 · manual/off 零 diff（SPEC A6 本 task 面）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("env", [None, "banana"])  # 缺省 / 非法 都=manual
async def test_decide_manual_resume_block_literal_unchanged(monkeypatch, env):
    """manual 形态响应 `resume` 块与 master 字面一致（快照对拍 · 实操-F）。"""
    if env is None:
        monkeypatch.delenv("OPS_HITL_AUTO_RESUME", raising=False)
    else:
        monkeypatch.setenv("OPS_HITL_AUTO_RESUME", env)
    store = InMemoryHitlStore()
    row = _row()
    await store.acreate(row)
    set_hitl_store(store)
    owner = _owner_map({_RUN: _MAINTAINER_ID})
    from httpx import ASGITransport, AsyncClient

    with patch("app.ops.lg_rag.event_store.run_owner", new=owner):
        async with AsyncClient(
            transport=ASGITransport(app=_bare_app()), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
            )
    assert res.status_code == 200, res.text
    assert res.json()["resume"] == {
        "required": True,
        "method": "POST",
        "endpoint": f"/api/ops/hitl/requests/{row['id']}/resume",
    }


async def test_manual_mode_dispatches_nothing(monkeypatch):
    """manual（含 delegation off 面）：spy 断言零派发 · 零后台任务（TB6 零 diff）。"""
    monkeypatch.delenv("OPS_HITL_AUTO_RESUME", raising=False)
    monkeypatch.setenv("LG_RAG_DELEGATION_TOKEN_MODE", "off")
    store = InMemoryHitlStore()
    row = _row()
    await store.acreate(row)
    set_hitl_store(store)
    owner = _owner_map({_RUN: _MAINTAINER_ID})
    from httpx import ASGITransport, AsyncClient

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch.object(auto_resume, "schedule_auto_resume") as spy,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=_bare_app()), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide",
                json={"decision": "approved", "resume_mode": "manual"},
            )
    assert res.status_code == 200, res.text
    spy.assert_not_called()
    assert not auto_resume._BACKGROUND_TASKS


def test_lifespan_manual_creates_no_scan_task(monkeypatch):
    """manual 默认下 lifespan **零创建**扫描任务（实操-D · TestClient 8 文件面）。"""
    from fastapi.testclient import TestClient

    from app.main import app as fastapi_app

    monkeypatch.delenv("OPS_HITL_AUTO_RESUME", raising=False)
    with (
        patch.object(auto_resume, "start_compensation_scanner") as spy,
        TestClient(fastapi_app) as client,
    ):
        assert client.get("/health").status_code == 200
    spy.assert_not_called()
    assert auto_resume._SCAN_TASK is None


def test_lifespan_auto_starts_then_cancels_scan(monkeypatch):
    """auto 下 lifespan 启动周期任务；shutdown cancel + 句柄清空（实操-D）。"""
    from fastapi.testclient import TestClient

    from app.main import app as fastapi_app

    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "auto")
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS", "3600")
    with TestClient(fastapi_app) as client:
        assert client.get("/health").status_code == 200
        task = auto_resume._SCAN_TASK
        assert task is not None and not task.done()
    assert auto_resume._SCAN_TASK is None, "shutdown 后句柄必须清空（任务泄漏坑）"
    assert task.cancelled() or task.done()


# ---------------------------------------------------------------------------
# TB1 · auto 全链（SPEC A9 机制段）：decide 后无需手动 resume → 自动恢复
# ---------------------------------------------------------------------------


async def test_auto_decide_auto_resumes_without_manual_call(monkeypatch, caplog):
    """A9 机制段：挂起 run → decide(approved, resume_mode=immediate) →
    **不调 resume 端点** → 后台任务走同源路径把图跑完（解锁 + replan  verdict）。

    注：live 全链（真 supervisor 图 replan 重盖章面）留 40 复跑——T1 40 已登记
    重盖章致消费键失配的 live 偏差；本断言钉的是「decide→自动恢复→图继续」机制段，
    消费成环机制由 T1 TA3（sid 保留形态）钉死。
    """
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "manual")  # 全局 manual，单据 immediate 覆盖
    store = InMemoryHitlStore()
    saver = InMemorySaver()
    payload = await _suspend(_hitl_state(), saver, "t-auto-chain")
    assert payload is not None, "前置：图没有挂起"
    row = _row(thread_id="t-auto-chain")
    await store.acreate(row)
    set_hitl_store(store)
    owner = _owner_map({_RUN: _MAINTAINER_ID})
    calls: list = []
    from httpx import ASGITransport, AsyncClient

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch("app.ops.hitl.router.resume_hitl_run", new=_resume_via(saver, calls)),
        patch(
            "app.ops.lg_rag.event_store.run_is_terminal", new=AsyncMock(return_value=False)
        ),
        caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=_bare_app()), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide",
                json={"decision": "approved", "resume_mode": "immediate"},
            )
            assert res.status_code == 200, res.text
            # auto 形态响应注明已触发（manual 字面零 diff 的反面）
            assert res.json()["resume"]["auto_triggered"] is True
            assert res.json()["resume"]["required"] is False
            # 不手动调 resume —— 等后台任务把图跑完
            await _drain_background()
    assert len(calls) == 1, f"自动恢复应恰好执行一次，实际 {len(calls)}"
    assert calls[0]["approved"] == [_T1]
    graph = _graph_factory(checkpointer=saver)
    snap = await graph.aget_state({"configurable": {"thread_id": "t-auto-chain"}})
    assert snap.values["hitl_unlocked_ids"] == [_T1], "批了却没解锁"
    assert snap.values["react_observation"]["verdict"] == "replan"
    messages = [r.getMessage() for r in caplog.records]
    assert any(m.startswith("hitl_auto_resume_triggered") for m in messages)
    assert any(m.startswith("hitl_auto_resume_claimed") for m in messages)


# ---------------------------------------------------------------------------
# Db 组（真 PG · 承 test_hitl_resume.py fixture 形态）：行锁 / 终态 / 重启链
# ---------------------------------------------------------------------------


def _db_prefix(tag: str) -> str:
    return f"hitl_t2{tag}_{uuid.uuid4().hex[:6]}_"


async def _db_cleanup(prefix: str, run_ids: list[str] | None = None) -> None:
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM ops_hitl_requests WHERE id LIKE :p"), {"p": f"{prefix}%"}
        )
        for rid in run_ids or []:
            await db.execute(
                text("DELETE FROM ops_lg_rag_run_events WHERE run_id = :r"), {"r": rid}
            )
        await db.commit()


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_claim_skip_locked_only_one_succeeds():
    """TB2③/TB3（Db 组 · FP-8）：一连接持行锁时，并发认领返回 None（SKIP LOCKED
    跳过锁定行）；锁释放后认领成功——**并发双认领仅一成功**的确定性钉法。"""
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal
    from app.ops.hitl.store import DbHitlStore

    store = DbHitlStore()
    prefix = _db_prefix("lock")
    rid = f"{prefix}a"
    await _db_cleanup(prefix)
    try:
        await store.acreate(_row(id=rid, run_id=f"run-{uuid.uuid4().hex[:8]}"))
        await store.adecide(rid, decision=STATUS_APPROVED, by="验收")
        async with AsyncSessionLocal() as holder, holder.begin():
            await holder.execute(
                text("SELECT id FROM ops_hitl_requests WHERE id = :id FOR UPDATE"),
                {"id": rid},
            )
            # 锁被持有期间：认领必须跳过（模拟另一副本/扫描同时命中）
            assert await store.aclaim_approved_for_resume(rid, ttl_seconds=3600) is None
        claimed = await store.aclaim_approved_for_resume(rid, ttl_seconds=3600)
        assert claimed is not None and claimed["status"] == STATUS_APPROVED
    finally:
        await _db_cleanup(prefix)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_claim_condition_filters():
    """TB2③ 条件组（Db）：非 approved / 过 TTL / 同 run 有未决 pending → 均不可认领。"""
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal
    from app.ops.hitl.store import DbHitlStore

    store = DbHitlStore()
    prefix = _db_prefix("flt")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    fresh, stale, blocked, rejected = (f"{prefix}{t}" for t in ("f", "s", "b", "r"))
    await _db_cleanup(prefix)
    try:
        await store.acreate(_row(id=fresh, run_id=f"run-{uuid.uuid4().hex[:8]}"))
        await store.acreate(_row(id=stale, run_id=f"run-{uuid.uuid4().hex[:8]}"))
        await store.acreate(_row(id=blocked, run_id=run_id))
        await store.acreate(_row(id=rejected, run_id=f"run-{uuid.uuid4().hex[:8]}"))
        for rid, dec in ((fresh, STATUS_APPROVED), (stale, STATUS_APPROVED),
                         (blocked, STATUS_APPROVED), (rejected, STATUS_REJECTED)):
            await store.adecide(rid, decision=dec, by="验收")
        # 过期：decided_at 拨回 2h（SQL 层真改 · 承 T1 TA2⑧ 形态）
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("UPDATE ops_hitl_requests SET decided_at = now() - interval '2 hours' WHERE id = :id"),
                {"id": stale},
            )
            await db.commit()
        # 同 run 未决 pending（FP-11 第四条件）
        await store.acreate(_row(id=f"{prefix}pend", run_id=run_id))
        assert await store.aclaim_approved_for_resume(fresh, ttl_seconds=3600) is not None
        assert await store.aclaim_approved_for_resume(stale, ttl_seconds=3600) is None
        assert await store.aclaim_approved_for_resume(blocked, ttl_seconds=3600) is None
        assert await store.aclaim_approved_for_resume(rejected, ttl_seconds=3600) is None
        assert await store.aclaim_approved_for_resume(f"{prefix}ghost", ttl_seconds=60) is None
    finally:
        await _db_cleanup(prefix)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_auto_chain_terminal_done_frame(seeded_maintainer, monkeypatch, caplog):
    """TB1 终态半（Db 组）：decide(immediate) → 自动恢复走完同源路径 →
    sink 落 `done{resumed}` → `run_is_terminal` 翻 True → 补偿扫描不再补触发。

    resume 驱动器打桩（不跑真图），其余全真：DbHitlStore / event_store /
    _open_event_sink / ResumeEventSink。
    """
    from app.ops.lg_rag.event_store import persist_run_event, run_is_terminal

    user = seeded_maintainer["user"]
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "manual")
    store_mod = __import__("app.ops.hitl.store", fromlist=["DbHitlStore"])
    store = store_mod.DbHitlStore()
    set_hitl_store(store)
    prefix = _db_prefix("term")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    rid = f"{prefix}a"
    await _db_cleanup(prefix, [run_id])
    try:
        await store.acreate(_row(id=rid, run_id=run_id, thread_id="t-term"))
        await persist_run_event(
            run_id=run_id, seq=1, user_id=str(user.id), thread_id="t-term",
            ts_ms=0, agent_role="system", event_type="run.start", payload={"query": "q"},
        )
        assert await run_is_terminal(run_id) is False

        async def _stub_resume(**kw):
            return {"state": {}, "answer": "", "query": ""}

        from httpx import ASGITransport, AsyncClient

        with (
            patch("app.ops.hitl.router.resume_hitl_run", new=_stub_resume),
            caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=_bare_app(user_id=str(user.id))),
                base_url="http://test",
            ) as client:
                res = await client.post(
                    f"/api/ops/hitl/requests/{rid}/decide",
                    json={"decision": "approved", "resume_mode": "immediate"},
                )
                assert res.status_code == 200, res.text
                assert res.json()["resume"]["auto_triggered"] is True
                await _drain_background()
        assert await run_is_terminal(run_id) is True, "恢复后 sink 的 done 帧应使 run 终态"
        # 终态后补偿扫描不再补触发（TB2② 幂等半 · 裁定四第三条件）
        assert await auto_resume.scan_approved_not_resumed_once() == 0
        messages = [r.getMessage() for r in caplog.records]
        assert any(m.startswith("hitl_auto_resume_triggered") for m in messages)
        assert any(m.startswith("hitl_auto_resume_claimed") for m in messages)
    finally:
        await _db_cleanup(prefix, [run_id])


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_scan_compensates_after_store_rebuild(caplog):
    """TB4（FP-9 崩溃兜底 · 真 PG 重启链形态）：approved 单据落库后「进程重启」
    （丢弃旧 store 实例、新建 DbHitlStore 重装）→ 补偿扫描补触发 + 台账。

    幂等半（TB2②）：执行后补一条同 run 未决 pending（模拟仍被拦/在处理），
    第二轮扫描跳过（第四条件）→ dispatched==0。
    """
    from app.ops.hitl.store import DbHitlStore

    prefix = _db_prefix("res")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    rid = f"{prefix}a"
    await _db_cleanup(prefix)
    try:
        seed = DbHitlStore()
        await seed.acreate(_row(id=rid, run_id=run_id, thread_id="t-re"))
        await seed.adecide(rid, decision=STATUS_APPROVED, by="验收")
        # —— 模拟进程重启：全新 store 实例（行锁/单据都在 PG · 触发器不载状态）——
        set_hitl_store(DbHitlStore())
        calls: list = []

        async def _stub_resume(**kw):
            calls.append(kw)
            return {"state": {}, "answer": "", "query": ""}

        with (
            patch("app.ops.hitl.router.resume_hitl_run", new=_stub_resume),
            patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
            caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
        ):
            assert await auto_resume.scan_approved_not_resumed_once() == 1
            await _drain_background()
            assert len(calls) == 1 and calls[0]["approved"] == [_T1]
            # 幂等半：同 run 出现未决 pending → 第二轮扫描跳过
            await DbHitlStore().acreate(_row(id=f"{prefix}pend", run_id=run_id))
            assert await auto_resume.scan_approved_not_resumed_once() == 0
            await _drain_background()
            assert len(calls) == 1, "第二轮扫描不得重复执行"
        messages = [r.getMessage() for r in caplog.records]
        assert any(m.startswith("hitl_auto_resume_compensated") for m in messages)
        assert any(m.startswith("hitl_auto_resume_claimed") for m in messages)
    finally:
        await _db_cleanup(prefix)


# ---------------------------------------------------------------------------
# InMemory 组：状态机幂等（无行锁语义 · 禁假断言 · 实操-C）+ 认领条件
# ---------------------------------------------------------------------------


async def test_inmemory_claim_condition_filters():
    """TB2③（InMemory 组）：条件过滤同源——非 approved/过 TTL/同 run pending 不可认领。"""
    store = InMemoryHitlStore()
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    fresh = _row(run_id=f"run-{uuid.uuid4().hex[:8]}")
    stale = _row(run_id=f"run-{uuid.uuid4().hex[:8]}")
    blocked = _row(run_id=run_id)
    await store.acreate(fresh)
    await store.acreate(stale)
    await store.acreate(blocked)
    for r in (fresh, stale, blocked):
        await store.adecide(r["id"], decision=STATUS_APPROVED, by="验收")
    store._items[stale["id"]]["decided_at"] = time.time() - 7200  # 拨回 2h
    await store.acreate(_row(run_id=run_id))  # 同 run 未决 pending
    assert await store.aclaim_approved_for_resume(fresh["id"], ttl_seconds=3600) is not None
    assert await store.aclaim_approved_for_resume(stale["id"], ttl_seconds=3600) is None
    assert await store.aclaim_approved_for_resume(blocked["id"], ttl_seconds=3600) is None
    assert await store.aclaim_approved_for_resume("ghost", ttl_seconds=60) is None


async def test_inmemory_double_dispatch_state_machine_idempotent(caplog):
    """TB3（InMemory 组）：触发与扫描同时命中同单 → 无行锁可凭，**状态机幂等**
    兜底——第二次恢复撞 not_interrupted 无副作用，实际执行仅一次。"""
    store = InMemoryHitlStore()
    row = _row()
    await store.acreate(row)
    await store.adecide(row["id"], decision=STATUS_APPROVED, by="验收")
    set_hitl_store(store)
    executed: list = []

    async def _stub_resume(**kw):
        if executed:  # 第一次已恢复 → 图不再挂起（状态机守卫）
            raise ResumeError("not_interrupted", "没有挂起的 interrupt")
        executed.append(kw)
        return {"state": {}, "answer": "", "query": ""}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_stub_resume),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch(
            "app.ops.lg_rag.event_store.run_is_terminal", new=AsyncMock(return_value=False)
        ),
        caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
    ):
        auto_resume.schedule_auto_resume(row, resume_mode="inherit", source="decide")
        auto_resume.schedule_auto_resume(row, resume_mode="inherit", source="scan")
        await _drain_background()
    assert len(executed) == 1, "并发双触发仅一执行（状态机幂等）"


# ---------------------------------------------------------------------------
# TB5 · 不循环（FP-11）：auto resume 后仍被拦 → 回挂起等人 · 不再自动触发
# ---------------------------------------------------------------------------


async def test_auto_re_interrupted_no_second_trigger_and_scan_skips(monkeypatch, caplog):
    """auto 恢复后又被拦（构造：恢复后同 run 出现新 pending）→
    台账 triggered 计数 == 1（单次 decide 至多一次）· 扫描跳过（第四条件）。"""
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "auto")  # 全局 auto · inherit 缺省
    store = InMemoryHitlStore()
    saver = InMemorySaver()
    payload = await _suspend(_hitl_state(), saver, "t-loop")
    assert payload is not None
    row = _row(thread_id="t-loop")
    await store.acreate(row)
    set_hitl_store(store)
    owner = _owner_map({_RUN: _MAINTAINER_ID})
    from httpx import ASGITransport, AsyncClient

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch("app.ops.hitl.router.resume_hitl_run", new=_resume_via(saver)),
        patch(
            "app.ops.lg_rag.event_store.run_is_terminal", new=AsyncMock(return_value=False)
        ),
        caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=_bare_app()), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
            )
            assert res.status_code == 200, res.text
            await _drain_background()
            # auto resume 后仍被拦的形态：同 run 新 pending（observe 再拦所产）
            await store.acreate(_row(id=new_request_id(), run_id=_RUN))
            assert await auto_resume.scan_approved_not_resumed_once() == 0
            await _drain_background()
    triggered = [
        r for r in caplog.records if r.getMessage().startswith("hitl_auto_resume_triggered")
    ]
    assert len(triggered) == 1, f"单次 decide 至多一次触发，实际 {len(triggered)}"


async def test_null_store_claim_returns_none():
    """Null 存储（未配持久化）：认领恒 None——不假装认领成功（承 Null 既有纪律）。"""
    assert await NullHitlStore().aclaim_approved_for_resume("x", ttl_seconds=60) is None


# ---------------------------------------------------------------------------
# TB2① · 无状态恢复纪律：源码级断言（触发器不载状态 · 禁 HTTP 自调 · 单一恢复路径）
# ---------------------------------------------------------------------------


def test_trigger_carries_no_state_and_no_http_self_call():
    """SPEC 设计纪律 6 机断：auto_resume 模块级可变态只有任务句柄集合；
    模块源码无 httpx/requests（禁 HTTP 自调）；触发器只带 request_id 进任务。"""
    import ast
    import inspect

    src = inspect.getsource(auto_resume)
    assert "httpx" not in src and "requests.post" not in src, "禁 HTTP 自调"
    tree = ast.parse(src)
    module_assigns = {
        t.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for t in node.targets
        if isinstance(t, ast.Name)
    }
    # 模块级可变态白名单：UPPER_CASE 常量外只允许任务句柄（防 GC · 不载业务状态）
    mutables = {n for n in module_assigns if not n.isupper()}
    assert mutables <= {"logger", "_BACKGROUND_TASKS", "_SCAN_TASK"}, mutables
    assert isinstance(auto_resume._BACKGROUND_TASKS, set)


def test_single_resume_path_in_router():
    """同源钉：router.py 里 `await resume_hitl_run(` 调用点唯一（在抽取的执行体内）。"""
    import inspect

    import app.ops.hitl.router as hitl_router

    src = inspect.getsource(hitl_router)
    assert src.count("await resume_hitl_run(") == 1, "禁止第二条恢复实现"
    assert hasattr(hitl_router, "_execute_decided_resume")

# ---------------------------------------------------------------------------
# hitl-auto-resume-claim-race（30）：竞态窗口注入复现（TC1 修复前红→修复后绿）
# + 修复后 auto decide-同秒链零 stranded_checkpoint（TC2）
# ---------------------------------------------------------------------------


class _RaceWindow:
    """竞态窗口替身（FP-1 注入式构造 · 禁赌真竞态：时序由本对象确定性控制）。

    模拟根因形态（nodes.py:1820-1831「落库先于挂起」）：pending/approved 行
    已可见，但 checkpoint interrupt 元数据**尚不可见**（aget_state 有 pending
    tasks · interrupts 全空）；``flip()`` 后元数据落库可见。live D1 实证
    该窗口为 transient（同码面 ~30s 后自愈）——替身钉的是窗口**形态**而非时长。
    """

    def __init__(self) -> None:
        self.visible = False
        self.probes = 0

    def flip(self) -> None:
        self.visible = True


def _assert_zero_stranded_logs(records) -> None:
    """TC2 台账/caplog 钉：零「HITL 自动恢复执行失败」· 零 stranded_checkpoint 痕迹。"""
    for r in records:
        msg = r.getMessage()
        assert "HITL 自动恢复执行失败" not in msg, msg
        if r.exc_info and r.exc_info[1] is not None:
            assert "stranded_checkpoint" not in repr(r.exc_info[1]), msg


async def test_tc1_claim_race_window_defers_until_metadata_visible(monkeypatch, caplog):
    """TC1 注入式竞态窗口复现（钉死契约 5：本测修复前红 → 修复后绿）。

    窗口内首轮认领（= live D1 decide 同秒首跑形态）：就绪校验未见 interrupt
    元数据 → **不执行不报错**，留 deferred 台账等下轮（竞态化为「等下轮」）；
    元数据可见后同单再认领 → 同源执行直达。stub 编码真实耦合：resume 侧
    aget_state 与就绪校验读同一快照源，窗口内若被执行必撞 stranded_checkpoint
    （resume.py:236-248）。
    """
    store = InMemoryHitlStore()
    row = _row(thread_id="t-race")
    await store.acreate(row)
    await store.adecide(row["id"], decision=STATUS_APPROVED, by="验收")
    set_hitl_store(store)
    window = _RaceWindow()
    attempted: list = []

    async def _fake_visible(r) -> bool:
        window.probes += 1
        return window.visible

    async def _stub_resume(**kw):
        attempted.append(kw)
        if not window.visible:
            raise ResumeError("stranded_checkpoint", "窗口内：tasks 有 · interrupts 空")
        return {"state": {}, "answer": "", "query": ""}

    # raising=False：修复前该 seam 不存在时注入即悬置（行为=现状）→ 红在断言层
    monkeypatch.setattr(
        auto_resume, "_interrupt_metadata_visible", _fake_visible, raising=False
    )
    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_stub_resume),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch(
            "app.ops.lg_rag.event_store.run_is_terminal", new=AsyncMock(return_value=False)
        ),
        caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
    ):
        await auto_resume._claim_and_execute(
            row["id"], resume_mode="inherit", ttl_seconds=3600
        )
        assert not attempted, "竞态窗口内不得执行（interrupt 元数据未就绪）"
        assert window.probes == 1, "窗口内认领须做只读就绪校验"
        window.flip()
        await auto_resume._claim_and_execute(
            row["id"], resume_mode="inherit", ttl_seconds=3600
        )
        assert len(attempted) == 1, "元数据可见后应直达执行一次"
    messages = [r.getMessage() for r in caplog.records]
    _assert_zero_stranded_logs(caplog.records)
    assert sum(m.startswith("hitl_auto_resume_claimed") for m in messages) == 2
    assert sum(m.startswith("hitl_auto_resume_deferred") for m in messages) == 1


async def test_tc2_auto_decide_chain_zero_stranded_in_race_window(monkeypatch, caplog):
    """TC2 修复后 auto decide-同秒链零 stranded_checkpoint（caplog/台账断言）。

    decide 同秒即时认领撞竞态窗口（注入）→ defer 等下轮（非失败重试轮）→
    补偿扫描补触发后同源恢复直达成功（真驱动器 + InMemorySaver 挂起态）。
    全程零「HITL 自动恢复执行失败」· 零 stranded_checkpoint · 窗口内零执行。
    """
    monkeypatch.setenv("OPS_HITL_AUTO_RESUME", "auto")
    store = InMemoryHitlStore()
    saver = InMemorySaver()
    payload = await _suspend(_hitl_state(), saver, "t-race-chain")
    assert payload is not None, "前置：图没有挂起"
    row = _row(thread_id="t-race-chain")
    await store.acreate(row)
    set_hitl_store(store)
    owner = _owner_map({_RUN: _MAINTAINER_ID})
    window = _RaceWindow()

    async def _fake_visible(r) -> bool:
        window.probes += 1
        return window.visible

    from app.ops.hitl.resume import resume_hitl_run as _real_resume

    async def _gated_resume(**kw):
        # 同源耦合：窗口内 resume 侧 aget_state 同样读不到 interrupt 元数据
        if not window.visible:
            raise ResumeError("stranded_checkpoint", "窗口内：tasks 有 · interrupts 空")
        return await _real_resume(checkpointer=saver, graph_factory=_graph_factory, **kw)

    monkeypatch.setattr(
        auto_resume, "_interrupt_metadata_visible", _fake_visible, raising=False
    )
    from httpx import ASGITransport, AsyncClient

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch("app.ops.hitl.router.resume_hitl_run", new=_gated_resume),
        patch(
            "app.ops.lg_rag.event_store.run_is_terminal", new=AsyncMock(return_value=False)
        ),
        caplog.at_level(logging.INFO, logger="app.ops.hitl.auto_resume"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=_bare_app()), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
            )
            assert res.status_code == 200, res.text
            assert res.json()["resume"]["auto_triggered"] is True
            await _drain_background()
        # decide 同秒首跑撞窗口：defer —— 零执行 · 图仍挂起
        graph = _graph_factory(checkpointer=saver)
        snap = await graph.aget_state({"configurable": {"thread_id": "t-race-chain"}})
        assert not snap.values.get("hitl_unlocked_ids"), "竞态窗口内不得执行"
        # 窗口关闭（interrupt 元数据落库）→ 补偿扫描下轮补触发直达恢复
        window.flip()
        assert await auto_resume.scan_approved_not_resumed_once() == 1
        await _drain_background()
        snap = await graph.aget_state({"configurable": {"thread_id": "t-race-chain"}})
        assert snap.values["hitl_unlocked_ids"] == [_T1], "批了却没解锁"
    _assert_zero_stranded_logs(caplog.records)
    messages = [r.getMessage() for r in caplog.records]
    assert any(m.startswith("hitl_auto_resume_triggered") for m in messages)
    assert any(m.startswith("hitl_auto_resume_deferred") for m in messages)
    assert any(m.startswith("hitl_auto_resume_compensated") for m in messages)
    assert any(m.startswith("hitl_auto_resume_claimed") for m in messages)

