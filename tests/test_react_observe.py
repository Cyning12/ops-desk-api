"""外层 ReAct（plan → execute → **observe** → 再 plan）· 收口语义。

对应提问 #3：原来"没有待发步骤"直接跳 aggregator 生成结论，
中间**没有任何针对性校验** —— 后缀为空 / 全被拦下 / 统统失败，
三种情况都会一路走到 aggregator，产出一份"看起来完整"的答案。

现在执行层先收口：``subtask_join`` 无待发 → ``observe`` → 判定
``replan``（再来一轮 plan→execute）还是 ``settle``（交给 aggregator）。

每条语义都配**正向 + 反向对照**：只做正向会得到假通过——
"一律 settle"天然满足"不会死循环"，"一律 replan"天然满足"会重试"，
两者都测不出对错。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.lg_rag.multi.budget import get_max_react_rounds
from app.ops.lg_rag.multi.nodes import (
    _unresolved_suffix,
    observe_node,
    route_after_react,
    route_next_subtask,
    supervisor_node,
)
from app.ops.lg_rag.state import unresolved_suffix_ids
from app.ops.strategy.critic import critic_node

_RUN = "runreact"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"
_T3 = f"{_RUN}:3"
_TOOL = "mock_get_issue_status"

_PLAN_PATCH = "app.ops.lg_rag.multi.nodes.get_llm_provider"
_CAPS_PATCH = "app.ops.lg_rag.multi.nodes.list_capabilities"


def _fake_caps(*_a, **_kw):
    return [
        SimpleNamespace(capability_id=_TOOL, description="Mock 查询", risk_level="low")
    ]


def _plan_row(sid: str, **kw) -> dict:
    row = {
        "id": sid,
        "subtask_id": sid,
        "alias": "t" + sid.rsplit(":", 1)[-1],
        "type": "tool",
        "tool": _TOOL,
        "input": "x",
        "depends_on": [],
    }
    row.update(kw)
    return row


def _ok(sid: str) -> dict:
    return {"subtask_id": sid, "type": "tool", "output": {"assignee": "张三"}}


def _err(sid: str, msg: str = "boom", **kw) -> dict:
    row = {"subtask_id": sid, "type": "tool", "error": msg}
    row.update(kw)
    return row


def _state(**kw) -> dict:
    base = {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "thread_id": "t-react",
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 1,
        "host_subtask_seq": 2,
        "react_round": 0,
        "inflight_subtask_ids": [],
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# 1 · 没有待发步骤 ≠ 做完了：必须先过 observe
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_inflight_goes_to_observe_not_aggregate():
    """正向：无待发步骤 → ``observe``（不再直连 aggregator）。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1), _err(_T2)],
        plan_prefix_ids=[_T1],
    )
    assert route_next_subtask(state) == "observe"


@pytest.mark.asyncio
async def test_inflight_still_dispatched_control():
    """反向对照：有待发步骤照常派工人 —— 不是"一律收口"。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1)],
        inflight_subtask_ids=[_T2],
    )
    out = route_next_subtask(state)
    assert out != "observe", "有待发步骤却被收口了"
    assert isinstance(out, list) and len(out) == 1


# ---------------------------------------------------------------------------
# 2 · observe 判定：没做完 → replan；做完了 → settle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_observe_replans_when_unsatisfied():
    """正向：有失败 → 再来一轮 plan→execute。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1), _err(_T2)],
        plan_prefix_ids=[_T1],
    )
    out = await observe_node(state)
    assert out["react_observation"]["verdict"] == "replan"
    assert out["react_observation"]["failed"] == [_T2]
    assert route_after_react({**state, **out}) == "replan"
    # 收口一轮：轮数 +1
    assert out["react_round"] == 1


@pytest.mark.asyncio
async def test_observe_settles_when_all_done_control():
    """反向对照：全成 → settle。否则"永远 replan"也能通过上一条。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1), _ok(_T2)],
        plan_prefix_ids=[_T1, _T2],
    )
    out = await observe_node(state)
    assert out["react_observation"]["verdict"] == "settle"
    assert route_after_react({**state, **out}) == "settle"


@pytest.mark.asyncio
async def test_observe_pending_counts_as_unsatisfied():
    """未终态（一次都没跑）也算没做完 —— 不能因为"没有 error"就收工。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1)],
        plan_prefix_ids=[_T1],
    )
    out = await observe_node(state)
    obs = out["react_observation"]
    assert obs["pending"] == [_T2]
    assert obs["unsatisfied"] is True
    assert obs["verdict"] == "replan"


@pytest.mark.asyncio
async def test_react_round_budget_caps_replan():
    """轮次耗尽 → 即使没做完也 settle（禁止"不满意就永远再来一轮"）。"""
    limit = get_max_react_rounds()
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1), _err(_T2)],
        plan_prefix_ids=[_T1],
        react_round=limit - 1,  # 已完成 limit-1 轮，再开就超
    )
    out = await observe_node(state)
    assert out["react_observation"]["unsatisfied"] is True
    assert out["react_observation"]["verdict"] == "settle", "轮次耗尽仍在开新轮"


