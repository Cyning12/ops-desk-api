"""api-controlled-write-hitl 阶段 W：写执行审批闸（capability_write_hitl_required）验收。

棒次口径（HG-STAGE-W-DESIGN 签收 · 2026-10-30 · task_api_controlled_write_hitl）：

- **W0** 写类 capability 无审批 → fail-closed 挂起 HITL pending（tool_exec 编排层闸，
  与 gateway Policy 写闸**正交两道闸**：``OPS_CAPABILITY_ALLOW_WRITE`` 只过 Policy 层，
  **不豁免**本闸——负样本钉死）；read/unknown 零 diff；
- **W1** decide(approved) → resume 续跑写执行全链（复用既有 ``resume_hitl_run``
  单一恢复驱动 · 无第二条恢复路径）；decide(rejected) → settle 不执行；
- **W2** tenant_scope 全链下推：capability_write 类审批行 tenant_id 缺失或与当前
  租户不一致 → fail-closed 不消费（跨租户负样本）；F1–F6 由既有
  test_tenant_context.py / test_hitl_pending_decide.py 回归承接；
- **W2-T**（api-w-hitl-tenant-fix · HG-W-TENANT-DESIGN ②③ 2026-11-03 维护者裁决）：
  delegation 类审批行**纳入同一租户守卫**——带戳同租户可消费 / 跨租户或空 tenant
  fail-closed 不消费（W2④ 旧形态「空 tenant 可消费」断言同步废止改写）；
- **W3** span ``approval_id`` 审计串链（gateway.py:1318 预留启用：审批命中后执行
  注入 ``ctx["approval_id"]`` → capability span metadata 落值）；
- **freeze 红线**：挂起载荷复用既有 ``hitl_waiting`` 形态（顶层键集 + requests
  字段集钉死 · 不新增 SSE 事件类型）；decide 400/404/409/422 消费语义零 diff
  由既有 test_hitl_pending_decide.py 回归承接（本文件不重复造面）。

写意图结构钉死（payload.write_intent）：capability_id + tenant_id + args 摘要
+ 幂等键模板。
"""

from __future__ import annotations

import time
import uuid

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

import app.ops.lg_rag.multi.nodes as nodes
from app.ops.capability import delegation as dl
from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.gateway import get_registry, register
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.capability.types import CapabilitySpec
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import resume_hitl_run
from app.ops.hitl.store import STATUS_APPROVED, STATUS_REJECTED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _delegation_blocked_terminal,
    _observe,
    _persist_hitl,
    observe_node,
    route_after_react,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.tenant_context import (
    TENANT_A,
    TENANT_B,
    reset_current_tenant,
    set_current_tenant,
)

_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"
_TESTING_CAP = "testing.write.echo"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"


@pytest.fixture
def write_env(monkeypatch):
    """delegation off（本闸独立于委派模式）+ testing tag 放行 + InMemory store。

    **不设** ``OPS_CAPABILITY_ALLOW_WRITE``——Host 写放行由审批命中后单次注入
    （两道闸语义：env 只过 Policy 层，不过审批闸）。

    adapter spy 绑定纪律（registry 首载 winner-take-all · manifest loader 对
    重复 id 幂等跳过 manifest.py:186）：先 patch 罐头函数 → ``unregister``
    卸掉旧绑定 → 重载 manifest 让 loader 解析到本测试 spy；teardown 先
    ``monkeypatch.undo()`` 还原函数引用再重载还原真罐头绑定，防跨文件污染。
    产出 ``(store, echo_calls)``。
    """
    from app.ops.capability.gateway import unregister

    echo_calls: list = []

    def _spy(payload):
        echo_calls.append(payload)
        return {"tool": "testing_write_echo", "input": payload, "written": False}

    monkeypatch.setattr("app.ops.capability.defaults.testing_write_echo", _spy)
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    unregister(_TESTING_CAP)  # 卸掉既有绑定（未注册时返回 False · 幂等）
    load_capability_manifest(_TESTING_MANIFEST)
    store = InMemoryHitlStore()
    set_hitl_store(store)
    yield store, echo_calls
    reset_hitl_store()
    monkeypatch.undo()  # 先还原函数引用，再重载 → 真罐头绑定还原（防污染他文件）
    unregister(_TESTING_CAP)
    load_capability_manifest(_TESTING_MANIFEST)


