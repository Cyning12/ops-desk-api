"""P4-T7 · 委派子 run 执行（19-p4-contracts §8-§13 · 18-p4 §3）验收。

- **总闸三件套**（19 §12）：OPS_RUN_TREE_ENABLED off(默认)/on、非法值回退
  off+warning；OPS_RUN_TREE_MAX_CHILDREN 默认 8 · 非法/越界回退默认；
- **route 闸开分支**（19 §8.1）：off 态 route_next_subtask 走既有 Send 路径
  逐字节零 diff（type=tool→tool_exec）；on 态 type=tool → delegate_exec ·
  payload 注入 user_id/allowed_capability_ids · plan-JSON 零新 type；
- **MAX_CHILDREN 第二层预算**（19 §8.4）：claim 前 COUNT(parent_run_id) 校验，
  超限=子任务按失败收口（不创建子 run）；
- **委派 happy path**（19 §8.2/§9.2）：子 run 继承父 tenant/user/thread ·
  帧序 run.start（带 delegate_spec+parent_run_id）→answer→done · 父轮询
  接回 output（既有 subtask_join 通路零改动）；
- **HITL 三段**（19 §10）：①写闸拦截→建单+waiting_approval 退出 worker（不占
  执行槽）②decide(approved)→_execute_decided_resume 按 depth 分流重启
  delegate worker ③重跑至同一能力调用点 _approval_consumed 命中放行——
  **能力适配器全链恰好执行一次**（重复 decide 409 语义 · 重复 resume
  preflight not_interrupted 拒 · 19 §13 表）；rejected → settle 落
  done{status:error,reason=审批驳回} · 父侧按失败收口。
"""

from __future__ import annotations

import asyncio
import logging
import uuid

import pytest
from sqlalchemy import delete, select

import app.ops.lg_rag.multi.nodes as nodes
from app.db.models import OpsLgRagRun, OpsLgRagRunEvent, OpsLgRagThread
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑委派子 run"
)

MAINTAINER_ID = "00000000-0000-0000-0000-000000000001"
_TESTING_CAP = "testing.write.echo"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"
_READ_CAP_ID = "p4t7_delegate_read_echo"


# ---------------------------------------------------------------------------
# 公共 fixture / helper
# ---------------------------------------------------------------------------


async def _cleanup_prefix(prefix: str) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(OpsLgRagRunEvent).where(OpsLgRagRunEvent.run_id.like(f"{prefix}%"))
        )
        await db.execute(delete(OpsLgRagRun).where(OpsLgRagRun.run_id.like(f"{prefix}%")))
        await db.execute(
            delete(OpsLgRagThread).where(OpsLgRagThread.id.like(f"{prefix}%"))
        )
        await db.commit()


def _mk_delegate_state(run_id: str, sid: str, tool: str, user_id: str) -> tuple[dict, dict]:
    """单步 tool 计划 + inflight（route/delegate_exec 直调用 · 承 _mk 范式）。"""
    state = {
        "messages": [],
        "run_id": run_id,
        "user_id": user_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": "p4t7 委派演示",
                "args": {"request_id": "r-1", "note": "p4t7"},
                "tool": tool,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [sid],
        "supervisor_step_count": 0,
        "allowed_capability_ids": [tool],
    }
    return state, state["subtasks"][0]


async def _child_row_of(parent_run_id: str):
    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(OpsLgRagRun).where(OpsLgRagRun.parent_run_id == parent_run_id)
        )


async def _events_of(run_id: str) -> list:
    async with AsyncSessionLocal() as db:
        rows = await db.scalars(
            select(OpsLgRagRunEvent)
            .where(OpsLgRagRunEvent.run_id == run_id)
            .order_by(OpsLgRagRunEvent.seq)
        )
        return list(rows)