# ---------------------------------------------------------------------------
# 3 · 重规划**拿不到后缀**时，不得把未解决的步骤从计划里删掉
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replan_fallback_carries_unresolved_steps():
    """正向：重规划输出非法 → 沿用前缀 + **未解决后缀**，不收缩。

    收缩（只留前缀）是 2026-09-20 实测出来的洞：t2 一从计划里消失，
    它的失败记录就变成"计划外 id"，observe 按 plan_ids 过滤看不见、
    aggregator 更看不见，结论会写成"已覆盖全部子任务"。
    """
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2, depends_on=[_T1])],
        subtask_results=[_ok(_T1), _err(_T2)],
        plan_prefix_ids=[_T1],
    )
    with patch(_CAPS_PATCH, new=_fake_caps), patch(
        _PLAN_PATCH, new=lambda *a, **k: SimpleNamespace(
            complete=AsyncMock(return_value="这不是 JSON")
        )
    ):
        out = await supervisor_node(state)
    assert [r["subtask_id"] for r in out["subtasks"]] == [_T1, _T2], (
        f"重规划失败时未解决的步骤被删掉了：{out['subtasks']}"
    )
    # 沿用 = 不换 id（换 id 就等于换了个新步骤，旧失败记录随之变成计划外）
    assert out["host_subtask_seq"] == state["host_subtask_seq"]
    assert out["plan_prefix_ids"] == [_T1]


@pytest.mark.asyncio
async def test_replan_with_valid_suffix_replaces_not_carries_control():
    """反向对照：重规划**成功**时，旧后缀被新签发的步骤替代（不是沿用）。

    否则"永远沿用旧步骤"也能通过上一条 —— 那就永远重试不了。
    """
    suffix = json.dumps(
        {"subtasks": [{"id": "s1", "type": "tool", "tool": _TOOL, "input": "丙"}]},
        ensure_ascii=False,
    )
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2, depends_on=[_T1])],
        subtask_results=[_ok(_T1), _err(_T2)],
        plan_prefix_ids=[_T1],
    )
    with patch(_CAPS_PATCH, new=_fake_caps), patch(
        _PLAN_PATCH, new=lambda *a, **k: SimpleNamespace(
            complete=AsyncMock(return_value=suffix)
        )
    ):
        out = await supervisor_node(state)
    # 前缀原样 + 新后缀（seq 前进 ⇒ 新 id）
    assert [r["subtask_id"] for r in out["subtasks"]] == [_T1, _T3], out["subtasks"]
    assert out["host_subtask_seq"] == 3


@pytest.mark.asyncio
async def test_replan_success_drops_superseded_failure():
    """重规划成功后，被替代的旧失败要从结果里剪掉。

    不剪的话陈尸一直在：critic 见 error 就 retry，整条链反复回环。
    """
    suffix = json.dumps(
        {"subtasks": [{"id": "s1", "type": "tool", "tool": _TOOL, "input": "丙"}]},
        ensure_ascii=False,
    )
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2, depends_on=[_T1])],
        subtask_results=[_ok(_T1), _err(_T2)],
        plan_prefix_ids=[_T1],
    )
    with patch(_CAPS_PATCH, new=_fake_caps), patch(
        _PLAN_PATCH, new=lambda *a, **k: SimpleNamespace(
            complete=AsyncMock(return_value=suffix)
        )
    ):
        out = await supervisor_node(state)
    assert out["subtask_results"].replace is True
    assert _T2 not in out["subtask_results"].plan_ids, "被替代的旧失败没剪掉"


# ---------------------------------------------------------------------------
# 4 · critic 回环同样不得抹掉未解决的步骤
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_critic_retry_keeps_unresolved_failure():
    """正向：critic retry 后，失败步骤连计划带结果都还在。"""
    out = await critic_node(
        {
            "subtask_results": [_ok(_T1), _err(_T2)],
            "allowed_capability_ids": [_TOOL],
            "inner_retry_count": 0,
            "rebinding_count": 0,
            "subtasks": [_plan_row(_T1), _plan_row(_T2)],
        }
    )
    assert out["critic_verdict"]["outcome"] == "retry_planner"
    assert [r["subtask_id"] for r in out["subtasks"]] == [_T1, _T2]
    assert out["subtask_results"].plan_ids == frozenset({_T1, _T2})
    # 前缀只认成功终态
    assert out["plan_prefix_ids"] == [_T1]


def test_unresolved_suffix_ids_semantics():
    """未解决 = 未终态 或 error 终态；成功终态与前缀都不算。"""
    plan = [_plan_row(_T1), _plan_row(_T2), _plan_row(_T3)]
    results = [_ok(_T1), _err(_T2)]
    assert unresolved_suffix_ids(plan, results) == [_T2, _T3]
    # 前缀（已成功）不算未解决
    assert unresolved_suffix_ids(plan, results, [_T1]) == [_T2, _T3]
    # 全成 → 没有未解决
    assert unresolved_suffix_ids(plan, [_ok(_T1), _ok(_T2), _ok(_T3)]) == []


