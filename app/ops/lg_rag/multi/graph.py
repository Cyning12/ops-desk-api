"""lg_rag Phase 4 · Supervisor 多智能体 StateGraph 组装。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md §1。

拓扑（**外层 ReAct + 内层 plan-and-execute**）：
START → intent_node（S2 细意图）→ strategy_builder（S1 allowlist）→ supervisor（LLM 拆解 ≤4 子任务）→ subtask_join
  ├─ 无依赖同批 Send：rag / extract / tool 可同时在飞，按 Host subtask_id 归并后回 join
  ├─ 有 depends_on 的等前驱终态再下发，不与前驱同批
  └─ 没有待发步骤 → **observe**（执行层收口，不再直连 aggregator）
       ├─ replan → supervisor（再来一轮 plan → execute，轮次上限 ``LG_RAG_REACT_MAX_ROUNDS``）
       └─ settle → aggregator（LLM 综合）→ critic_node（S4 规则 stub）
            ├─ pass / end → END
            ├─ retry_planner → supervisor（同 catalog / 已有 allowlist；全局耗尽禁回环）
            └─ rebind → strategy_builder（结构闭环，不扩权；全局耗尽禁回环）

**为什么多一层 observe**：原来"没有待发步骤"直接跳 aggregator，于是
「后缀为空 / 全被契约拦下 / 前驱失败后继停住」这三种情况都会一路走到
aggregator 生成一份**看起来完整的结论**，中间没有任何针对性校验。
observe 是执行层的收口：先判"这一轮有没有做完"，再决定要不要再来一轮。

总步默认 32（env ``LG_RAG_SUPERVISOR_MAX_STEPS``）；不计 rag_subtask 内 router 子图。
轮次默认 2（env ``LG_RAG_REACT_MAX_ROUNDS``）——**步数与轮数是两个维度，不能互相替代**。

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
    _join_subtasks,
    aggregator_node,
    info_extract_node,
    observe_node,
    rag_subtask_node,
    route_after_react,
    route_next_subtask,
    supervisor_node,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.strategy.builder import strategy_builder_node
from app.ops.strategy.critic import critic_node, route_after_critic
from app.ops.strategy.intent import intent_node

# dispatch 条件边映射：三专业 agent 或"没有待发步骤"进 observe（外层 ReAct 收口）
_DISPATCH_MAP = {
    "rag_subtask": "rag_subtask",
    "info_extract": "info_extract",
    "tool_exec": "tool_exec",
    # ★ 不再直连 aggregator：没有待发步骤 ≠ 这轮满足了问题，
    #   先让 observe 判断"再来一轮还是收工"
    "observe": "observe",
}

# observe 条件边：再来一轮 plan→execute，还是收工出结论
_REACT_MAP = {
    "replan": "supervisor",
    "settle": "aggregator",
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
    builder.add_node("subtask_join", _join_subtasks)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "intent_node")
    builder.add_edge("intent_node", "strategy_builder")
    builder.add_edge("strategy_builder", "supervisor")
    builder.add_edge("supervisor", "subtask_join")
    builder.add_conditional_edges("subtask_join", route_next_subtask, _DISPATCH_MAP)
    for name in _AGENT_NODES:
        builder.add_edge(name, "subtask_join")
    builder.add_conditional_edges("observe", route_after_react, _REACT_MAP)
    builder.add_edge("aggregator", "critic_node")
    builder.add_conditional_edges("critic_node", route_after_critic, _CRITIC_MAP)
    return _compile(builder, checkpointer)


async def ainvoke_supervisor_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-supervisor-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Phase 4 Supervisor 图；同 thread_id 可经 checkpointer 续写 messages。"""
    graph = build_supervisor_agent(checkpointer=checkpointer)
    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    return await _ainvoke_with_tracing(
        graph,
        query,
        thread_id=thread_id,
        history_turns=history_turns,
        run_id=run_id,
        **kwargs,
    )


async def astream_supervisor_agent(
    query: str,
    *,
    thread_id: str = "lg-rag-supervisor-smoke",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
    user_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Phase 4 Supervisor · astream(updates)。"""
    graph = build_supervisor_agent(checkpointer=checkpointer)
    kwargs: dict[str, Any] = {}
    if user_id:
        kwargs["user_id"] = user_id
    async for update in _astream_with_tracing(
        graph,
        query,
        thread_id=thread_id,
        history_turns=history_turns,
        run_id=run_id,
        **kwargs,
    ):
        yield update