@pytest.fixture
def read_cap_env(monkeypatch):
    """read 类罐头（委派 happy path 用 · 幂等注册 + teardown 卸载）。"""
    from app.ops.capability.adapters.local_fn import LocalFnAdapter
    from app.ops.capability.gateway import register, unregister
    from app.ops.capability.types import CapabilitySpec

    calls: list = []

    def _spy(payload):
        calls.append(payload)
        return {"tool": _READ_CAP_ID, "input": payload, "written": False}

    unregister(_READ_CAP_ID)
    spec = CapabilitySpec(
        capability_id=_READ_CAP_ID,
        kind="local_fn",
        description="P4-T7 委派 happy path 罐头",
        args_schema={"type": ["string", "object"], "properties": {}, "additionalProperties": True},
        tags=("testing",),
        risk_level="low",
        side_effect="read",
    )
    register(spec, LocalFnAdapter(_spy))
    yield calls
    unregister(_READ_CAP_ID)


@pytest.fixture
def write_cap_env(monkeypatch):
    """写罐头 + InMemory HITL store（HITL 三段用 · 承 test_write_approval_gate 范式）。"""
    from app.ops.capability import delegation as dl
    from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
    from app.ops.capability.gateway import unregister
    from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
    from app.ops.hitl import reset_hitl_store, set_hitl_store
    from app.ops.hitl.store import InMemoryHitlStore

    echo_calls: list = []

    def _spy(payload):
        echo_calls.append(payload)
        return {"tool": "testing_write_echo", "input": payload, "written": False}

    monkeypatch.setattr("app.ops.capability.defaults.testing_write_echo", _spy)
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    unregister(_TESTING_CAP)
    load_capability_manifest(MANIFEST_DIR / "testing.v1.yaml")
    store = InMemoryHitlStore()
    set_hitl_store(store)
    yield store, echo_calls
    reset_hitl_store()
    monkeypatch.undo()
    unregister(_TESTING_CAP)
    load_capability_manifest(MANIFEST_DIR / "testing.v1.yaml")


# ---------------------------------------------------------------------------
# 总闸三件套（19 §12 · 无 DB）
# ---------------------------------------------------------------------------


def test_run_tree_enabled_default_off(monkeypatch) -> None:
    monkeypatch.delenv(nodes.ENV_RUN_TREE_ENABLED, raising=False)
    assert nodes.run_tree_enabled() is False


def test_run_tree_enabled_on(monkeypatch) -> None:
    monkeypatch.setenv(nodes.ENV_RUN_TREE_ENABLED, "on")
    assert nodes.run_tree_enabled() is True


def test_run_tree_enabled_invalid_fallback_off(monkeypatch, caplog) -> None:
    monkeypatch.setenv(nodes.ENV_RUN_TREE_ENABLED, "banana")
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.multi.nodes"):
        assert nodes.run_tree_enabled() is False
    assert any("OPS_RUN_TREE_ENABLED" in r.message for r in caplog.records)


def test_run_tree_max_children_default_and_parse(monkeypatch) -> None:
    monkeypatch.delenv(nodes.ENV_RUN_TREE_MAX_CHILDREN, raising=False)
    assert nodes.run_tree_max_children() == 8
    monkeypatch.setenv(nodes.ENV_RUN_TREE_MAX_CHILDREN, "3")
    assert nodes.run_tree_max_children() == 3
    monkeypatch.setenv(nodes.ENV_RUN_TREE_MAX_CHILDREN, "0")
    assert nodes.run_tree_max_children() == 8  # 越界回退默认
    monkeypatch.setenv(nodes.ENV_RUN_TREE_MAX_CHILDREN, "abc")
    assert nodes.run_tree_max_children() == 8  # 非法回退默认


# ---------------------------------------------------------------------------
# route_next_subtask 闸开分支（19 §8.1/§11.5 · 无 DB）
# ---------------------------------------------------------------------------


def _route_state(run_id: str, sid: str) -> dict:
    state, _row = _mk_delegate_state(run_id, sid, _READ_CAP_ID, "u-route")
    return state


def test_route_gate_off_zero_diff(monkeypatch) -> None:
    """闸 off（默认）：type=tool 仍发 Send(tool_exec) · 行为面零 diff。"""
    from app.ops.capability import delegation as dl

    monkeypatch.delenv(nodes.ENV_RUN_TREE_ENABLED, raising=False)
    monkeypatch.setenv(dl.ENV_MODE, "off")
    run_id = f"route-{uuid.uuid4().hex[:8]}"
    state = _route_state(run_id, f"{run_id}:1")

    sends = nodes.route_next_subtask(state)

    assert isinstance(sends, list) and len(sends) == 1
    assert sends[0].node == "tool_exec"


