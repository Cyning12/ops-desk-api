"""fix-delegation-resume-approval-id：delegation 路径 resume 单消费语义对齐验收。

缺陷（issue #334 · 维护者裁决 2026-11-06 · issue comment `6665660681`）：
delegation 路径 resume 后同一 approval_id 被**双消费**——签发门
``_approval_consumed``（:426 面 · ``delegation_approval_consumed{request_id}``
台账）+ 写闸 ``_write_execution_approval``（:498 面 ·
``capability_write_approval_consumed{approval_id}`` 台账）独立触达同一单据；
主路径（capability_write 类）仅写闸单消费。签认锚点 `:2162+:2177` 经红测
探针实证为干净面（建单守卫区 · 不含任何 approval_id 消费/残留），锚点作废，
修复面收敛到消费层双消费合一。

修复语义（案 A 修正面 · 零行为变化）：
- delegation 类单据的审批消费**归签发门单点**（其台账即该单据的唯一消费记录）；
- 写闸对 delegation 类命中仍走同一 fail-closed 匹配 + W2 租户守卫 +
  返回行注入 ``capability_write_approval_consumed`` 之外的 approval_id 审计串链
  （Host 单次写放行 + cap_ctx approval_id → gateway span 三照不变），
  但**不重复记消费台账**（查命中 ≠ 再消费）；
- capability_write 类单据写闸消费形态与主路径逐字节一致（对称对拍）。

验收映射（维护者 30 授权六条件 + 第七条锚点修正留痕 · issue #334 #6664735511 /
#6665660681）：

- **负样本（红线）**：delegation on 全链 resume 后，同一 approval_id 的消费
  台账**恰为一笔**（签发门面）且写闸面无第二笔；真落笔 + 消费闭环三照
  （台账 request_id / gateway span approval_id / 真执行回执）approval_id 串链；
- **对称对拍**：主路径（delegation off · capability_write 闸）resume 后写闸
  单消费形态与修复前零漂移；
- **fail-closed 不放宽**：既有 TA2 / W2 负样本组全量承接（本文件不重复造面）。
"""

from __future__ import annotations

import logging
import uuid
from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

import app.ops.lg_rag.multi.nodes as nodes
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import resume_hitl_run
from app.ops.hitl.store import STATUS_APPROVED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _delegation_issue_block_reason,
    _issue_delegation_token,
    _join_subtasks,
    _observe,
    _persist_hitl,
    supervisor_node,
    tool_exec_node,
)
from tests.test_hitl_approval_consumption import (
    _CAPS_PATCH,
    _PLAN_PATCH,
    _TESTING_CAP,
    _fake_caps,
    _llm_returning,
    _new_step_suffix,
    _observe_graph_factory,
)

_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"


@pytest.fixture
def deleg_write_env(monkeypatch):
    """delegation enforce + 放行 testing tag + 干净 InMemory store（每用例隔离）。"""
    monkeypatch.setenv(dl.ENV_MODE, "enforce")
    monkeypatch.setenv(dl.ENV_SECRET, "consumption-test-secret")
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    load_capability_manifest(_TESTING_MANIFEST)
    store = InMemoryHitlStore()
    set_hitl_store(store)
    yield store
    reset_hitl_store()