def _mk(run_id: str, sid: str) -> tuple[dict, dict]:
    """单步 tool 计划 state + 该步 row（承 TA 范式）。"""
    state = {
        "messages": [HumanMessage(content="演示写操作审批")],
        "run_id": run_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": {"request_id": "r-1", "note": "demo"},
                "tool": _TESTING_CAP,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "allowed_capability_ids": [_TESTING_CAP],
    }
    return state, state["subtasks"][0]


def _write_approved_req(run_id: str, sid: str, **over):
    """capability_write 类 approved 单据（三元组 + tenant + payload 键 · over 可变异）。"""
    req = {
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "run_id": run_id,
        "thread_id": "t-w",
        "subtask_id": sid,
        "blocked_by": _BLOCKED_BY_WRITE,
        "unlock_subtask_id": sid,
        "reason": "写操作需人工审批（测试）",
        "tenant_id": TENANT_A,
        "payload": {
            "capability_id": _TESTING_CAP,
            "write_intent": {"capability_id": _TESTING_CAP, "tenant_id": TENANT_A},
        },
        "status": "approved",
        "decision_by": "验收",
        "decided_at": time.time(),
        "created_at": time.time(),
    }
    req.update(over)
    return req


def _observe_graph_factory(*, checkpointer):
    """只含真 observe_node 的最小图（承 test_hitl_resume harness）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


_READ_CAP_ID = "test_write_gate_read_cap"


def _ensure_read_cap() -> None:
    """注册一枚 read 罐头（W0 零 diff 对照 · 幂等）。"""
    if get_registry().get(_READ_CAP_ID) is not None:
        return
    spec = CapabilitySpec(
        capability_id=_READ_CAP_ID,
        kind="local_fn",
        description="写闸对照：read 罐头",
        args_schema={"type": ["string", "object"], "properties": {}, "additionalProperties": True},
        tags=("testing",),
        risk_level="low",
        side_effect="read",
    )
    register(spec, LocalFnAdapter(lambda payload: {"tool": _READ_CAP_ID, "input": payload}))


# ---------------------------------------------------------------------------
# W0 · 审批闸 fail-closed（红 → 绿）
# ---------------------------------------------------------------------------


async def test_w0_write_blocked_without_approval_fail_closed(write_env, caplog):
    """W0①：无任何审批单据 → tool_exec 不写：blocked terminal（hitl_required +
    blocked_by=capability_write_hitl_required）· adapter 零调用 · 闸本身零建单
    （建单是 observe/_persist_hitl 职责）。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)

    import logging

    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE
    assert result.get("hitl_required") is True
    assert "output" not in result
    assert result.get("error")
    assert calls == []  # 适配器零调用：罐头都没跑
    assert await store.alist(status="pending", limit=10) == []  # 闸零建单
    # 台账（记动作不记内容）：capability_write_hitl_required 一条 · 无参数原值
    hits = [r for r in caplog.records if "capability_write_hitl_required" in r.message]
    assert len(hits) == 1
    assert sid in hits[0].message and _TESTING_CAP in hits[0].message
    assert "demo" not in hits[0].message  # note 原值不落台账


async def test_w0_env_allow_write_does_not_bypass_approval_gate(write_env, monkeypatch):
    """W0② 负样本钉死（棒次红线「无审批直接写 = fail-closed」）：
    ``OPS_CAPABILITY_ALLOW_WRITE=1`` 只过 gateway Policy 写闸，**不豁免** HITL
    审批闸——无审批单据仍挂起，adapter 零调用。"""
    _store, calls = write_env
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE
    assert result.get("hitl_required") is True
    assert calls == []