def test_route_gate_on_promotes_tool_to_delegate_exec(monkeypatch) -> None:
    """闸 on：type=tool inflight 子任务 → Send(delegate_exec) · plan-JSON 零新 type
    （subtasks 行 type 仍是 tool · 提升面由「type=tool + 闸开」机械决定）。"""
    from app.ops.capability import delegation as dl

    monkeypatch.setenv(nodes.ENV_RUN_TREE_ENABLED, "on")
    monkeypatch.setenv(dl.ENV_MODE, "off")
    run_id = f"route-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state = _route_state(run_id, sid)
    state["user_id"] = "u-owner"

    sends = nodes.route_next_subtask(state)

    assert isinstance(sends, list) and len(sends) == 1
    assert sends[0].node == "delegate_exec"
    payload = sends[0].arg
    assert payload["user_id"] == "u-owner"
    assert payload["allowed_capability_ids"] == [_READ_CAP_ID]
    assert "delegation_token" not in payload  # §3.9：子侧自发签发 · 父不注入
    assert state["subtasks"][0]["type"] == "tool"  # plan-JSON 零新 type


# ---------------------------------------------------------------------------
# MAX_CHILDREN 第二层预算（19 §8.4 · DB）
# ---------------------------------------------------------------------------


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_max_children_exceeded_fails_subtask(seeded_maintainer, monkeypatch) -> None:
    """claim 前 COUNT(parent_run_id) 达上限 → 子任务按失败收口 · 不再建行。"""
    from app.ops.lg_rag.run_store import claim_child_run, count_child_runs, create_run

    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t7-{uuid.uuid4().hex[:8]}"
    parent_id = f"{prefix}-p"
    sid = f"{prefix}:1"
    try:
        assert (
            await create_run(
                run_id=parent_id,
                thread_id=f"{prefix}-th",
                user_id=user_id,
                tenant_id="tenant-p4t7",
            )
            is True
        )
        for i in range(2):
            rid, created = await claim_child_run(
                parent_run_id=parent_id,
                subtask_id=f"{prefix}-seed-{i}",
                child_run_id=f"{prefix}-seed-c{i}",
            )
            assert created is True and rid
        monkeypatch.setenv(nodes.ENV_RUN_TREE_MAX_CHILDREN, "2")
        state, row = _mk_delegate_state(parent_id, sid, _READ_CAP_ID, user_id)

        out = await nodes.delegate_exec_node({**state, "assigned_subtask": row})

        result = out["subtask_results"][-1]
        assert result.get("error") == "委派子 run 总数超限"
        assert "output" not in result
        assert await count_child_runs(parent_id) == 2  # 未再建行
    finally:
        await _cleanup_prefix(prefix)


