"""Strategy Builder 薄包（S1 · 非 G-L1 一级模块）。

首版规则/配置写 allowlist；消费方见 ``app.ops.lg_rag.multi``。
"""

from app.ops.strategy.builder import (
    BUILDER_CAP_FILTER,
    build_allowlist_from_candidates,
    get_policy_visible_ids,
    strategy_builder_node,
)
from app.ops.strategy.config import get_candidate_capability_ids

__all__ = [
    "BUILDER_CAP_FILTER",
    "build_allowlist_from_candidates",
    "get_candidate_capability_ids",
    "get_policy_visible_ids",
    "strategy_builder_node",
]
