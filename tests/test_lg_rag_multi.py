"""lg_rag Phase 4 · Multi-Agent（Supervisor 协作）全链与容错（mock，不连库）。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md §7。

mock 三处：
- multi 自己的 LLM（supervisor/extract/aggregator）：
  patch app.ops.lg_rag.multi.nodes.get_llm_provider
- rag 子图内部 router 的 LLM 与 evidence chain：
  patch app.ops.lg_rag.nodes.get_llm_provider /
        app.ops.lg_rag.nodes.ainvoke_evidence_answer
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.lc_evidence_chain.types import ChainResult
from app.ops.lg_rag.multi.nodes import route_next_subtask
from app.ops.lg_rag.schemas import IntentV1

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
    summary="复合运维查询",
)
_QUERY = "超时问题查一下，顺带抽取发版信息，再看看 issue 状态"
_AGGREGATED = "## 综合结论\n已覆盖全部子任务。"


def _result(answer: str, gate: str = "answer", kept: int = 1) -> ChainResult:
    return ChainResult(
        query="q",
        evidence=[],
        answer=answer,
        meta={"gate_action": gate, "kept_count": kept, "hit_count": kept},
    )


def _provider(*outputs) -> SimpleNamespace:
    return SimpleNamespace(complete=AsyncMock(side_effect=list(outputs)))


def _subtasks_json(subtasks: list[dict]) -> str:
    return json.dumps({"subtasks": subtasks}, ensure_ascii=False)


def _build():
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    return build_supervisor_agent(checkpointer=InMemorySaver())


async def _run(graph, query: str = _QUERY, thread_id: str = "t-p4"):
    with patch(_INTENT_COMPLETE_PATCH, new=AsyncMock(return_value=_INTENT_OK)):
        return await graph.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            {"configurable": {"thread_id": thread_id}},
        )


@pytest.mark.asyncio
async def test_full_chain_decompose_dispatch_aggregate():
    """全链：拆解 rag+extract+tool → 顺序分派 → aggregator 综合。"""
    supervisor_out = _subtasks_json(
        [
            {"id": "t1", "type": "rag", "input": "超时问题怎么排查"},
            {"id": "t2", "type": "extract", "input": "2026-08-20 cyning 发布 v2.3.1"},
            {
                "id": "t3",
                "type": "tool",
                "input": "查 #128 状态",
                "tool": "mock_get_issue_status",
            },
        ]
    )
    extract_out = '{"dates": ["2026-08-20"], "versions": ["v2.3.1"], "people": ["cyning"]}'
    multi = _provider(supervisor_out, extract_out, _AGGREGATED)
    router = _provider('{"route": "rag"}')
    chain = AsyncMock(return_value=_result("检索答案"))
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_ROUTER_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await _run(_build())
    assert len(out["subtasks"]) == 3
    results = out["subtask_results"]
    assert [r["type"] for r in results] == ["rag", "extract", "tool"]
    # rag 子任务：复用 router 图，输出末条 AIMessage + chain_meta 摘要
    chain.assert_awaited_once()
    assert chain.await_args_list[0].args[0] == "超时问题怎么排查"
    assert results[0]["output"] == "检索答案"
    assert results[0]["chain_meta"]["gate_action"] == "answer"
    # extract 子任务：解析为结构化实体
    assert results[1]["output"] == {
        "dates": ["2026-08-20"],
        "versions": ["v2.3.1"],
        "people": ["cyning"],
    }
    # tool 子任务：命中 Mock 注册表罐头数据
    assert results[2]["output"]["issue"] == "#128"
    # 中间结果不进 messages：仅 HumanMessage + 最终 AIMessage
    assert len(out["messages"]) == 2
    assert out["messages"][-1].content == _AGGREGATED
    # supervisor + extract + aggregator 共 3 次 multi LLM；router 分类 1 次；critic 无 LLM
    assert multi.complete.await_count == 3
    assert router.complete.await_count == 1
    assert out["critic_verdict"]["outcome"] == "pass"


@pytest.mark.asyncio
async def test_cap_four_truncation():
    """cap=4：supervisor 拆出 6 个子任务 → 截断为 4 个。"""
    supervisor_out = _subtasks_json(
        [
            {
                "id": f"t{i}",
                "type": "tool",
                "input": f"查部署 {i}",
                "tool": "mock_get_deploy_info",
            }
            for i in range(1, 7)
        ]
    )
    multi = _provider(supervisor_out, _AGGREGATED)
    with patch(_MULTI_PROVIDER_PATCH, return_value=multi):
        out = await _run(_build())
    assert len(out["subtasks"]) == 4
    assert len(out["subtask_results"]) == 4
    assert all(r["type"] == "tool" for r in out["subtask_results"])
    assert out["messages"][-1].content == _AGGREGATED


@pytest.mark.asyncio
async def test_decompose_invalid_json_fallback_single_rag():
    """拆解输出非法 → fallback 单 rag 子任务（宁退化不失败）。"""
    multi = _provider("这个问题我拆不了", _AGGREGATED)
    router = _provider('{"route": "rag"}')
    chain = AsyncMock(return_value=_result("兜底检索答案"))
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_ROUTER_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await _run(_build())
    assert out["subtasks"] == [{"id": "t1", "type": "rag", "input": _QUERY}]
    assert len(out["subtask_results"]) == 1
    assert out["subtask_results"][0]["output"] == "兜底检索答案"
    assert out["messages"][-1].content == _AGGREGATED


@pytest.mark.asyncio
async def test_decompose_llm_exception_fallback_single_rag():
    """拆解 LLM 异常 → 同样 fallback 单 rag 子任务。"""
    multi = _provider(RuntimeError("llm down"), _AGGREGATED)
    router = _provider('{"route": "rag"}')
    chain = AsyncMock(return_value=_result("兜底检索答案"))
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_ROUTER_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await _run(_build())
    assert out["subtasks"] == [{"id": "t1", "type": "rag", "input": _QUERY}]
    assert out["subtask_results"][0]["output"] == "兜底检索答案"


@pytest.mark.asyncio
async def test_extract_invalid_json_falls_back_empty():
    """extract 输出非法 JSON → 空结构 + 不中断，aggregator 照常综合。"""
    supervisor_out = _subtasks_json(
        [{"id": "t1", "type": "extract", "input": "随便一段文本"}]
    )
    multi = _provider(supervisor_out, "这不是 JSON", _AGGREGATED)
    with patch(_MULTI_PROVIDER_PATCH, return_value=multi):
        out = await _run(_build())
    results = out["subtask_results"]
    assert len(results) == 1
    assert results[0]["output"] == {"dates": [], "versions": [], "people": []}
    assert "error" not in results[0]
    assert out["messages"][-1].content == _AGGREGATED


@pytest.mark.asyncio
async def test_invalid_tool_id_in_plan_fallback_single_rag():
    """H1：plan 含非法 tool id → supervisor 整 plan fallback 单 rag（不进入 tool_exec）。"""
    supervisor_out = _subtasks_json(
        [
            {"id": "t1", "type": "tool", "input": "查点什么", "tool": "no_such_tool"},
            {
                "id": "t2",
                "type": "tool",
                "input": "查部署",
                "tool": "mock_get_deploy_info",
            },
        ]
    )
    router = _provider('{"route": "direct"}')
    chain = AsyncMock(return_value=_result("direct 答案"))
    multi = _provider(supervisor_out, _AGGREGATED)
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_ROUTER_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await _run(_build())
    assert len(out["subtasks"]) == 1
    assert out["subtasks"][0]["type"] == "rag"
    assert len(out["subtask_results"]) == 1
    assert out["messages"][-1].content == _AGGREGATED


@pytest.mark.asyncio
async def test_unknown_tool_at_invoke_recorded_and_continues():
    """tool_exec：invoke 未知 id → 错误结果记录；合法 tool 子任务照常（绕过 supervisor）。"""
    from app.ops.lg_rag.multi.nodes import tool_exec_node

    state_unknown = {
        "subtasks": [
            {"id": "t1", "type": "tool", "input": "查什么", "tool": "no_such_tool"},
        ],
        "subtask_results": [],
    }
    out1 = await tool_exec_node(state_unknown)
    assert "未知工具" in out1["subtask_results"][0]["error"]

    state_valid = {
        "subtasks": [
            {"id": "t2", "type": "tool", "input": "查部署", "tool": "mock_get_deploy_info"},
        ],
        "subtask_results": [],
    }
    out2 = await tool_exec_node(state_valid)
    assert out2["subtask_results"][0]["output"]["version"] == "v2.3.1"


def test_supervisor_graph_includes_strategy_builder_node():
    """S1：supervisor 图拓扑含 strategy_builder 前置节点。"""
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    graph = build_supervisor_agent()
    node_names = set(graph.get_graph().nodes.keys())
    assert "intent_node" in node_names
    assert "strategy_builder" in node_names
    assert "supervisor" in node_names


def test_empty_subtasks_dispatch_goes_aggregate():
    """空 subtasks / 耗尽 → dispatch 直走 aggregate（防死循环）。"""
    assert route_next_subtask({"subtasks": [], "subtask_results": []}) == "aggregate"
    assert (
        route_next_subtask(
            {
                "subtasks": [{"id": "t1", "type": "rag", "input": "q"}],
                "subtask_results": [{"type": "rag", "output": "a"}],
            }
        )
        == "aggregate"
    )
    assert (
        route_next_subtask(
            {
                "subtasks": [{"id": "t1", "type": "extract", "input": "q"}],
                "subtask_results": [],
            }
        )
        == "info_extract"
    )


@pytest.mark.asyncio
async def test_subtask_exception_recorded_and_continues():
    """单个 rag 子任务异常 → 记录错误结果，后续 tool 子任务照常执行。"""
    supervisor_out = _subtasks_json(
        [
            {"id": "t1", "type": "rag", "input": "会炸的检索"},
            {
                "id": "t2",
                "type": "tool",
                "input": "查部署",
                "tool": "mock_get_deploy_info",
            },
        ]
    )
    # 非空 allowlist → 第一次 critic 为 retry_planner，需第二次 supervisor + aggregator
    multi = _provider(supervisor_out, _AGGREGATED, supervisor_out, _AGGREGATED)
    router = _provider('{"route": "rag"}', '{"route": "rag"}')
    chain = AsyncMock(side_effect=RuntimeError("chain down"))
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_ROUTER_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await _run(_build())
    results = out["subtask_results"]
    assert len(results) == 2
    assert "chain down" in results[0]["error"]
    assert results[1]["output"]["status"] == "healthy"
    assert out["messages"][-1].content == _AGGREGATED
    assert out["inner_retry_count"] == 1
    assert out["critic_verdict"]["outcome"] == "end"


@pytest.mark.asyncio
async def test_three_graphs_coexist():
    """三图并存：basic / router / supervisor 均可构建且导出。"""
    from app.ops.lg_rag import (
        ainvoke_supervisor_agent,
        build_basic_agent,
        build_router_agent,
        build_supervisor_agent,
    )

    assert build_basic_agent() is not None
    assert build_router_agent() is not None
    assert build_supervisor_agent() is not None
    assert callable(ainvoke_supervisor_agent)