# ---------------------------------------------------------------------------
# 委派 happy path（19 §8.2/§8.3/§9.2 · DB）
# ---------------------------------------------------------------------------


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_delegate_happy_path_frames_and_join(
    seeded_maintainer, read_cap_env, monkeypatch
) -> None:
    """闸 on 全链：claim 子 run（继承父归属）→ worker 执行 read 罐头 →
    run.start/answer/done 帧序 → 父轮询终态接回 output（既有 join 通路）。"""
    from app.ops.lg_rag.run_store import create_run

    calls = read_cap_env
    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t7-{uuid.uuid4().hex[:8]}"
    parent_id = f"{prefix}-p"
    thread_id = f"{prefix}-th"
    sid = f"{prefix}:1"
    try:
        assert (
            await create_run(
                run_id=parent_id,
                thread_id=thread_id,
                user_id=user_id,
                tenant_id="tenant-p4t7",
            )
            is True
        )
        state, row = _mk_delegate_state(parent_id, sid, _READ_CAP_ID, user_id)

        out = await asyncio.wait_for(
            nodes.delegate_exec_node({**state, "assigned_subtask": row}), timeout=30
        )

        result = out["subtask_results"][-1]
        assert result.get("output") == {
            "tool": _READ_CAP_ID,
            "input": {"request_id": "r-1", "note": "p4t7"},
            "written": False,
        }, f"父侧应接回子 run output：{result!r}"
        assert len(calls) == 1  # 能力恰好执行一次

        # §8.2：子 run 归属全从父行继承
        child = await _child_row_of(parent_id)
        assert child is not None
        assert child.depth == 1
        assert child.subtask_id == sid
        assert child.status == "done"
        assert child.tenant_id == "tenant-p4t7"
        assert str(child.user_id) == user_id
        assert child.thread_id == thread_id

        # §3.4 帧序：run.start（带 parent_run_id+delegate_spec）→answer→done
        events = await _events_of(child.run_id)
        kinds = [e.event_type for e in events]
        assert kinds == ["run.start", "answer", "done"]
        start_payload = events[0].payload
        assert start_payload["parent_run_id"] == parent_id
        assert start_payload["mode"] == "delegate"
        assert start_payload["delegate_spec"]["subtask"]["tool"] == _READ_CAP_ID
        assert events[1].payload.get("final") is True
        done_payload = events[2].payload
        assert done_payload["status"] == "done"
        assert done_payload["delegate_result"]["output"] == result["output"]
    finally:
        await _cleanup_prefix(prefix)


