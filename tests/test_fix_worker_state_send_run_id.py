"""fix-worker-state-send-run-id · hat 30（案 A · ``_worker_state`` 补 ``run_id`` 键）：

HITL resume 后写审批消费闭环修复回归（承 task_fix_worker_state_send_run_id · 40
invoke 偏差登记①——``_worker_state`` Send 载荷丢 ``run_id`` → 写消费门 fail-closed
再拦 resume 后重下发 · PR #303 时期潜伏）。

- **红测负样本（维护者红线 · 真派发路径）**：``route_next_subtask`` → ``_worker_state``
  产载荷 → ``tool_exec_node``——预置 approved 单据后重下发**不再被消费门拦截**，
  消费命中 + 真落笔三照（便签行 / 回执 / 消费台账 span）；单测直调 tool_exec
  自带全 state 的盲区正是本缺陷藏至 40 live 才暴露的根因，故负样本**禁止**直造
  全 state；
- **键集回归钉**：``_worker_state`` 产物工人可见键集含 ``run_id``（防再发）；
  空 run_id state **不写入**（FP-7 空串键防污染）；
- **delegation on 对拍**：委派路径 payload ``run_id`` 值不变（重复赋值同值兼容，
  HG-WORKER-STATE-RUN-ID-DESIGN 决策点②签收面）；
- 改码面唯一对拍（本文件自身约束）：``nodes.py`` 仅 ``_worker_state`` 增量，
  闸链 / HITL 表 / 状态机 / auto-resume 一行不动（工程面 git 对拍由 30 invoke 承载）。
"""

from __future__ import annotations

import time
import uuid

import pytest
from langchain_core.messages import HumanMessage
from langgraph.types import Send

import app.ops.lg_rag.multi.nodes as nodes
from app.db.session import AsyncSessionLocal
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.idempotency import (
    InMemoryIdempotencyStore,
    reset_idempotency_store,
    set_idempotency_store,
)
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.capability.receipts import (
    InMemoryReceiptSink,
    reset_receipt_sink,
    set_receipt_sink,
)
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _worker_state,
    route_next_subtask,
    tool_exec_node,
)
from app.ops.tenant_context import TENANT_A
from tests.conftest import DB_AVAILABLE

_NEW_MANIFEST = MANIFEST_DIR / "ops.write.v1.yaml"
_NEW_CAP = "ops.write.run_note"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"

_DB_MARK = pytest.mark.skipif(not DB_AVAILABLE, reason="需要 PostgreSQL（opsdesk_test）")

# 测试数据统一前缀：清理与断言都按它过滤，绝不触碰其他行
_PREFIX = "fxrunid"


@pytest.fixture(autouse=True)
def _restore():
    dl.reset_delegation_state()
    yield
    reset_hitl_store()
    reset_idempotency_store()
    reset_receipt_sink()
    dl.reset_delegation_state()
    get_registry().clear()
    ensure_default_capabilities()


@pytest.fixture(autouse=True)
async def _db_clean():
    if DB_AVAILABLE:
        await _clear_notes()
    yield
    if DB_AVAILABLE:
        await _clear_notes()


@pytest.fixture
def write_env(monkeypatch):
    """新能力三层显式打开 + 内存 hitl/幂等/回执（承 run_note_env 范式）。"""
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "run_note")
    load_capability_manifest(_NEW_MANIFEST)
    hitl_store = InMemoryHitlStore()
    set_hitl_store(hitl_store)
    idem_store = InMemoryIdempotencyStore()
    set_idempotency_store(idem_store)
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    yield hitl_store, sink


# ---------------------------------------------------------------------------
# DB 小工具（真 PostgreSQL · opsdesk_test）
# ---------------------------------------------------------------------------


async def _clear_notes() -> None:
    from sqlalchemy import text

    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_capability_notes WHERE idempotency_key LIKE :p"),
            {"p": f"{_PREFIX}-%"},
        )


async def _fetch_notes(idem_key: str) -> list[dict]:
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT id, tenant_id, capability_id, run_id, subtask_id, approval_id,"
                " note, idempotency_key FROM ops_capability_notes"
                " WHERE idempotency_key = :k"
            ),
            {"k": idem_key},
        )
        cols = ("id", "tenant_id", "capability_id", "run_id", "subtask_id",
                "approval_id", "note", "idempotency_key")
        return [dict(zip(cols, r, strict=True)) for r in rows.all()]


