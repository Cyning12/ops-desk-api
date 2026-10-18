"""lg_rag StateGraph 组装（Phase 1 basic + Phase 2 router）。

说明书：
- Phase 1：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S3/S4
- Phase 2：docs/guides/DESIGN_langgraph-lg-rag-phase2-router_v1.md §1

拓扑：
- basic ：START → rag → END（Phase 1，保留作回归对照与回滚）
- router：START → router ─┬─ direct → direct_answer → END
                          ├─ refuse → refuse → END
                          └─ rag → rag → evaluate ─┬─ high/medium → END
                                                   └─ low → rewrite → rag（回环 ≤2 次）

默认 InMemorySaver；ainvoke 注入 Langfuse（propagate_attributes
修内层 run_name 抢占，见 Phase 1 修订记录）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import nullcontext
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.ops.lg_rag.continuity import assemble_graph_messages_with_memory
from app.ops.lg_rag.nodes import (
    direct_answer_node,
    evaluate_node,
    rag_node,
    refuse_node,
    rewrite_node,
    route_after_rewrite,
    route_by_quality,
    route_by_route,
    router_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.tenant_context import current_tenant
from app.ops.tracing import (
    ensure_langfuse_environment,
    trace_span,
    tracing_enabled,
)

_RUN_NAME = "lg-rag"
_TAG = "lg-rag"


def _compile(builder: StateGraph, checkpointer: Any | None):
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    return builder.compile(checkpointer=saver)


def build_basic_agent(*, checkpointer: Any | None = None):
    """START → rag → END；默认 InMemorySaver（Phase 1，保留对照）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("rag", rag_node)
    builder.add_edge(START, "rag")
    builder.add_edge("rag", END)
    return _compile(builder, checkpointer)


def build_router_agent(*, checkpointer: Any | None = None):
    """START → router → 三路；rag 路径带 evaluate/rewrite 自纠错回环（≤2 次）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("router", router_node)
    builder.add_node("rag", rag_node)
    builder.add_node("direct_answer", direct_answer_node)
    builder.add_node("refuse", refuse_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        route_by_route,
        {
            "rag": "rag",
            "direct": "direct_answer",
            "refuse": "refuse",
        },
    )
    builder.add_edge("rag", "evaluate")
    builder.add_conditional_edges(
        "evaluate",
        route_by_quality,
        {
            "rewrite": "rewrite",
            "end": END,
        },
    )
    builder.add_conditional_edges(
        "rewrite",
        route_after_rewrite,
        {
            "rag": "rag",
            "end": END,
        },
    )
    builder.add_edge("direct_answer", END)
    builder.add_edge("refuse", END)
    return _compile(builder, checkpointer)


def _trace_config(*, thread_id: str | None = None) -> dict | None:
    if not tracing_enabled():
        return None
    ensure_langfuse_environment()
    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        return None
    metadata: dict = {"langfuse_tags": [_TAG]}
    if thread_id:
        metadata["langfuse_session_id"] = thread_id
    return {
        "callbacks": [CallbackHandler()],
        "metadata": metadata,
        "run_name": _RUN_NAME,
    }


def _run_config(thread_id: str) -> dict[str, Any]:
    """thread_id + 可选 Langfuse callbacks。"""
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id[:255]}}
    if tc := _trace_config(thread_id=thread_id):
        config = {**tc, "configurable": config["configurable"]}
    return config


def _tracing_contexts(thread_id: str):
    """根 span + propagate_attributes；返回 (span_cm, attr_cm)。"""
    span_cm = (
        trace_span(_RUN_NAME, run_type="chain", tags=[_TAG]) if tracing_enabled() else nullcontext()
    )
    if tracing_enabled():
        try:
            from langfuse import propagate_attributes

            attr_cm = propagate_attributes(trace_name=_RUN_NAME, session_id=thread_id, tags=[_TAG])
        except Exception:  # SDK 可选；失败不挡主流程
            attr_cm = nullcontext()
    else:
        attr_cm = nullcontext()
    return span_cm, attr_cm


async def _ainvoke_with_tracing(
    graph: Any,
    query: str,
    *,
    thread_id: str,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """共享 ainvoke 外壳：历史压缩 + 本轮 query 装配 + Langfuse。

    `user_id`（session 用户，由 HTTP 入口显式传入）+ tenant ContextVar
    仅供记忆注入（memory-facts-p0）；`MEMORY_FACTS_ENABLED` 默认关，
    关闭时装配与现网逐字节一致。
    """
    config = _run_config(thread_id)
    span_cm, attr_cm = _tracing_contexts(thread_id)
    messages = await assemble_graph_messages_with_memory(
        query,
        history_turns,
        tenant_id=current_tenant(),
        user_id=user_id,
        thread_id=thread_id,
    )
    payload: dict[str, Any] = {"messages": messages}
    if run_id:
        payload["run_id"] = run_id
    with span_cm, attr_cm:
        # 官方推荐的 trace 级属性传播：trace_name/session/tags 写到当前 span
        # 并随上下文传播给所有子 span。内层 LCEL 的 CallbackHandler 在其根
        # run 会 update_trace(name="lc-evidence-chain")，后置
        # update_current_trace 实测抢不回命名，故用 propagate_attributes。
        return await graph.ainvoke(payload, config)


async def _astream_with_tracing(
    graph: Any,
    query: str,
    *,
    thread_id: str,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
    user_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """共享 astream(updates) 外壳；yield 每个节点 update dict。

    `user_id` 语义同 `_ainvoke_with_tracing`（记忆注入身份；默认关零 diff）。
    """
    config = _run_config(thread_id)
    span_cm, attr_cm = _tracing_contexts(thread_id)
    messages = await assemble_graph_messages_with_memory(
        query,
        history_turns,
        tenant_id=current_tenant(),
        user_id=user_id,
        thread_id=thread_id,
    )
    payload: dict[str, Any] = {"messages": messages}
    if run_id:
        payload["run_id"] = run_id
    with span_cm, attr_cm:
        async for update in graph.astream(
            payload,
            config,
            stream_mode="updates",
        ):
            yield update


async def ainvoke_basic_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Phase 1 单节点图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_basic_agent(checkpointer=checkpointer)
    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    return await _ainvoke_with_tracing(
        graph, query, thread_id=thread_id, history_turns=history_turns, **kwargs
    )


async def astream_basic_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    user_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Phase 1 basic · astream(updates)。"""
    graph = build_basic_agent(checkpointer=checkpointer)
    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    async for update in _astream_with_tracing(
        graph, query, thread_id=thread_id, history_turns=history_turns, **kwargs
    ):
        yield update


async def ainvoke_router_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Phase 2 三路路由图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_router_agent(checkpointer=checkpointer)
    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    return await _ainvoke_with_tracing(
        graph, query, thread_id=thread_id, history_turns=history_turns, **kwargs
    )


async def astream_router_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    user_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Phase 2 router · astream(updates)。"""
    graph = build_router_agent(checkpointer=checkpointer)
    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    async for update in _astream_with_tracing(
        graph, query, thread_id=thread_id, history_turns=history_turns, **kwargs
    ):
        yield update
