"""lg_rag Phase 1：mock ainvoke_evidence_answer，不连真库 / LLM 也可绿。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S7。
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.lc_evidence_chain.types import ChainResult


def _fake(answer: str = "ok-from-chain") -> ChainResult:
    return ChainResult(query="q", evidence=[], answer=answer, meta={})


@pytest.mark.asyncio
async def test_basic_agent_appends_ai_message():
    with patch(
        "app.ops.lg_rag.nodes.ainvoke_evidence_answer",
        new=AsyncMock(return_value=_fake()),
    ):
        from app.ops.lg_rag.graph import build_basic_agent

        graph = build_basic_agent(checkpointer=InMemorySaver())
        out = await graph.ainvoke(
            {"messages": [HumanMessage(content="q")]},
            {"configurable": {"thread_id": "t-test"}},
        )
    last = out["messages"][-1]
    assert isinstance(last, AIMessage)
    assert last.content == "ok-from-chain"


@pytest.mark.asyncio
async def test_same_thread_id_continues_messages():
    """同 thread_id 连续两次 invoke：messages 增长（验证 checkpointer 续写）。"""
    saver = InMemorySaver()
    with patch(
        "app.ops.lg_rag.nodes.ainvoke_evidence_answer",
        new=AsyncMock(side_effect=[_fake("a1"), _fake("a2")]),
    ):
        from app.ops.lg_rag.graph import build_basic_agent

        graph = build_basic_agent(checkpointer=saver)
        cfg = {"configurable": {"thread_id": "t-cont"}}
        out1 = await graph.ainvoke({"messages": [HumanMessage(content="q1")]}, cfg)
        out2 = await graph.ainvoke({"messages": [HumanMessage(content="q2")]}, cfg)
    assert len(out1["messages"]) == 2  # Human + AI
    assert len(out2["messages"]) == 4  # 续写：上轮 2 条 + 本轮 2 条
    assert out2["messages"][-1].content == "a2"


@pytest.mark.asyncio
async def test_custom_checkpointer_resume_across_graph_instances():
    """共享 checkpointer + 重建图实例（模拟进程重启）：同 thread_id 续写。

    语义等价于 S5 PostgresSaver 的「重启后恢复」：图实例可丢弃，
    状态由 checkpointer 持有。真实 PG 路径由 scripts/lg_rag_smoke.py
    --postgres 跨进程验证。
    """
    saver = InMemorySaver()
    with patch(
        "app.ops.lg_rag.nodes.ainvoke_evidence_answer",
        new=AsyncMock(side_effect=[_fake("r1"), _fake("r2")]),
    ):
        from app.ops.lg_rag.graph import build_basic_agent

        cfg = {"configurable": {"thread_id": "t-restart"}}
        g1 = build_basic_agent(checkpointer=saver)
        out1 = await g1.ainvoke({"messages": [HumanMessage(content="q1")]}, cfg)
        # 模拟重启：丢掉图实例，用同一 saver 重新 compile
        g2 = build_basic_agent(checkpointer=saver)
        out2 = await g2.ainvoke({"messages": [HumanMessage(content="q2")]}, cfg)
    assert len(out1["messages"]) == 2
    assert len(out2["messages"]) == 4
    assert out2["messages"][-1].content == "r2"


def test_build_basic_agent_respects_given_checkpointer():
    """传入的 checkpointer 必须被采用（S5 注入点）。"""
    from app.ops.lg_rag.graph import build_basic_agent

    saver = InMemorySaver()
    graph = build_basic_agent(checkpointer=saver)
    assert graph.checkpointer is saver


@pytest.mark.asyncio
async def test_ainvoke_basic_agent_helper():
    """库级入口 ainvoke_basic_agent 返回末条 AIMessage。"""
    with patch(
        "app.ops.lg_rag.nodes.ainvoke_evidence_answer",
        new=AsyncMock(return_value=_fake("helper-ok")),
    ):
        from app.ops.lg_rag.graph import ainvoke_basic_agent

        out = await ainvoke_basic_agent("q", thread_id="t-helper")
    assert out["messages"][-1].content == "helper-ok"
