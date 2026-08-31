"""lg_rag Phase 4 · Supervisor 多智能体 StateGraph 组装。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md §1。

拓扑：
START → intent_node（S2 细意图）→ strategy_builder（S1 allowlist）→ supervisor（LLM 拆解 ≤4 子任务）→ dispatch 条件边
  ├─ type=rag     → rag_subtask（内部调 router 图子图）→ 回 dispatch
  ├─ type=extract → info_extract（LLM 实体抽取）→ 回 dispatch
  ├─ type=tool    → tool_exec（Mock 工具注册表）→ 回 dispatch
  └─ 耗尽/空 subtasks → aggregator（LLM 综合）→ critic_node（S4 规则 stub）
       ├─ pass / end → END
       ├─ retry_planner → supervisor（同 catalog / 已有 allowlist）
       └─ rebind → strategy_builder（结构闭环，不扩权）

tracing 注入复用 app.ops.lg_rag.graph._ainvoke_with_tracing（不复制）；
默认 InMemorySaver；三图并存（basic / router / supervisor）互不破坏。
禁止每请求 compile；禁止 intent→② 回环。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.ops.lg_rag.graph import _ainvoke_with_tracing, _astream_with_tracing, _compile
from app.ops.lg_rag.multi.nodes import (
    aggregator_node,
    info_extract_node,
    rag_subtask_node,
    route_next_subtask,
    supervisor_node,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.strategy.builder import strategy_builder_node
from app.ops.strategy.critic import critic_node, route_after_critic
from app.ops.strategy.intent import intent_node

# dispatch 条件边映射：三专业 agent 或耗尽进 aggregator
_DISPATCH_MAP = {
    "rag_subtask": "rag_subtask",
    "info_extract": "info_extract",
    "tool_exec": "tool_exec",
    "aggregate": "aggregator",
}

# Critic 条件边：pass/end → END；retry 同 catalog；rebind 回 Builder
_CRITIC_MAP = {
    "pass": END,
    "retry_planner": "supervisor",
    "rebind": "strategy_builder",
    "end": END,
}

_AGENT_NODES = ("rag_subtask", "info_extract", "tool_exec")


def build_supervisor_agent(*, checkpointer: Any | None = None):
    """START → intent_node → strategy_builder → supervisor → dispatch → aggregator → critic_node。

    节点 id 用 ``intent_node`` / ``critic_node``：LangGraph 禁止与 state key 同名。
    """
    builder = StateGraph(LgRagState)
    builder.add_node("intent_node", intent_node)
    builder.add_node("strategy_builder", strategy_builder_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("rag_subtask", rag_subtask_node)
    builder.add_node("info_extract", info_extract_node)
    builder.add_node("tool_exec", tool_exec_node)
    builder.add_node("aggregator", aggregator_node)
    builder.add_node("critic_node", critic_node)
    builder.add_edge(START, "intent_node")
    builder.add_edge("intent_node", "strategy_builder")
    builder.add_edge("strategy_builder", "supervisor")
    builder.add_conditional_edges("supervisor", route_next_subtask, _DISPATCH_MAP)
    for name in _AGENT_NODES:
        builder.add_conditional_edges(name, route_next_subtask, _DISPATCH_MAP)
    builder.add_edge("aggregator", "critic_node")
    builder.add_conditional_edges("critic_node", route_after_critic, _CRITIC_MAP)
    return _compile(builder, checkpointer)


async def ainvoke_supervisor_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-supervisor-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
) -> dict[str, Any]:
    """Phase 4 Supervisor 图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_supervisor_agent(checkpointer=checkpointer)
    return await _ainvoke_with_tracing(
        graph, query, thread_id=thread_id, history_turns=history_turns
    )


async def astream_supervisor_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-supervisor-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Phase 4 Supervisor · astream(updates)。"""
    graph = build_supervisor_agent(checkpointer=checkpointer)
    async for update in _astream_with_tracing(
        graph, query, thread_id=thread_id, history_turns=history_turns
    ):
        yield update
