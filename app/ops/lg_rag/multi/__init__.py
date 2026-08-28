"""lg_rag Phase 4 · Multi-Agent（Supervisor 协作）子包。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md

拓扑：START → intent_node → strategy_builder → supervisor（LLM 拆解 ≤4 子任务）
→ dispatch 条件边 → rag_subtask / info_extract / tool_exec（顺序 fan-out，回 dispatch）
→ 耗尽 → aggregator（LLM 综合）→ critic_node（S4 规则 stub）→ 条件边 END / supervisor / Builder。
"""

from app.ops.lg_rag.multi.graph import (
    ainvoke_supervisor_agent,
    build_supervisor_agent,
)

__all__ = [
    "build_supervisor_agent",
    "ainvoke_supervisor_agent",
]