async def test_w0_read_capability_zero_diff(write_env):
    """W0③：read 类 capability 不过审批闸（现状零 diff · 不触 store 不拦截）。"""
    store, _calls = write_env
    _ensure_read_cap()
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    row["tool"] = _READ_CAP_ID

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert "error" not in result, f"read 能力被误拦：{result.get('error')!r}"
    assert "output" in result
    assert "blocked_by" not in result
    assert await store.alist(status="approved", limit=10) == []  # 读路径零触达


async def test_w0_unknown_capability_passthrough(write_env):
    """W0④：未注册 capability 走既有 unknown 错误面（闸不新增行为）。"""
    _store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    row["tool"] = "no.such.capability"

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("error")
    assert "blocked_by" not in result
    assert "hitl_required" not in result
    assert calls == []


# ---------------------------------------------------------------------------
# W1/W3 · decide(approved) → resume → 写执行全链 + span approval_id 串链
# ---------------------------------------------------------------------------


async def test_w1_w3_approved_resume_executes_write_with_approval_span(write_env, monkeypatch):
    """W1 全链 + W3 串链：闸拦 → pending 落库（写意图结构钉死）→ 图真挂起
    （freeze 形态钉死）→ decide(approved) → resume（replan · 解锁留痕）→
    重下发消费命中 → Host 单次写放行注入 → 罐头真执行 → span approval_id 落值。
    """
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)

    # ① 闸拦（off 模式：无 join 拦截 · 审批闸是唯一 HITL 保护）
    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert blocked.get("hitl_required") is True
    assert blocked.get("tenant_id") == TENANT_A  # W2：拦单即带租户
    assert calls == []

    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-w1")
    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["blocked_by"] == _BLOCKED_BY_WRITE
    assert req["unlock_subtask_id"] == sid  # D2 回填（resume 不 409 前提）
    assert req["tenant_id"] == TENANT_A  # W2：审批行全链带租户
    payload = req["payload"]
    assert payload["capability_id"] == _TESTING_CAP
    intent = payload["write_intent"]  # 写意图结构钉死
    assert intent["capability_id"] == _TESTING_CAP
    assert intent["tenant_id"] == TENANT_A
    assert intent["idempotency_key"] == "{{request_id}}"  # 幂等键模板
    summary = intent["args_summary"]  # gateway._args_summary 同构：脱敏串
    assert isinstance(summary, str)
    assert "request_id" in summary and "note" in summary  # 摘要含键名不见敏感原值

    # ② 图真挂起：freeze 形态钉死（复用既有 hitl_waiting · 键集合零新增）
    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-w1"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None, "前置：图没有被挂起"
    assert set(suspended.keys()) == {  # 顶层形态零 diff（_hitl_interrupt_payload 钉死）
        "reason",
        "run_id",
        "thread_id",
        "checkpoint_id",
        "round",
        "unpersisted",
        "requests",
    }
    assert suspended["reason"] == "hitl_waiting"
    req0 = next(r for r in suspended["requests"] if r["subtask_id"] == sid)
    assert set(req0.keys()) == {  # requests 字段集钉死（SSE freeze 负样本）
        "id",
        "subtask_id",
        "unlock_subtask_id",
        "blocked_by",
        "reason",
    }
    assert req0["blocked_by"] == _BLOCKED_BY_WRITE
    assert req0["unlock_subtask_id"] == sid

    # ③ decide(approved) → resume（既有单一驱动 resume_hitl_run）
    decided = await store.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    assert decided["status"] == STATUS_APPROVED
    resumed = await resume_hitl_run(
        thread_id="t-w1",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = resumed["state"]
    assert final["react_observation"]["verdict"] == "replan"
    assert final["hitl_unlocked_ids"] == [sid]

    # ④ 重下发：消费命中 → 单次写放行注入 → 真执行 + W3 span 串链
    node_spans: list[dict] = []
    gw_spans: list[dict] = []
    monkeypatch.setattr(nodes, "_record_span_metadata", lambda md: node_spans.append(md))
    monkeypatch.setattr(
        "app.ops.capability.gateway.update_current_span_metadata",
        lambda md: gw_spans.append(md),
    )
    post = {**merged, "hitl_unlocked_ids": final["hitl_unlocked_ids"]}
    exec_out = await tool_exec_node({**post, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert "error" not in result, f"批准后重下发仍失败：{result.get('error')!r}"
    assert "output" in result
    assert len(calls) == 1  # 罐头真执行一次

    # 消费台账（nodes 面）：approval_id 串链 + 记动作不记内容
    consumed = [c for c in node_spans if c.get("capability_write_approval_consumed") is True]
    assert len(consumed) == 1
    assert consumed[0]["approval_id"] == req["id"]
    assert consumed[0]["subtask_id"] == sid
    assert consumed[0]["capability_id"] == _TESTING_CAP

    # W3：capability span metadata approval_id 落值（gateway.py:1318 预留启用）
    gw = [m for m in gw_spans if m.get("capability_id") == _TESTING_CAP]
    assert gw, "capability span 未落"
    assert gw[-1]["approval_id"] == req["id"]
    assert gw[-1]["side_effect"] == "write"


async def test_w1_rejected_settles_without_execution(write_env):
    """W1 反向：decide(rejected) → resume 收工（verdict=settle）· 不执行不写。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)

    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    created, _ = await _persist_hitl(merged, obs, thread_id="t-w1r")
    req = next(r for r in created if str(r.get("subtask_id")) == sid)

    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-w1r"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None

    decided = await store.adecide(req["id"], decision=STATUS_REJECTED, by="验收")
    assert decided["status"] == STATUS_REJECTED
    resumed = await resume_hitl_run(
        thread_id="t-w1r",
        approved=[],
        rejected=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = resumed["state"]
    assert final["react_observation"]["verdict"] == "settle"
    assert not final.get("hitl_unlocked_ids")
    assert calls == []  # 全程零执行


def test_w1_single_resume_path_source_pin():
    """红线钉死（棒次口径「禁第二条 resume 实现」）：恢复执行体全仓唯一定义在
    ``app.ops.hitl.router._execute_decided_resume``；auto_resume 同源惰性 import
    复用（auto_resume.py:225-227 形态）。"""
    import inspect

    import app.ops.hitl.auto_resume as ar
    import app.ops.hitl.router as hr

    ar_src = inspect.getsource(ar)
    hr_src = inspect.getsource(hr)
    assert "from app.ops.hitl.router import _execute_decided_resume" in ar_src
    assert ar_src.count("def _execute_decided_resume") == 0  # 无第二实现
    assert hr_src.count("def _execute_decided_resume") == 1  # 唯一定义点


# ---------------------------------------------------------------------------
# W2 · tenant_scope 下推（fail-closed 负样本组）
# ---------------------------------------------------------------------------


async def test_w2_cross_tenant_approval_not_consumed(write_env):
    """W2①：approved 单据 tenant_id=B，当前租户 A → 不消费（跨租户写 fail-closed
    拦死）· adapter 零调用。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await store.acreate(
        _write_approved_req(
            run_id,
            sid,
            tenant_id=TENANT_B,
            payload={
                "capability_id": _TESTING_CAP,
                "write_intent": {"capability_id": _TESTING_CAP, "tenant_id": TENANT_B},
            },
        )
    )

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE  # 仍拦
    assert calls == []


async def test_w2_current_tenant_mismatch_not_consumed(write_env, monkeypatch):
    """W2② 反向：单据 tenant_id=A，当前租户 B（session 真源下推）→ 不消费。"""
    store, calls = write_env
    monkeypatch.setattr(nodes, "current_tenant_or_default", lambda: TENANT_B)
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await store.acreate(_write_approved_req(run_id, sid))

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE
    assert result.get("tenant_id") == TENANT_B  # 拦单带当前租户
    assert calls == []


async def test_w2_missing_tenant_row_fail_closed(write_env):
    """W2③：capability_write 类 approved 单据缺 tenant_id（旧形态/脏数据）→
    fail-closed 不消费（新类单据必须带租户）。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await store.acreate(_write_approved_req(run_id, sid, tenant_id=""))

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE
    assert calls == []


async def test_w2_delegation_class_row_stamped_tenant_consumed(write_env):
    """W2④（api-w-hitl-tenant-fix · HG-W-TENANT-DESIGN ② 改写）：delegation 类
    approved 单据**带租户戳**（T-fix-2 新形态）在写执行闸同源可消费——enforce
    链不双审批；同租户正样本放行。旧形态断言（tenant_id='' 仍可消费）已废止：
    守卫扩列后空/跨租户 delegation 行一律 fail-closed（见下两条负样本）。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await store.acreate(
        _write_approved_req(
            run_id,
            sid,
            blocked_by="delegation_issue_hitl_required",
            tenant_id=TENANT_A,
            payload={"capability_id": _TESTING_CAP},
        )
    )

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert "error" not in result, f"委派类审批未同源放行：{result.get('error')!r}"
    assert "output" in result
    assert len(calls) == 1


async def test_w2_delegation_class_cross_tenant_not_consumed(write_env):
    """守卫扩列负样本①：delegation 类单据 tenant=B · 当前租户 A → 不消费
    （HG-W-TENANT-DESIGN ② · 守卫真空收口 · adapter 零调用）。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await store.acreate(
        _write_approved_req(
            run_id,
            sid,
            blocked_by="delegation_issue_hitl_required",
            tenant_id=TENANT_B,
            payload={"capability_id": _TESTING_CAP},
        )
    )

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE  # 仍拦（fail-closed）
    assert calls == []


async def test_w2_delegation_class_empty_tenant_fail_closed(write_env):
    """守卫扩列负样本②：delegation 类单据 tenant=''（历史 40 行形态）→ 不消费
    （HG-W-TENANT-DESIGN ③ · 空 tenant 视同无授权 · fail-closed）。"""
    store, calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await store.acreate(
        _write_approved_req(
            run_id,
            sid,
            blocked_by="delegation_issue_hitl_required",
            tenant_id="",
            payload={"capability_id": _TESTING_CAP},
        )
    )

    out = await tool_exec_node({**state, "assigned_subtask": row})

    result = out["subtask_results"][-1]
    assert result.get("blocked_by") == _BLOCKED_BY_WRITE  # 仍拦（fail-closed）
    assert calls == []


async def test_w2t_delegation_persist_row_carries_tenant(write_env):
    """T-fix-2 落库链：delegation 拦截 terminal（_delegation_blocked_terminal
    打的戳）经 _persist_hitl 落库后审批行 tenant_id 非空且 = 当前租户 —
    守卫扩列「查非空成立」的落库前提。"""
    store, _calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    token = set_current_tenant(TENANT_B)
    try:
        blocked = _delegation_blocked_terminal(row, "委派签发需人工审批（测试）")
    finally:
        reset_current_tenant(token)
    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]

    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-w2t")

    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["blocked_by"] == "delegation_issue_hitl_required"
    assert req["tenant_id"] == TENANT_B, "delegation 审批行 tenant 戳丢失（F3 真空）"
    assert req["unlock_subtask_id"] == sid  # _SELF_UNLOCK 回填（D2 形态）


async def test_w2t_unstamped_class_persist_falls_back_to_current_tenant(write_env):
    """T-fix-2 全类口径：terminal 未带戳的类（prefix_touch 等）落库时回落
    当前租户上下文 —— 「新单不再产 tenant_id=''」对**所有**类成立，resume 链
    单据快照真源不因单据类而断（dualproc 真链负样本的单元钉）。"""
    store, _calls = write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    blocked = {
        "subtask_id": sid,
        "type": "tool",
        "error": "需要重跑已执行步骤",
        "blocked_by": "prefix_touch_required",
        "hitl_required": True,
    }
    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]

    token = set_current_tenant(TENANT_B)
    try:
        created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-w2t2")
    finally:
        reset_current_tenant(token)

    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["blocked_by"] == "prefix_touch_required"
    assert req["tenant_id"] == TENANT_B, "未带戳类落库未回落当前租户（新单仍产 ''）"