# ---------------------------------------------------------------------------
# HITL 三段（19 §10 · DB）：建单→waiting 退出→approve 重跑放行→幂等防线
# ---------------------------------------------------------------------------


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_delegate_hitl_approve_resume_exactly_once(
    seeded_maintainer, write_cap_env, monkeypatch
) -> None:
    """T7 实证①+②：approve 后重跑放行至 done（能力适配器全链恰好一次）·
    重复 decide → None（409 语义）· 重复 resume → preflight not_interrupted 拒。"""
    from app.ops.hitl.resume import ResumeError
    from app.ops.hitl.router import _execute_decided_resume, _preflight_decided_resume
    from app.ops.lg_rag.run_store import create_run, fetch_run_row
    from app.ops.tenant_context import TENANT_A

    store, echo_calls = write_cap_env
    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t7-{uuid.uuid4().hex[:8]}"
    parent_id = f"{prefix}-p"
    thread_id = f"{prefix}-th"
    sid = f"{prefix}:1"
    parent_task = None
    try:
        assert (
            await create_run(
                run_id=parent_id,
                thread_id=thread_id,
                user_id=user_id,
                tenant_id=TENANT_A,
            )
            is True
        )
        state, row = _mk_delegate_state(parent_id, sid, _TESTING_CAP, user_id)

        # 段①：父节点在后台轮询；子 run 写闸拦截 → 建单 + waiting_approval 退出
        parent_task = asyncio.create_task(
            nodes.delegate_exec_node({**state, "assigned_subtask": row})
        )
        req = None
        for _ in range(300):  # 最长 ~15s 等子 run 挂起
            pending = await store.alist(status="pending", limit=10)
            if pending:
                req = pending[0]
                break
            await asyncio.sleep(0.05)
        assert req is not None, "委派子 run 未落 HITL 单据"
        child_run_id = str(req["run_id"])
        assert child_run_id != parent_id  # 单据 run_id=子 run_id（§9.2 行 4）
        assert req["blocked_by"] == _BLOCKED_BY_WRITE
        assert req["subtask_id"] == sid
        assert req["unlock_subtask_id"] == sid  # 自解锁
        assert req["tenant_id"] == TENANT_A
        assert req["payload"]["capability_id"] == _TESTING_CAP
        assert echo_calls == []  # 拦截在适配器之前 · 零副作用
        child_row = await fetch_run_row(child_run_id)
        assert child_row is not None and child_row["status"] == "waiting_approval"
        assert child_row["depth"] == 1
        child_events = await _events_of(child_run_id)
        assert [e.event_type for e in child_events] == [
            "run.start",
            "hitl.waiting",
            "done",
        ]
        assert child_events[-1].payload["status"] == "waiting_approval"
        assert parent_task.done() is False  # 父仍在轮询（waiting 非终态）

        # 段②：decide(approved) → _execute_decided_resume 按 depth 分流重启子 worker
        decided = await store.adecide(req["id"], decision="approved", by="验收T7")
        assert decided is not None
        assert await store.adecide(req["id"], decision="approved", by="x") is None  # 重复 decide
        resume_outcome = await _execute_decided_resume(decided)
        assert resume_outcome["outcome"]["delegate_restarted"] is True

        # 段③：重跑至同一能力调用点 _approval_consumed 命中放行 → done
        out = await asyncio.wait_for(parent_task, timeout=30)
        parent_task = None
        result = out["subtask_results"][-1]
        assert "error" not in result, f"approve 后应放行至 done：{result!r}"
        assert result["output"]["tool"] == "testing_write_echo"
        assert len(echo_calls) == 1, "能力适配器全链必须恰好执行一次（幂等）"

        child_row = await fetch_run_row(child_run_id)
        assert child_row["status"] == "resumed"
        child_events = await _events_of(child_run_id)
        kinds = [e.event_type for e in child_events]
        assert kinds == ["run.start", "hitl.waiting", "done", "hitl.resumed", "answer", "done"]
        assert child_events[-1].payload["status"] == "resumed"

        # 重复 resume 防线（19 §13）：子 run 已终态 → preflight not_interrupted 拒
        with pytest.raises(ResumeError) as excinfo:
            await _preflight_decided_resume(decided)
        assert excinfo.value.code == "not_interrupted"
        assert len(echo_calls) == 1  # 仍未重复执行
    finally:
        if parent_task is not None:
            parent_task.cancel()
        await _cleanup_prefix(prefix)


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_delegate_hitl_rejected_settles_error(
    seeded_maintainer, write_cap_env, monkeypatch
) -> None:
    """段② rejected 分支：settle_delegate_run_rejected 落终态帧收口 ·
    父侧按子任务失败进 observe（19 §13 表「HITL 超时/驳回」行）。"""
    from app.ops.hitl.router import _execute_decided_resume
    from app.ops.lg_rag.run_store import create_run, fetch_run_row
    from app.ops.tenant_context import TENANT_A

    store, echo_calls = write_cap_env
    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t7-{uuid.uuid4().hex[:8]}"
    parent_id = f"{prefix}-p"
    thread_id = f"{prefix}-th"
    sid = f"{prefix}:1"
    parent_task = None
    try:
        assert (
            await create_run(
                run_id=parent_id,
                thread_id=thread_id,
                user_id=user_id,
                tenant_id=TENANT_A,
            )
            is True
        )
        state, row = _mk_delegate_state(parent_id, sid, _TESTING_CAP, user_id)

        parent_task = asyncio.create_task(
            nodes.delegate_exec_node({**state, "assigned_subtask": row})
        )
        req = None
        for _ in range(300):
            pending = await store.alist(status="pending", limit=10)
            if pending:
                req = pending[0]
                break
            await asyncio.sleep(0.05)
        assert req is not None
        child_run_id = str(req["run_id"])

        decided = await store.adecide(req["id"], decision="rejected", by="验收T7")
        assert decided is not None
        resume_outcome = await _execute_decided_resume(decided)
        assert resume_outcome["outcome"]["delegate_rejected_settled"] is True

        out = await asyncio.wait_for(parent_task, timeout=30)
        parent_task = None
        result = out["subtask_results"][-1]
        assert "output" not in result
        assert "审批驳回" in str(result.get("error") or "")
        assert echo_calls == []  # 驳回零执行

        child_row = await fetch_run_row(child_run_id)
        assert child_row["status"] == "error"
        child_events = await _events_of(child_run_id)
        kinds = [e.event_type for e in child_events]
        assert kinds[-2:] == ["hitl.resumed", "done"]
        assert child_events[-1].payload["status"] == "error"
        assert child_events[-1].payload["reason"] == "审批驳回"
    finally:
        if parent_task is not None:
            parent_task.cancel()
        await _cleanup_prefix(prefix)
