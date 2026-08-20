"""lg_rag 最小 StateGraph 组装（Phase 1）。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S3/S4。
拓扑：START → rag → END；默认 InMemorySaver；
ainvoke 注入 Langfuse config（对齐 app/ops/chat/service.py 与
lc_evidence_chain 的 _trace_config 约定，不改 Chat service）。
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.ops.lg_rag.nodes import rag_node
from app.ops.lg_rag.state import LgRagState
from app.ops.tracing import (
    ensure_langfuse_environment,
    trace_span,
    tracing_enabled,
)

_RUN_NAME = "lg-rag"
_TAG = "lg-rag"


def build_basic_agent(*, checkpointer: Any | None = None):
    """START → rag → END；默认 InMemorySaver。"""
    builder = StateGraph(LgRagState)
    builder.add_node("rag", rag_node)
    builder.add_edge(START, "rag")
    builder.add_edge("rag", END)
    saver = checkpointer if checkpointer is not None else InMemorySaver()
    return builder.compile(checkpointer=saver)


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


async def ainvoke_basic_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-smoke",
    checkpointer: Any | None = None,
) -> dict[str, Any]:
    """单 query 走通图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_basic_agent(checkpointer=checkpointer)
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
