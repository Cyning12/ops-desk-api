"""S4 · Critic 规则 stub / reducer / supervisor 图边 / 预算熔断（mock，不连外网）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ops.lg_rag.state import merge_subtask_results
from app.ops.strategy.critic import (
    MAX_INNER_RETRIES,
    MAX_REBINDING,
    critic_node,
    decide_critic_verdict,
)


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _edge_pairs(graph) -> set[tuple[str, str]]:
    return {(e.source, e.target) for e in graph.get_graph().edges}


def _error_result() -> dict:
    return {"id": "t1", "type": "rag", "input": "q", "error": "boom"}


def test_decide_no_error_is_pass():
    assert decide_critic_verdict({"subtask_results": [{"output": "ok"}]}) == "pass"
    assert decide_critic_verdict({"subtask_results": []}) == "pass"
    assert decide_critic_verdict({}) == "pass"


def test_decide_error_empty_allowlist_is_rebind():
    state = {
        "subtask_results": [_error_result()],
        "allowed_capability_ids": [],
        "rebinding_count": 0,
    }
    assert decide_critic_verdict(state) == "rebind"
    state_missing = {
        "subtask_results": [_error_result()],
        "rebinding_count": 0,
    }
    assert decide_critic_verdict(state_missing) == "rebind"


def test_decide_error_nonempty_allowlist_is_retry_planner():
    state = {
        "subtask_results": [_error_result()],
        "allowed_capability_ids": ["utc_now_iso"],
        "inner_retry_count": 0,
    }
    assert decide_critic_verdict(state) == "retry_planner"


def test_decide_budget_exhausted_is_end():
    error_empty = {
        "subtask_results": [_error_result()],
        "allowed_capability_ids": [],
        "rebinding_count": MAX_REBINDING,
    }
    assert decide_critic_verdict(error_empty) == "end"
    error_allow = {
        "subtask_results": [_error_result()],
        "allowed_capability_ids": ["utc_now_iso"],
        "inner_retry_count": MAX_INNER_RETRIES,
    }
    assert decide_critic_verdict(error_allow) == "end"


def test_subtask_results_reducer_append_then_none_clears():
    existing = [{"id": "t1"}]
    appended = merge_subtask_results(existing, [{"id": "t2"}])
    assert appended == [{"id": "t1"}, {"id": "t2"}]
    assert merge_subtask_results(appended, None) == []
    assert merge_subtask_results(None, [{"id": "t3"}]) == [{"id": "t3"}]


def test_supervisor_graph_aggregator_to_critic_not_end():
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    graph = build_supervisor_agent()
    edges = _edge_pairs(graph)
    assert ("aggregator", "critic_node") in edges
    assert ("aggregator", "__end__") not in edges
    assert ("critic_node", "__end__") in edges
    assert ("critic_node", "supervisor") in edges
    assert ("critic_node", "strategy_builder") in edges


def test_router_and_basic_graphs_have_no_critic_node():
    from app.ops.lg_rag.graph import build_basic_agent, build_router_agent

    router = build_router_agent()
    basic = build_basic_agent()
    router_nodes = set(router.get_graph().nodes.keys())
    basic_nodes = set(basic.get_graph().nodes.keys())
    assert "critic_node" not in router_nodes
    assert "critic_node" not in basic_nodes
    router_edges = _edge_pairs(router)
    basic_edges = _edge_pairs(basic)
    assert ("__start__", "router") in router_edges
    assert ("__start__", "rag") in basic_edges


@pytest.mark.asyncio
async def test_critic_span_metadata_contains_outcome():
    recorded: list[tuple] = []

    def _fake_span(name, **kwargs):
        recorded.append((name, kwargs))
        return _span_cm()

    with patch("app.ops.strategy.critic.trace_span", side_effect=_fake_span):
        out = await critic_node(
            {"subtask_results": [{"output": "ok"}], "inner_retry_count": 0, "rebinding_count": 0}
        )
    assert out["critic_verdict"]["outcome"] == "pass"
    assert recorded
    assert recorded[0][0] == "critic"
    assert recorded[0][1]["critic_outcome"] == "pass"
    assert "inner_retry_count" in recorded[0][1]
    assert "rebinding_count" in recorded[0][1]


@pytest.mark.asyncio
async def test_critic_retry_clears_subtasks_and_results_when_no_prefix():
    """无已成功步骤时，回环等价于整批清空（与 2026-09-20 之前一致）。"""
    with patch("app.ops.strategy.critic.trace_span", return_value=_span_cm()):
        out = await critic_node(
            {
                "subtask_results": [_error_result()],
                "allowed_capability_ids": ["utc_now_iso"],
                "inner_retry_count": 0,
                "rebinding_count": 0,
                "subtasks": [{"id": "t1", "type": "rag", "input": "q"}],
            }
        )
    assert out["critic_verdict"]["outcome"] == "retry_planner"
    assert out["inner_retry_count"] == 1
    assert out["subtasks"] == []
    # 不再是 None，而是"裁剪到空前缀"的批次 —— 语义相同，写法可断言
    assert list(out["subtask_results"]) == []
    assert out["subtask_results"].plan_ids == frozenset()
    assert out["subtask_results"].replace is True
    assert out["recoverable_point"] == 0


@pytest.mark.asyncio
async def test_critic_retry_keeps_prefix_results():
    """Q8：已成功步骤连计划带结果都留下，重规划只动后缀。

    修这条之前是 ``subtask_results = None`` ⇒ 已跑过的步骤会被重跑一遍，
    前缀根本无从锁定。
    """
    with patch("app.ops.strategy.critic.trace_span", return_value=_span_cm()):
        out = await critic_node(
            {
                "subtask_results": [
                    {"subtask_id": "r:1", "output": {"a": 1}},
                    {"subtask_id": "r:2", "error": "boom"},
                ],
                "allowed_capability_ids": ["utc_now_iso"],
                "inner_retry_count": 0,
                "rebinding_count": 0,
                "subtasks": [
                    {"id": "r:1", "subtask_id": "r:1", "type": "tool", "input": "甲"},
                    {"id": "r:2", "subtask_id": "r:2", "type": "tool", "input": "乙"},
                ],
            }
        )
    assert out["critic_verdict"]["outcome"] == "retry_planner"
    # 计划 = 前缀 + **未解决后缀**。
    # 只留前缀是错的（2026-09-20 实测）：r:2 一旦从计划里消失，它的失败记录
    # 就变成"计划外 id"，observe 按 plan_ids 过滤看不见、aggregator 更看不见，
    # 结论会写成"已覆盖全部子任务" —— 失败被静默抹掉。
    assert [r["subtask_id"] for r in out["subtasks"]] == ["r:1", "r:2"]
    # 结果同样保留未解决后缀：失败是**发生过的事实**，重规划不能假装没发生
    assert out["subtask_results"].plan_ids == frozenset({"r:1", "r:2"})
    assert out["subtask_results"].replace is True
    # 可恢复点显式声明出来了（只有成功终态算前缀）
    assert out["plan_prefix_ids"] == ["r:1"]
    assert out["recoverable_point"] == 1


@pytest.mark.asyncio
async def test_always_error_retry_planner_ends_within_budget():
    """非空 allowlist + 永远 error：retry 一次后 end；计数 ≤1；有限步停（不 ainvoke）。"""
    from app.ops.strategy.critic import route_after_critic

    state: dict = {
        "subtask_results": [_error_result()],
        "allowed_capability_ids": ["utc_now_iso"],
        "inner_retry_count": 0,
        "rebinding_count": 0,
        "subtasks": [{"id": "t1", "type": "rag", "input": "q"}],
    }
    routes: list[str] = []
    with patch("app.ops.strategy.critic.trace_span", return_value=_span_cm()):
        for _ in range(8):
            out = await critic_node(state)
            routes.append(route_after_critic({**state, **out}))
            state = {
                **state,
                "critic_verdict": out["critic_verdict"],
                "inner_retry_count": out["inner_retry_count"],
                "rebinding_count": out["rebinding_count"],
                "subtask_results": [_error_result()],
                "subtasks": [{"id": "t1", "type": "rag", "input": "q"}],
            }
            if out["critic_verdict"]["outcome"] == "end":
                break
    assert routes == ["retry_planner", "end"]
    assert state["inner_retry_count"] == 1
    assert state["rebinding_count"] == 0
    assert state["inner_retry_count"] <= MAX_INNER_RETRIES


@pytest.mark.asyncio
async def test_always_error_empty_allowlist_rebind_ends_within_budget():
    """空 allowlist + 永远 error：rebind 一次后 end；计数 ≤1；有限步停。"""
    from app.ops.strategy.critic import route_after_critic

    state: dict = {
        "subtask_results": [_error_result()],
        "allowed_capability_ids": [],
        "inner_retry_count": 0,
        "rebinding_count": 0,
        "subtasks": [{"id": "t1", "type": "rag", "input": "q"}],
    }
    routes: list[str] = []
    with patch("app.ops.strategy.critic.trace_span", return_value=_span_cm()):
        for _ in range(8):
            out = await critic_node(state)
            routes.append(route_after_critic({**state, **out}))
            state = {
                **state,
                "critic_verdict": out["critic_verdict"],
                "inner_retry_count": out["inner_retry_count"],
                "rebinding_count": out["rebinding_count"],
                "subtask_results": [_error_result()],
                "subtasks": [{"id": "t1", "type": "rag", "input": "q"}],
            }
            if out["critic_verdict"]["outcome"] == "end":
                break
    assert routes == ["rebind", "end"]
    assert state["rebinding_count"] == 1
    assert state["inner_retry_count"] == 0
    assert state["rebinding_count"] <= MAX_REBINDING
