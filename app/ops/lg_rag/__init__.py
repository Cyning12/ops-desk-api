"""LangGraph 旁路：Evidence Chain 封装为单 Agent（默认不挂 chat/graph）。

Phase 1 basic（START→rag→END）与 Phase 2 router（三路分流）并存；
basic 保留作回归对照与回滚。
"""

from app.ops.lg_rag.checkpointer import apostgres_saver, postgres_saver
from app.ops.lg_rag.graph import (
    ainvoke_basic_agent,
    ainvoke_router_agent,
    build_basic_agent,
    build_router_agent,
)
from app.ops.lg_rag.state import LgRagState

__all__ = [
    "build_basic_agent",
    "ainvoke_basic_agent",
    "build_router_agent",
    "ainvoke_router_agent",
    "LgRagState",
    "apostgres_saver",
    "postgres_saver",
]
