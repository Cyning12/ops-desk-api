"""LangGraph 主线：Evidence Chain 封装为单 Agent（旧 chat/graph 已于 P0' T2a 清除）。

Phase 1 basic（START→rag→END）、Phase 2 router（三路分流）与
Phase 4 supervisor（多智能体协作）三图并存；basic 保留作回归对照与回滚。
"""

from app.ops.lg_rag.checkpointer import apostgres_saver, postgres_saver
from app.ops.lg_rag.graph import (
    ainvoke_basic_agent,
    ainvoke_router_agent,
    build_basic_agent,
    build_router_agent,
)
from app.ops.lg_rag.multi import (
    ainvoke_supervisor_agent,
    build_supervisor_agent,
)
from app.ops.lg_rag.state import LgRagState

__all__ = [
    "build_basic_agent",
    "ainvoke_basic_agent",
    "build_router_agent",
    "ainvoke_router_agent",
    "build_supervisor_agent",
    "ainvoke_supervisor_agent",
    "LgRagState",
    "apostgres_saver",
    "postgres_saver",
]
