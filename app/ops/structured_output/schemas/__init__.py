"""Deprecated：域 schema 已迁至 ``app.ops.lg_rag.schemas``。

短期兼容 re-export；新代码请改从 ``app.ops.lg_rag.schemas`` 导入。
本包顶层 ``structured_output.__all__`` 不含业务 schema。
"""

from app.ops.lg_rag.schemas import (
    ExtractResult,
    RouteDecision,
    SubtaskItem,
    SubtasksPlan,
)

__all__ = [
    "ExtractResult",
    "RouteDecision",
    "SubtaskItem",
    "SubtasksPlan",
]
