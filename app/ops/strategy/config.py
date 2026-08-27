"""Strategy Builder S1 配置（规则/候选 id · 无 LLM）。

``CANDIDATE_CAPABILITY_IDS``：
- ``None``：采用 Registry ∩ Policy 全量可见 local_fn（非 high risk）；
- ``[]``：显式空 allowlist（supervisor 路径 fallback 单 rag）；
- 非空 list：与可见 catalog 求交，非法 id 剔除。
"""

from __future__ import annotations

# S1 首版：Host 配置候选 capability id；测试可 patch 本模块。
CANDIDATE_CAPABILITY_IDS: list[str] | None = None


def get_candidate_capability_ids() -> list[str] | None:
    """返回当前候选 id 列表副本；``None`` 表示「全量可见 catalog」。"""
    if CANDIDATE_CAPABILITY_IDS is None:
        return None
    return list(CANDIDATE_CAPABILITY_IDS)
