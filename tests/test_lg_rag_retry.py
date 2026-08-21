"""lg_rag Phase 3 自纠错：evaluate/rewrite 回环与熔断（mock，不连库）。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase3-selfcorrect_v1.md §7。
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.lc_evidence_chain.types import ChainResult

_CHAIN_PATCH = "app.ops.lg_rag.nodes.ainvoke_evidence_answer"
_PROVIDER_PATCH = "app.ops.lg_rag.nodes.get_llm_provider"
_TECH_QUERY = "这个函数为什么会报错"


def _result(answer: str, gate: str, kept: int = 1) -> ChainResult:
    return ChainResult(
        query="q",
        evidence=[],
        answer=answer,
        meta={"gate_action": gate, "kept_count": kept, "hit_count": kept},
    )


def _provider(*outputs: str) -> SimpleNamespace:
    return SimpleNamespace(complete=AsyncMock(side_effect=list(outputs)))


def _build():
    from app.ops.lg_rag.graph import build_router_agent

    return build_router_agent(checkpointer=InMemorySaver())


async def _run(graph, query: str = _TECH_QUERY, thread_id: str = "t-p3"):
    return await graph.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        {"configurable": {"thread_id": thread_id}},
    )


@pytest.mark.asyncio
async def test_high_quality_no_retry():
    """gate=answer → high → 直接 END，rewrite 不被调用。"""
    chain = AsyncMock(return_value=_result("好答案", "answer"))
    provider = _provider('{"route": "rag"}')
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    chain.assert_awaited_once()
    assert provider.complete.await_count == 1  # 仅 router 分类
    assert out["messages"][-1].content == "好答案"
    assert (out.get("retry_count") or 0) == 0


@pytest.mark.asyncio
async def test_medium_quality_no_retry():
    """gate=answer_partial → medium → END 不重试（DESIGN §3 取舍）。"""
    chain = AsyncMock(return_value=_result("部分答案", "answer_partial"))
    provider = _provider('{"route": "rag"}')
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    chain.assert_awaited_once()
    assert (out.get("retry_count") or 0) == 0


@pytest.mark.asyncio
async def test_low_triggers_rewrite_and_uses_rewritten_query():
    """low → rewrite → rag 用改写后 query 重试；第二次 high → END。"""
    chain = AsyncMock(
        side_effect=[_result("拒答", "refuse", 0), _result("改后好答案", "answer")]
    )
    provider = _provider('{"route": "rag"}', "改写后的技术问题")
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    assert chain.await_count == 2
    # 第二次 chain 调用用的是改写后 query
    second_call_query = chain.await_args_list[1].args[0]
    assert second_call_query == "改写后的技术问题"
    assert out["retry_count"] == 1
    assert out["current_query"] == "改写后的技术问题"
    assert out["messages"][-1].content == "改后好答案"


@pytest.mark.asyncio
async def test_circuit_breaker_max_two_retries():
    """连续 low：rag 共 3 次（首 + 2 重试），rewrite 恰好 2 次后熔断。"""
    chain = AsyncMock(return_value=_result("仍拒答", "refuse", 0))
    provider = _provider('{"route": "rag"}', "改写一", "改写二")
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    assert chain.await_count == 3
    assert provider.complete.await_count == 3  # router 1 + rewrite 2
    assert out["retry_count"] == 2
    assert out["messages"][-1].content == "仍拒答"


@pytest.mark.asyncio
async def test_rewrite_llm_failure_ends_immediately():
    """rewrite LLM 异常 → 清空 current_query 顶格 retry_count → END，不再 rag。"""
    chain = AsyncMock(return_value=_result("拒答", "refuse", 0))
    provider = SimpleNamespace(
        complete=AsyncMock(
            side_effect=['{"route": "rag"}', RuntimeError("llm down")]
        )
    )
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    chain.assert_awaited_once()  # 无第二次 rag
    assert out["retry_count"] == 2  # MAX_RETRIES 顶格（熔断记号）
    assert not out.get("current_query")


@pytest.mark.asyncio
async def test_rewrite_same_query_ends():
    """rewrite 输出与原 query 相同 → 视为无法改写，终止回环。"""
    chain = AsyncMock(return_value=_result("拒答", "refuse", 0))
    provider = _provider('{"route": "rag"}', _TECH_QUERY)
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    chain.assert_awaited_once()
    assert not out.get("current_query")


@pytest.mark.asyncio
async def test_missing_chain_meta_treated_high():
    """chain_meta 缺失（老 checkpoint）→ 视为 high，不回环。"""
    chain = AsyncMock(return_value=ChainResult(query="q", evidence=[], answer="a", meta={}))
    provider = _provider('{"route": "rag"}')
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build())
    chain.assert_awaited_once()
    assert (out.get("retry_count") or 0) == 0


@pytest.mark.asyncio
async def test_direct_route_bypasses_retry():
    """direct 路径不进 rag/evaluate（回环只挂 rag 路径）。"""
    chain = AsyncMock(return_value=_result("不应出现", "answer"))
    provider = _provider('{"route": "direct"}', "你好呀")
    with (
        patch(_CHAIN_PATCH, new=chain),
        patch(_PROVIDER_PATCH, return_value=provider),
    ):
        out = await _run(_build(), query="你好")
    chain.assert_not_awaited()
    assert out["messages"][-1].content == "你好呀"