# ---------------------------------------------------------------------------
# 计划行 / approved 单据构造（承 test_write_approval_gate 范式）
# ---------------------------------------------------------------------------


def _plan_row(run_id: str, sid: str, req_id: str) -> dict:
    return {
        "subtask_id": sid,
        "id": sid,
        "type": "tool",
        "input": {"run_id": run_id, "note": "修复验证便签", "request_id": req_id},
        "args": {"run_id": run_id, "note": "修复验证便签", "request_id": req_id},
        "tool": _NEW_CAP,
        "depends_on": [],
    }


def _dispatch_state(run_id: str, row: dict) -> dict:
    """supervisor 持有的图 state（run_id 在通道层 · 经派发才进工人载荷）。"""
    return {
        "messages": [HumanMessage(content="写一条 run 备注")],
        "run_id": run_id,
        "subtasks": [row],
        "subtask_results": [],
        "inflight_subtask_ids": [str(row["subtask_id"])],
        "allowed_capability_ids": [_NEW_CAP],
        "supervisor_step_count": 0,
    }


def _approved_req(run_id: str, sid: str, **over) -> dict:
    """capability_write 类 approved 单据（三元组 + tenant + payload 键）。"""
    req = {
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "run_id": run_id,
        "thread_id": "t-fx",
        "subtask_id": sid,
        "blocked_by": _BLOCKED_BY_WRITE,
        "unlock_subtask_id": sid,
        "reason": "写操作需人工审批（测试）",
        "tenant_id": TENANT_A,
        "payload": {
            "capability_id": _NEW_CAP,
            "write_intent": {"capability_id": _NEW_CAP, "tenant_id": TENANT_A},
        },
        "status": "approved",
        "decision_by": "验收",
        "decided_at": time.time(),
        "created_at": time.time(),
    }
    req.update(over)
    return req


# ---------------------------------------------------------------------------
# 键集回归钉（_worker_state 直调 · 防再发）
# ---------------------------------------------------------------------------


def test_worker_state_payload_carries_run_id():
    """键集钉①：有 run_id 的 state → 工人可见载荷含 run_id（值正确）。"""
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    row = _plan_row(run_id, f"{run_id}:1", f"{run_id}-req")
    state = _dispatch_state(run_id, row)
    payload = _worker_state(state, row)
    assert payload["run_id"] == run_id
    # 键集精确钉死（条件可选键不在场时的最小面 · 防静默增删键）
    assert set(payload.keys()) == {
        "messages",
        "assigned_subtask",
        "subtasks",
        "supervisor_step_count",
        "run_id",
    }


def test_worker_state_payload_omits_run_id_when_missing():
    """FP-7：run_id 缺失（空 state）→ **不写入** run_id 键（防空串污染工人视野）。"""
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    row = _plan_row(run_id, f"{run_id}:1", f"{run_id}-req")
    state = {k: v for k, v in _dispatch_state(run_id, row).items() if k != "run_id"}
    payload = _worker_state(state, row)
    assert "run_id" not in payload
    assert set(payload.keys()) == {
        "messages",
        "assigned_subtask",
        "subtasks",
        "supervisor_step_count",
    }


# ---------------------------------------------------------------------------
# 派发路径载荷（route_next_subtask → Send）
# ---------------------------------------------------------------------------


def test_dispatch_payload_carries_run_id_delegation_off():
    """真派发路径（delegation off · 默认面）：Send 载荷含 run_id。"""
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    row = _plan_row(run_id, f"{run_id}:1", f"{run_id}-req")
    sends = route_next_subtask(_dispatch_state(run_id, row))
    assert len(sends) == 1 and isinstance(sends[0], Send)
    assert sends[0].node == "tool_exec"
    assert sends[0].arg["run_id"] == run_id  # 工人可见全部 state


def test_dispatch_payload_run_id_unchanged_with_delegation_on(monkeypatch):
    """决策点②对拍：delegation on 路径 payload run_id 值不变（重复赋值同值兼容）。

    （此断言在修复前亦绿——delegation 分支 :1666 既有补键；钉死的是修复后
    不得漂移。）"""
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    row = _plan_row(run_id, f"{run_id}:1", f"{run_id}-req")
    sends = route_next_subtask(_dispatch_state(run_id, row))
    assert len(sends) == 1
    assert sends[0].arg["run_id"] == run_id