def _mk(run_id: str, sid: str) -> tuple[dict, dict]:
    """单步写 tool 计划 state + 该步 row（承 TA 范式）。"""
    state = {
        "messages": [HumanMessage(content="演示写操作审批")],
        "run_id": run_id,
        "user_id": "u-fix",
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


def _consumption_lines(caplog, approval_id: str) -> list[str]:
    """全日志中携带该 approval_id 且属消费台账（任一 *_approval_consumed）的行。"""
    return [
        r.message
        for r in caplog.records
        if approval_id in r.message and "approval_consumed" in r.message
    ]


# ---------------------------------------------------------------------------
# 负样本（维护者红线）：delegation resume 全链 · 单消费 + 真落笔 + 三照
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_negative_delegation_resume_approval_id_consumed_once(
    deleg_write_env, monkeypatch, caplog
):
    """负样本：delegation on 签发拦下 → decide → 真 resume → replan → 重下发执行。

    红线断言（修复前红 · 双消费）：
    - 同一 approval_id 消费台账恰一笔（签发门 ``delegation_approval_consumed``）；
    - 写闸面不再出现第二笔 ``capability_write_approval_consumed{approval_id}``；
    - 真落笔 + 三照（台账 request_id / gw span approval_id / 执行回执）串链不断。
    """
    store = deleg_write_env
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)

    # ① 签发门拦下（delegation on · 写类工具非只读 → HITL_REQUIRED）
    joined = await _join_subtasks(state)
    term = next(t for t in joined["subtask_results"] if str(t.get("subtask_id")) == sid)
    assert term.get("blocked_by") == "delegation_issue_hitl_required"
    merged = {**state, "subtask_results": [term], "inflight_subtask_ids": []}

    obs = _observe(merged)
    created, _ = await _persist_hitl(merged, obs, thread_id="t-fix")
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    approval_id = req["id"]

    # ② 图真挂起 → decide(approved) → 真 resume（resume_hitl_run 单路径）
    saver = InMemorySaver()
    async for _chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-fix"}}, stream_mode="updates"
    ):
        pass
    await store.adecide(approval_id, decision=STATUS_APPROVED, by="验收")
    out = await resume_hitl_run(
        thread_id="t-fix",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = out["state"]
    assert final["react_observation"]["verdict"] == "replan"
    assert final["hitl_unlocked_ids"] == [sid]

    # ③ replan 保号 → 签发门查命中放行（消费单点在签发门）→ 令牌 → 真执行
    node_spans: list[dict] = []
    gw_spans: list[dict] = []
    monkeypatch.setattr(nodes, "_record_span_metadata", lambda md: node_spans.append(md))
    monkeypatch.setattr(
        "app.ops.capability.gateway.update_current_span_metadata",
        lambda md: gw_spans.append(md),
    )
    caplog.clear()
    replan_state = {
        **merged,
        "subtask_results": [],
        "hitl_unlocked_ids": final["hitl_unlocked_ids"],
        "host_subtask_seq": 1,
        "plan_prefix_ids": [],
        "supervisor_step_count": 1,
        "react_round": 0,
    }
    with (
        patch(_CAPS_PATCH, new=_fake_caps),
        patch(_PLAN_PATCH, new=_llm_returning(_new_step_suffix("后续步骤"))),
    ):
        replanned = await supervisor_node(replan_state)
    carried = next(r for r in replanned["subtasks"] if str(r.get("subtask_id")) == sid)

    post = {**merged, "hitl_unlocked_ids": final["hitl_unlocked_ids"]}
    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        assert await _delegation_issue_block_reason(post, carried) is None
        token = _issue_delegation_token(post, carried)
        assert token is not None
        exec_out = await tool_exec_node(
            {**post, "assigned_subtask": carried, "delegation_token": token}
        )

    # ④ 红线：单消费——全链恰一笔消费台账（签发门面 · request_id 形态）
    lines = _consumption_lines(caplog, approval_id)
    assert len(lines) == 1, f"同一 approval_id 消费须恰一笔（双消费即缺陷）：{lines}"
    assert "delegation_approval_consumed" in lines[0]
    assert "capability_write_approval_consumed" not in lines[0]
    assert not any(
        "capability_write_approval_consumed" in m for m in lines
    ), "写闸不得对 delegation 类单据重复记消费台账（双消费合一）"

    # ⑤ 真落笔：执行成功 + 回执面
    result = exec_out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert "error" not in result, f"批准后重下发仍失败：{result.get('error')!r}"
    assert "output" in result

    # ⑥ 消费闭环三照：台账 request_id（④已钉）+ gw span approval_id + 回执
    gw = [m for m in gw_spans if m.get("capability_id") == _TESTING_CAP]
    assert gw, "capability span 未落"
    assert gw[-1]["approval_id"] == approval_id, "写闸仍须注入 approval_id 审计串链"
    assert gw[-1]["side_effect"] == "write"


# ---------------------------------------------------------------------------
# 对称对拍：主路径（delegation off · capability_write 闸）零漂移
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_main_path_resume_single_consumption_zero_drift(
    monkeypatch, caplog
):
    """对拍：主路径 resume 后写闸单消费形态与修复前零漂移（capability_write
    类单据写闸消费 · 台账 + span approval_id 串链不变 · 防修成 delegation-only
    特殊分支后主路径被误伤）。"""
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    load_capability_manifest(_TESTING_MANIFEST)
    store = InMemoryHitlStore()
    set_hitl_store(store)
    try:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        sid = f"{run_id}:1"
        state, row = _mk(run_id, sid)

        # ① 写闸拦下（capability_write_hitl_required · 主路径）
        out = await tool_exec_node({**state, "assigned_subtask": row})
        blocked = out["subtask_results"][-1]
        assert blocked.get("blocked_by") == "capability_write_hitl_required"
        merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}

        obs = _observe(merged)
        created, _ = await _persist_hitl(merged, obs, thread_id="t-main")
        req = next(r for r in created if str(r.get("subtask_id")) == sid)
        approval_id = req["id"]

        # ② 挂起 → decide → 真 resume
        saver = InMemorySaver()
        async for _chunk in _observe_graph_factory(checkpointer=saver).astream(
            merged, {"configurable": {"thread_id": "t-main"}}, stream_mode="updates"
        ):
            pass
        await store.adecide(approval_id, decision=STATUS_APPROVED, by="验收")
        resumed = await resume_hitl_run(
            thread_id="t-main",
            approved=[sid],
            decided_by="验收",
            checkpointer=saver,
            graph_factory=_observe_graph_factory,
        )
        assert resumed["state"]["hitl_unlocked_ids"] == [sid]

        # ③ 重下发：写闸消费命中（主路径唯一消费点）→ 真执行
        node_spans: list[dict] = []
        monkeypatch.setattr(nodes, "_record_span_metadata", lambda md: node_spans.append(md))
        caplog.clear()
        post = {**merged, "hitl_unlocked_ids": resumed["state"]["hitl_unlocked_ids"]}
        with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
            exec_out = await tool_exec_node({**post, "assigned_subtask": row})
        result = exec_out["subtask_results"][-1]
        assert "error" not in result and "output" in result

        # 对拍断言：恰一笔 capability_write_approval_consumed（写闸面 · approval_id 形态）
        lines = _consumption_lines(caplog, approval_id)
        assert len(lines) == 1, f"主路径消费形态漂移：{lines}"
        assert "capability_write_approval_consumed" in lines[0]
        consumed = [c for c in node_spans if c.get("capability_write_approval_consumed") is True]
        assert len(consumed) == 1
        assert consumed[0]["approval_id"] == approval_id
    finally:
        reset_hitl_store()