def test_unresolved_suffix_helper_reads_state():
    """``_unresolved_suffix`` 沿用原行（不重新签发），且排除前缀。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1), _err(_T2)],
    )
    locked = [_plan_row(_T1)]
    carried = _unresolved_suffix(state, locked)
    assert [r["subtask_id"] for r in carried] == [_T2]
    assert carried[0] is not state["subtasks"][1], "必须是副本，不能改到 state"


# ---------------------------------------------------------------------------
# 5 · HITL 挂起：不再开新轮（人没批之前，再来几轮都是同一个拦截）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hitl_pending_settles_and_flags_unpersisted():
    """正向：有 HITL 挂起 → wait_hitl，且**未落库必须显式带出来**。

    默认持久化是 null（不落库并告警）⇒ ``hitl_unpersisted`` 必须为 True。
    "申请丢了"和"没人申请过"在观测上长得一模一样，人会一直等一个不存在的审批。
    """
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[
            _ok(_T1),
            _err(_T2, "需要重跑已执行步骤", blocked_by="prefix_touch_required",
                 hitl_required=True),
        ],
        plan_prefix_ids=[_T1],
    )
    out = await observe_node(state)
    obs = out["react_observation"]
    assert obs["verdict"] == "wait_hitl"
    assert obs["hitl_pending"] == [_T2]
    assert obs["hitl_unpersisted"] is True, "申请没落库却没报出来"
    # wait_hitl 走 settle（收工等审批），不是 replan
    assert route_after_react({**state, **out}) == "settle"
    assert out["hitl_requests"], "没有产出审批申请"


@pytest.mark.asyncio
async def test_no_hitl_pending_does_not_claim_pending_control():
    """反向对照：没有 HITL 就不许报 pending —— 否则"一律报 pending"能过。"""
    state = _state(
        subtasks=[_plan_row(_T1), _plan_row(_T2)],
        subtask_results=[_ok(_T1), _ok(_T2)],
        plan_prefix_ids=[_T1, _T2],
    )
    out = await observe_node(state)
    assert out["react_observation"]["hitl_pending"] == []
    assert out["react_observation"]["hitl_unpersisted"] is False
    assert out["hitl_requests"] == []


# ---------------------------------------------------------------------------
# 6 · 端到端：失败不得被静默抹掉（这条最初就是这么被发现的）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failure_survives_replan_and_reaches_final_state():
    """全链：一步失败 + 重规划一直拿不到后缀 ⇒ 失败仍出现在最终状态里。

    改这条之前，失败会在第二轮被"只留前缀"裁掉，最终结论是
    "已覆盖全部子任务" —— 失败被静默抹掉。
    """
    from app.ops.lg_rag.schemas import IntentV1

    intent_ok = IntentV1(
        domain="ops_kb",
        needs_tool=True,
        needs_skill=False,
        is_composite=True,
        risk_hint="low",
        summary="复合运维查询",
    )
    plan = json.dumps(
        {
            "subtasks": [
                {"id": "t1", "type": "tool", "tool": _TOOL, "input": "甲"},
                {"id": "t2", "type": "tool", "tool": _TOOL, "input": "乙",
                 "depends_on": ["t1"]},
            ]
        },
        ensure_ascii=False,
    )
    seen: list[str] = []

    async def _tool_call(name, args, ctx=None):
        sid = str((ctx or {}).get("subtask_id"))
        seen.append(sid)
        return (SimpleNamespace(ok=True, output={"assignee": "张三"}, error=None, meta={})
                if sid.endswith(":1")
                else SimpleNamespace(ok=False, output={}, error="boom", meta={}))

    async def _prov_complete(msgs, model=None):
        # 首次给计划；之后一律给拿不到后缀的垃圾 ⇒ 触发 carry 路径
        return plan if not seen else "（无更多计划）"

    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    graph = build_supervisor_agent(checkpointer=InMemorySaver())
    with patch(
        "app.ops.strategy.intent.acomplete_structured",
        new=AsyncMock(return_value=intent_ok),
    ), patch(
        _PLAN_PATCH,
        new=lambda *a, **k: SimpleNamespace(complete=_prov_complete),
    ), patch(
        "app.ops.lg_rag.multi.nodes.capability_ainvoke", new=_tool_call
    ):
        out = await graph.ainvoke(
            {"messages": [HumanMessage(content="复合问题")], "run_id": _RUN},
            {"configurable": {"thread_id": "t-react-e2e"}},
        )

    results = out["subtask_results"]
    ids = [r["subtask_id"] for r in results]
    assert len(ids) == len(set(ids)), f"同一个 subtask_id 重复了：{ids}"
    assert any("boom" in str(r.get("error") or "") for r in results), (
        f"失败被静默抹掉了：{results}"
    )
    # 前缀（已成功的 t1）没有被重跑
    assert seen.count(_T1) == 1, f"前缀被重跑了：{seen}"
    # 收口判定留痕
    assert (out.get("react_observation") or {}).get("verdict") in (
        "settle",
        "wait_hitl",
    )
