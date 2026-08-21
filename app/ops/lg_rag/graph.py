"""lg_rag StateGraph 组装（Phase 1 basic + Phase 2 router）。

说明书：
- Phase 1：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S3/S4
- Phase 2：docs/guides/DESIGN_langgraph-lg-rag-phase2-router_v1.md §1

拓扑：
- basic ：START → rag → END（Phase 1，保留作回归对照与回滚）
- router：START → router ─┬─ direct → direct_answer → END
                          ├─ refuse → refuse → END
                          └─ rag → rag → END

默认 InMemorySaver；ainvoke 注入 Langfuse（propagate_attributes
修内层 run_name 抢占，见 Phase 1 修订记录）。
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.ops.lg_rag.nodes import (
    direct_answer_node,
    rag_node,
    refuse_node,
    route_by_route,
    router_node,
)
from app.ops.lg_rag.state import LgRagState
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
    """START → router → direct/rag/refuse 三路；默认 InMemorySaver（Phase 2）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("router", router_node)
    builder.add_node("rag", rag_node)
    builder.add_node("direct_answer", direct_answer_node)
    builder.add_node("refuse", refuse_node)
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
    builder.add_edge("rag", END)
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


async def _ainvoke_with_tracing(
    graph: Any, query: str, *, thread_id: str
) -> dict[str, Any]:
    """共享 ainvoke 外壳：thread_id 截断 + Langfuse config/span/属性传播。"""
    config: dict = {"configurable": {"thread_id": thread_id[:255]}}
    if tc := _trace_config(thread_id=thread_id):
        # 合并 callbacks / metadata / run_name；勿丢掉 thread_id
        config = {**tc, "configurable": config["configurable"]}
    span_cm = (
        trace_span(_RUN_NAME, run_type="chain", tags=[_TAG])
        if tracing_enabled()
        else nullcontext()
    )
    with span_cm:
        # 官方推荐的 trace 级属性传播：trace_name/session/tags 写到当前 span
        # 并随上下文传播给所有子 span。内层 LCEL 的 CallbackHandler 在其根
        # run 会 update_trace(name="lc-evidence-chain")，后置
        # update_current_trace 实测抢不回命名，故用 propagate_attributes。
        if tracing_enabled():
            try:
                from langfuse import propagate_attributes

                attr_cm = propagate_attributes(
                    trace_name=_RUN_NAME, session_id=thread_id, tags=[_TAG]
                )
            except Exception:  # SDK 可选；失败不挡主流程
                attr_cm = nullcontext()
        else:
            attr_cm = nullcontext()
        with attr_cm:
            return await graph.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config,
            )


async def ainvoke_basic_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
) -> dict[str, Any]:
    """Phase 1 单节点图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_basic_agent(checkpointer=checkpointer)
    return await _ainvoke_with_tracing(graph, query, thread_id=thread_id)


async def ainvoke_router_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
) -> dict[str, Any]:
    """Phase 2 三路路由图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_router_agent(checkpointer=checkpointer)
    return await _ainvoke_with_tracing(graph, query, thread_id=thread_id)