# ---------------------------------------------------------------------------
# 红测负样本（维护者红线）：resume 后重下发不再被消费门拦截 · 真落笔三照
# ---------------------------------------------------------------------------


@_DB_MARK
async def test_resume_redispatch_consumes_approval_real_write(write_env, monkeypatch):
    """负样本：经真派发路径（route_next_subtask → _worker_state 产载荷）——
    预置 approved 单据 → tool_exec 消费命中 → 真落笔三照
    （便签行 / 回执 / 消费台账 span · approval_id 串链）。

    修复前：载荷无 run_id → 消费门 fail-closed 再拦（本测试红——即 40 live
    偏差#1 的单测形态）；修复后：消费命中真落笔（绿）。"""
    store, sink = write_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    row = _plan_row(run_id, sid, req_id)
    state = _dispatch_state(run_id, row)

    # 真派发路径：Send 载荷 = 工人所见全部 state（非直造全 state）
    sends = route_next_subtask(state)
    assert len(sends) == 1
    payload = sends[0].arg
    assert payload["run_id"] == run_id  # 红测核心断言①：载荷带键
    assert "assigned_subtask" in payload and payload["assigned_subtask"]["tool"] == _NEW_CAP

    # 预置 approved 单据（三元组匹配 · tenant A · 新鲜 TTL）
    req = _approved_req(run_id, sid)
    await store.acreate(req)

    node_spans: list[dict] = []
    monkeypatch.setattr(nodes, "_record_span_metadata", lambda md: node_spans.append(md))

    out = await tool_exec_node(payload)

    # 消费命中：不再 fail-closed 拦截
    result = out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert "error" not in result, f"批准后重下发仍被拦：{result.get('error')!r}"
    assert result["output"]["written"] is True
    assert result["output"]["tool"] == "ops_write_run_note"

    # 真落笔三照①：便签行落值（tenant / approval / subtask / 幂等键串链）
    notes = await _fetch_notes(req_id)
    assert len(notes) == 1
    note = notes[0]
    assert note["tenant_id"] == TENANT_A
    assert note["capability_id"] == _NEW_CAP
    assert note["run_id"] == run_id
    assert note["subtask_id"] == sid
    assert note["approval_id"] == req["id"]
    assert note["idempotency_key"] == req_id
    assert note["note"] == "修复验证便签"

    # 真落笔三照②：消费台账 span（capability_write_approval_consumed）
    consumed = [c for c in node_spans if c.get("capability_write_approval_consumed") is True]
    assert len(consumed) == 1
    assert consumed[0]["approval_id"] == req["id"]
    assert consumed[0]["subtask_id"] == sid
    assert consumed[0]["capability_id"] == _NEW_CAP

    # 真落笔三照③：回执（Host 单次放行下执行 · UUID 同串链）
    receipts = sink.by_idempotency_key(req_id)
    assert len(receipts) == 1
    assert receipts[0].ok is True
    assert receipts[0].write_confirmed is True
    assert receipts[0].tenant_id == TENANT_A
    assert receipts[0].captured.get("note_id") == str(note["id"])


@_DB_MARK
async def test_dispatch_payload_without_run_id_still_blocked(write_env):
    """FP-9 防误读：修复**不**放行无审批直跑——空 run_id 派生载荷（无单据
    可匹配）仍 fail-closed 拦死 · 零落笔。"""
    store, _sink = write_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    row = _plan_row(run_id, sid, req_id)
    state = _dispatch_state(run_id, row)
    del state["run_id"]  # 极端：图 state 本身无 run_id（模拟旧链路/异常路径）
    sends = route_next_subtask(state)
    payload = sends[0].arg
    assert "run_id" not in payload  # 空值不写入（FP-7）
    # 单据以真 run_id 维度存在也无法被空 run_id 消费（三元组精确匹配）
    await store.acreate(_approved_req(run_id, sid))

    out = await tool_exec_node(payload)

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE  # 仍拦（fail-closed 不放宽）
    assert result.get("hitl_required") is True
    assert await _fetch_notes(req_id) == []
