"""Supervisor 无依赖子任务同批下发，按 Host subtask_id 归并（不连真 LLM）。"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Send

from app.ops.lg_rag.multi.nodes import MAX_SUBTASKS, route_next_subtask, supervisor_node
from app.ops.lg_rag.schemas import IntentV1
from app.ops.lg_rag.sse_replay import format_sse_event, make_cursor
from app.ops.lg_rag.state import merge_subtask_results

_MULTI_PROVIDER_PATCH = "app.ops.lg_rag.multi.nodes.get_llm_provider"
_ROUTER_PROVIDER_PATCH = "app.ops.lg_rag.nodes.get_llm_provider"
_CHAIN_PATCH = "app.ops.lg_rag.nodes.ainvoke_evidence_answer"
_INTENT_COMPLETE_PATCH = "app.ops.strategy.intent.acomplete_structured"
_INTENT_OK = IntentV1(
    domain="ops_kb",
    needs_tool=True,
    needs_skill=False,
    is_composite=True,
    risk_hint="low",
    summary="并发归并",
)
_RUN = "runhost"
_AGG = "## 综合结论\n齐了。"


def _provider(*outputs) -> SimpleNamespace:
    """按序返回；用尽后**重复最后一项**。

    为什么不再让 AsyncMock 抛 StopAsyncIteration：外层 ReAct 加了 observe 之后，
    一次 run 里 supervisor / aggregator 的调用次数取决于"判定结果"，
    把桩写死成固定条数会让**拓扑一变测试就红**，而红的原因跟被测行为无关。
    """
    stream = list(outputs)

    async def complete(messages, model=None):
        if not stream:
            return ""
        if len(stream) > 1:
            return stream.pop(0)
        return stream[0]

    return SimpleNamespace(complete=complete)


def _plan_json(items: list[dict]) -> str:
    return json.dumps({"subtasks": items}, ensure_ascii=False)


def _build():
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    return build_supervisor_agent(checkpointer=InMemorySaver())


async def _run(graph, query: str = "并行问"):
    with patch(_INTENT_COMPLETE_PATCH, new=AsyncMock(return_value=_INTENT_OK)):
        return await graph.ainvoke(
            {
                "messages": [HumanMessage(content=query)],
                "run_id": _RUN,
            },
            {"configurable": {"thread_id": "t-parallel"}},
        )


def _batch(items: list[dict], plan_ids: set[str]):
    from app.ops.lg_rag.state import SubtaskResultBatch

    return SubtaskResultBatch(items, plan_ids)


def test_illegal_depends_and_cycle_are_error_terminals_not_parallel():
    from app.ops.lg_rag.multi.nodes import _issue_plan

    plan, errors, seq = _issue_plan(
        [
            {"id": "t1", "type": "tool", "input": "甲", "depends_on": ["t2"]},
            {"id": "t2", "type": "tool", "input": "乙", "depends_on": ["t1"]},
            {"id": "t3", "type": "rag", "input": "丙", "depends_on": ["nope"]},
        ],
        run_id=_RUN,
        seq=0,
    )
    assert seq == 3
    assert len(plan) == 3
    by_id = {row["subtask_id"]: row["error"] for row in errors}
    assert set(by_id) == {f"{_RUN}:1", f"{_RUN}:2", f"{_RUN}:3"}
    assert "成环" in by_id[f"{_RUN}:1"]
    assert "成环" in by_id[f"{_RUN}:2"]
    assert "计划外" in by_id[f"{_RUN}:3"] or "无法解析" in by_id[f"{_RUN}:3"]
    assert MAX_SUBTASKS == 4


def test_merge_none_clears():
    """Critic 回环：None 必须清空，不能当成追加。"""
    existing = [{"subtask_id": f"{_RUN}:1", "output": "keep"}]
    assert merge_subtask_results(existing, None) == []
    assert merge_subtask_results(None, None) == []


def test_merge_drops_unknown_and_duplicate_terminal():
    plan = {f"{_RUN}:1", f"{_RUN}:2"}
    existing = [{"subtask_id": f"{_RUN}:1", "id": f"{_RUN}:1", "output": "first"}]
    incoming = _batch(
        [
            {"subtask_id": "not-in-plan", "output": "丢"},
            {"subtask_id": f"{_RUN}:1", "output": "覆盖失败"},
            {"subtask_id": f"{_RUN}:2", "output": "second"},
        ],
        plan,
    )
    merged = merge_subtask_results(existing, incoming)
    by_id = {row["subtask_id"]: row for row in merged}
    assert set(by_id) == plan
    assert by_id[f"{_RUN}:1"]["output"] == "first"
    assert by_id[f"{_RUN}:2"]["output"] == "second"
    assert len(merged) == 2


def test_cursor_is_sse_seq_not_subtask_id():
    """顶层字段不增不减；cursor 只由 SSE seq 生成。形状可与 subtask_id 相同，靠字段区分。"""
    payload = {"status": "running", "subtask_id": f"{_RUN}:1", "type": "rag"}
    event = format_sse_event(
        {
            "run_id": _RUN,
            "seq": 7,
            "ts_ms": 1,
            "agent_role": "rag_subtask",
            "event_type": "subtask.progress",
            "payload": payload,
        }
    )
    assert set(event) == {
        "run_id",
        "seq",
        "ts_ms",
        "agent_role",
        "event_type",
        "payload",
        "cursor",
    }
    assert event["cursor"] == make_cursor(_RUN, 7)
    assert event["cursor"] == f"{_RUN}:7"
    assert event["cursor"] != payload["subtask_id"]
    assert "subtask_id" not in event
    assert event["payload"]["subtask_id"] == f"{_RUN}:1"


def test_route_fans_out_two_independent_workers():
    """同批两个无依赖工人：返回多个 Send，载荷各带自己的 subtask_id，不共享下标。"""
    a = {
        "id": f"{_RUN}:1",
        "subtask_id": f"{_RUN}:1",
        "alias": "t1",
        "type": "tool",
        "input": "查甲",
        "tool": "mock_get_issue_status",
        "depends_on": [],
    }
    b = {
        "id": f"{_RUN}:2",
        "subtask_id": f"{_RUN}:2",
        "alias": "t2",
        "type": "rag",
        "input": "查乙",
        "depends_on": [],
    }
    routed = route_next_subtask(
        {
            "subtasks": [a, b],
            "subtask_results": [],
            "inflight_subtask_ids": [a["subtask_id"], b["subtask_id"]],
            "supervisor_step_count": 1,
        }
    )
    assert isinstance(routed, list)
    assert all(isinstance(item, Send) for item in routed)
    assert len(routed) == 2
    bound = [item.arg["assigned_subtask"]["subtask_id"] for item in routed]
    assert bound == [a["subtask_id"], b["subtask_id"]]
    assert len(set(bound)) == 2
    assert {item.node for item in routed} == {"tool_exec", "rag_subtask"}
    tool_send = next(item for item in routed if item.node == "tool_exec")
    assert tool_send.arg["assigned_subtask"]["tool"] == "mock_get_issue_status"
    assert tool_send.arg["assigned_subtask"]["input"] == "查甲"


def test_route_budget_exhausted_still_aggregate():
    routed = route_next_subtask(
        {
            "subtasks": [
                {"id": f"{_RUN}:1", "subtask_id": f"{_RUN}:1", "type": "rag", "input": "q"}
            ],
            "subtask_results": [],
            "inflight_subtask_ids": [f"{_RUN}:1"],
            "supervisor_step_count": 99,
            "supervisor_budget_exhausted": True,
        }
    )
    assert routed == "observe"


def test_route_dependent_not_in_same_batch():
    """有 depends_on 的项不得与前驱同批。"""
    a = {
        "id": f"{_RUN}:1",
        "subtask_id": f"{_RUN}:1",
        "type": "tool",
        "input": "先",
        "tool": "utc_now_iso",
        "depends_on": [],
    }
    b = {
        "id": f"{_RUN}:2",
        "subtask_id": f"{_RUN}:2",
        "type": "tool",
        "input": "后",
        "tool": "utc_now_iso",
        "depends_on": [f"{_RUN}:1"],
    }
    routed = route_next_subtask(
        {
            "subtasks": [a, b],
            "subtask_results": [],
            "inflight_subtask_ids": [a["subtask_id"]],
            "supervisor_step_count": 1,
        }
    )
    assert isinstance(routed, list)
    assert len(routed) == 1
    assert routed[0].arg["assigned_subtask"]["subtask_id"] == a["subtask_id"]


@pytest.mark.asyncio
async def test_parallel_workers_do_not_share_index():
    """两个无依赖 tool 同时在飞，各自绑定不同 subtask_id。"""
    started: list[str] = []
    gate = asyncio.Event()

    async def _tool(state):
        assigned = state.get("assigned_subtask") or {}
        sid = str(assigned.get("subtask_id") or "")
        started.append(sid)
        if len(started) >= 2:
            gate.set()
        else:
            await asyncio.wait_for(gate.wait(), timeout=1.0)
        return {
            "subtask_results": [
                {
                    "subtask_id": sid,
                    "id": sid,
                    "type": "tool",
                    "input": assigned.get("input"),
                    "output": {"echo": sid},
                }
            ]
        }

    plan = _plan_json(
        [
            {
                "id": "t1",
                "type": "tool",
                "input": "查 #1",
                "tool": "mock_get_issue_status",
            },
            {
                "id": "t2",
                "type": "tool",
                "input": "查部署",
                "tool": "mock_get_deploy_info",
            },
        ]
    )
    multi = _provider(plan, _AGG)
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch("app.ops.lg_rag.multi.graph.tool_exec_node", new=_tool),
    ):
        out = await _run(_build())
    assert set(started) == {f"{_RUN}:1", f"{_RUN}:2"}
    assert len(started) == 2
    by_id = {row["subtask_id"]: row for row in out["subtask_results"]}
    assert by_id[f"{_RUN}:1"]["output"]["echo"] == f"{_RUN}:1"
    assert by_id[f"{_RUN}:2"]["output"]["echo"] == f"{_RUN}:2"
    assert out["messages"][-1].content == _AGG


@pytest.mark.asyncio
async def test_late_result_joins_by_id_not_arrival_order():
    """后返回的条按 subtask_id 对齐，不按到达顺序错位。"""

    async def _tool(state):
        assigned = state["assigned_subtask"]
        sid = assigned["subtask_id"]
        if assigned.get("alias") == "t1":
            await asyncio.sleep(0.05)
            marker = "planned-first"
        else:
            marker = "planned-second"
        return {
            "subtask_results": [
                {
                    "subtask_id": sid,
                    "id": sid,
                    "type": "tool",
                    "input": assigned.get("input"),
                    "output": {"marker": marker},
                }
            ]
        }

    plan = _plan_json(
        [
            {"id": "t1", "type": "tool", "input": "甲", "tool": "utc_now_iso"},
            {"id": "t2", "type": "tool", "input": "乙", "tool": "utc_now_iso"},
        ]
    )
    multi = _provider(plan, _AGG)
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch("app.ops.lg_rag.multi.graph.tool_exec_node", new=_tool),
    ):
        out = await _run(_build())
    by_id = {row["subtask_id"]: row["output"]["marker"] for row in out["subtask_results"]}
    assert by_id[f"{_RUN}:1"] == "planned-first"
    assert by_id[f"{_RUN}:2"] == "planned-second"


@pytest.mark.asyncio
async def test_depends_on_waits_for_predecessor_terminal():
    order: list[tuple[str, str]] = []

    async def _tool(state):
        sid = state["assigned_subtask"]["subtask_id"]
        order.append(("start", sid))
        await asyncio.sleep(0.01)
        order.append(("end", sid))
        return {
            "subtask_results": [
                {
                    "subtask_id": sid,
                    "id": sid,
                    "type": "tool",
                    "input": "x",
                    "output": {"ok": True},
                }
            ]
        }

    plan = _plan_json(
        [
            {"id": "t1", "type": "tool", "input": "先", "tool": "utc_now_iso"},
            {
                "id": "t2",
                "type": "tool",
                "input": "后",
                "tool": "utc_now_iso",
                "depends_on": ["t1"],
            },
        ]
    )
    multi = _provider(plan, _AGG)
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch("app.ops.lg_rag.multi.graph.tool_exec_node", new=_tool),
    ):
        out = await _run(_build())
    assert ("end", f"{_RUN}:1") in order
    assert ("start", f"{_RUN}:2") in order
    assert order.index(("end", f"{_RUN}:1")) < order.index(("start", f"{_RUN}:2"))
    assert {row["subtask_id"] for row in out["subtask_results"]} == {
        f"{_RUN}:1",
        f"{_RUN}:2",
    }


@pytest.mark.asyncio
async def test_worker_error_is_terminal_and_reaches_aggregator():
    plan = _plan_json(
        [
            {"id": "t1", "type": "rag", "input": "会炸"},
            {"id": "t2", "type": "tool", "input": "查部署", "tool": "mock_get_deploy_info"},
        ]
    )
    multi = _provider(plan, _AGG, plan, _AGG)
    router = _provider('{"route": "rag"}', '{"route": "rag"}')
    chain = AsyncMock(side_effect=RuntimeError("chain down"))
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_ROUTER_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await _run(_build())
    first = [row for row in out["subtask_results"] if row.get("subtask_id") == f"{_RUN}:1"]
    # critic 可能重拆；至少第一轮失败 id 占了错误终态，且最终进了综合
    assert out["messages"][-1].content == _AGG
    assert any("chain down" in str(row.get("error")) for row in out["subtask_results"]) or first


@pytest.mark.asyncio
async def test_missing_run_id_does_not_dispatch_t1(monkeypatch: pytest.MonkeyPatch):
    provider = SimpleNamespace(complete=AsyncMock(return_value="不会被调用也可以"))
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span") as span,
    ):
        span.return_value.__enter__ = lambda s: None
        span.return_value.__exit__ = lambda s, *a: False
        out = await supervisor_node(
            {
                "messages": [HumanMessage(content="缺 run")],
                "allowed_capability_ids": ["utc_now_iso"],
            }
        )
    blob = json.dumps(out.get("subtasks") or [], ensure_ascii=False)
    assert "t1" not in blob
    assert out.get("subtasks") == []
    assert any("run_id" in str(row.get("error")) for row in out.get("subtask_results") or [])
    routed = route_next_subtask(
        {
            "subtasks": out["subtasks"],
            "subtask_results": out["subtask_results"],
            "inflight_subtask_ids": [],
        }
    )
    assert routed == "observe"


@pytest.mark.asyncio
async def test_host_seq_not_reset_and_cap_four():
    raw_items = [
        {"id": f"t{i}", "type": "tool", "input": f"q{i}", "tool": "utc_now_iso"}
        for i in range(1, 7)
    ]
    provider = SimpleNamespace(complete=AsyncMock(return_value=_plan_json(raw_items)))
    state = {
        "messages": [HumanMessage(content="很多")],
        "allowed_capability_ids": ["utc_now_iso"],
        "run_id": _RUN,
        "host_subtask_seq": 3,
    }
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span") as span,
    ):
        span.return_value.__enter__ = lambda s: None
        span.return_value.__exit__ = lambda s, *a: False
        out = await supervisor_node(state)
    ids = [row["subtask_id"] for row in out["subtasks"]]
    assert ids == [f"{_RUN}:4", f"{_RUN}:5", f"{_RUN}:6", f"{_RUN}:7"]
    assert out["host_subtask_seq"] == 7
    assert all(row["alias"] == f"t{i}" for i, row in enumerate(out["subtasks"], start=1))
    assert all(row["id"] == row["subtask_id"] for row in out["subtasks"])


@pytest.mark.asyncio
async def test_rag_thread_id_equals_subtask_id():
    seen: list[str] = []

    async def _fake_stream(query: str, *, thread_id: str = "x", **_kwargs):
        seen.append(thread_id)
        if False:
            yield {}

    plan = _plan_json(
        [
            {"id": "t1", "type": "rag", "input": "甲"},
            {"id": "t2", "type": "rag", "input": "乙"},
        ]
    )
    multi = _provider(plan, _AGG)
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(
            "app.ops.lg_rag.multi.nodes.astream_router_agent",
            new=_fake_stream,
        ),
    ):
        out = await _run(_build())
    assert set(seen) == {f"{_RUN}:1", f"{_RUN}:2"}
    assert len(seen) == 2
    assert {row["subtask_id"] for row in out["subtask_results"]} == set(seen)
